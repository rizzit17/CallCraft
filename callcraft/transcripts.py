"""Transcript parser, validator, and deterministic offline analyzer.

Implements rule-based validation and defect audits.
Operates completely offline with zero external network or provider calls.
"""

from __future__ import annotations

import csv
import difflib
import io
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from callcraft.models import (
    Severity,
    TranscriptAnalysis,
    TranscriptFinding,
    TRANSCRIPT_FINDING_CATEGORIES,
)

DEFAULT_PROHIBITED_PHRASES: list[str] = [
    "guaranteed approval",
    "guarantee you will be approved",
    "you will definitely be approved",
    "100% approved",
    "no credit check",
]

AGENT_SPEAKER_ALIASES = {"agent", "assistant", "bot", "ai"}
CUSTOMER_SPEAKER_ALIASES = {"customer", "user", "caller", "client"}


class TranscriptValidationError(Exception):
    def __init__(self, errors: list[str], total_error_count: int) -> None:
        super().__init__("; ".join(errors[:5]))
        self.errors = errors
        self.total_error_count = total_error_count


def parse_and_validate_transcripts(
    raw_content: bytes | str,
    filename: str,
    max_mb: int = 5,
    max_rows: int = 20000,
) -> tuple[list[dict[str, Any]], str, list[str]]:
    """Parse and validate CSV, JSON, or JSONL transcript content.

    Returns:
        (rows, detected_format, validation_errors)
    """
    # Size check
    if isinstance(raw_content, bytes):
        byte_len = len(raw_content)
        if byte_len > max_mb * 1024 * 1024:
            return [], "unknown", [f"File {filename} exceeds maximum allowed size of {max_mb} MB ({byte_len / 1024 / 1024:.2f} MB)."]
        try:
            text = raw_content.decode("utf-8")
        except UnicodeDecodeError as ude:
            return [], "unknown", [f"File {filename} could not be decoded as UTF-8: {ude}"]
    else:
        text = raw_content

    # Determine format from extension or content
    lower_fn = filename.lower()
    if lower_fn.endswith(".jsonl"):
        detected_format = "jsonl"
    elif lower_fn.endswith(".json"):
        detected_format = "json"
    elif lower_fn.endswith(".csv"):
        detected_format = "csv"
    else:
        # Sniff
        stripped = text.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            detected_format = "json"
        else:
            detected_format = "csv"

    parsed_records: list[dict[str, Any]] = []
    errors: list[str] = []

    if detected_format == "csv":
        try:
            non_comment_lines = [l for l in text.splitlines() if not l.strip().startswith("#")]
            clean_csv_text = "\n".join(non_comment_lines)
            reader = csv.DictReader(io.StringIO(clean_csv_text))
            if not reader.fieldnames:
                return [], "csv", [f"CSV file {filename} is empty or missing a header row."]
            for idx, row in enumerate(reader, start=2):  # row 1 is header
                parsed_records.append({"_row_num": idx, **row})
        except Exception as exc:
            return [], "csv", [f"Error parsing CSV in {filename}: {exc}"]

    elif detected_format == "jsonl":
        for idx, line in enumerate(text.splitlines(), start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                rec = json.loads(line_str)
                if not isinstance(rec, dict):
                    errors.append(f"[{filename}:line {idx}] JSONL record must be a JSON object")
                    continue
                parsed_records.append({"_row_num": idx, **rec})
            except Exception as exc:
                errors.append(f"[{filename}:line {idx}] Invalid JSON: {exc}")

    elif detected_format == "json":
        try:
            data = json.loads(text)
        except Exception as exc:
            return [], "json", [f"Error decoding JSON in {filename}: {exc}"]

        if isinstance(data, list):
            for idx, item in enumerate(data, start=1):
                if not isinstance(item, dict):
                    errors.append(f"[{filename}:item {idx}] Array item must be a JSON object")
                else:
                    parsed_records.append({"_row_num": idx, **item})
        elif isinstance(data, dict):
            # Support {"conversations": [{"conversation_id": "...", "turns": [{"speaker": "...", "message": "..."}]}]}
            convs = data.get("conversations")
            if isinstance(convs, list):
                row_counter = 1
                for c in convs:
                    if not isinstance(c, dict):
                        continue
                    cid = c.get("conversation_id", "")
                    turns = c.get("turns", [])
                    if isinstance(turns, list):
                        for tidx, turn in enumerate(turns):
                            if isinstance(turn, dict):
                                parsed_records.append({
                                    "_row_num": row_counter,
                                    "conversation_id": cid,
                                    "turn_index": turn.get("turn_index", tidx),
                                    "speaker": turn.get("speaker", ""),
                                    "message": turn.get("message", ""),
                                    "timestamp": turn.get("timestamp", ""),
                                })
                                row_counter += 1
            else:
                errors.append(f"[{filename}] JSON root object must contain a 'conversations' list or be an array of records")
        else:
            errors.append(f"[{filename}] Unsupported JSON root type: {type(data).__name__}")

    if errors:
        return [], detected_format, errors

    # Check maximum rows
    if len(parsed_records) > max_rows:
        return [], detected_format, [f"File {filename} contains {len(parsed_records)} rows, exceeding maximum allowed of {max_rows}."]

    # Validate individual flat records
    validated_rows: list[dict[str, Any]] = []
    val_errors: list[str] = []

    for r in parsed_records:
        row_n = r.get("_row_num", "?")
        cid = r.get("conversation_id")
        if not cid or not str(cid).strip():
            val_errors.append(f"[{filename}:row {row_n}] Field 'conversation_id' is required and cannot be empty")

        raw_speaker = r.get("speaker")
        if raw_speaker is None or not str(raw_speaker).strip():
            val_errors.append(f"[{filename}:row {row_n}] Field 'speaker' is required")
            norm_speaker = "unknown"
        else:
            s_clean = str(raw_speaker).strip().lower()
            if s_clean in AGENT_SPEAKER_ALIASES:
                norm_speaker = "agent"
            elif s_clean in CUSTOMER_SPEAKER_ALIASES:
                norm_speaker = "customer"
            else:
                val_errors.append(f"[{filename}:row {row_n}] Invalid speaker '{raw_speaker}'. Must map to 'agent' or 'customer'")
                norm_speaker = "unknown"

        if "message" not in r:
            val_errors.append(f"[{filename}:row {row_n}] Missing required field 'message'")
            msg = ""
        else:
            msg = str(r["message"]) if r["message"] is not None else ""

        # turn_index
        turn_idx: Optional[int] = None
        if "turn_index" in r and r["turn_index"] not in (None, ""):
            try:
                turn_idx = int(r["turn_index"])
            except ValueError:
                val_errors.append(f"[{filename}:row {row_n}] Field 'turn_index' must be an integer (got {r['turn_index']!r})")

        validated_rows.append({
            "conversation_id": str(cid).strip() if cid else "",
            "speaker": norm_speaker,
            "message": msg,
            "turn_index": turn_idx,
            "timestamp": str(r.get("timestamp", "")) if r.get("timestamp") else None,
            "_row_num": row_n,
        })

    if val_errors:
        return [], detected_format, val_errors

    return validated_rows, detected_format, []


def analyze_transcripts(
    validated_rows: list[dict[str, Any]],
    source_filename: str,
    file_format: str,
    prohibited_phrases: Optional[list[str]] = None,
    store_excerpts: bool = False,
) -> TranscriptAnalysis:
    """Run deterministic structural and defect checks on grouped transcript conversations."""
    phrases = [p.lower() for p in (prohibited_phrases or DEFAULT_PROHIBITED_PHRASES)]

    # Group by conversation_id
    conversations: dict[str, list[dict[str, Any]]] = {}
    for r in validated_rows:
        cid = r["conversation_id"]
        if cid not in conversations:
            conversations[cid] = []
        conversations[cid].append(r)

    now_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    analysis_id = f"T-{now_str}-{secrets.token_hex(2)}"

    all_findings: list[TranscriptFinding] = []
    flagged_conversations: set[str] = set()
    total_messages = len(validated_rows)

    category_counts: dict[str, int] = {c: 0 for c in TRANSCRIPT_FINDING_CATEGORIES}

    for cid, turns in conversations.items():
        # Order turns deterministically: by turn_index if present, else original order
        has_indices = all(t.get("turn_index") is not None for t in turns)
        if has_indices:
            sorted_turns = sorted(turns, key=lambda t: t["turn_index"])
        else:
            sorted_turns = turns

        # Check single_speaker
        speakers = {t["speaker"] for t in sorted_turns}
        if len(speakers) == 1:
            all_findings.append(
                TranscriptFinding(
                    analysis_id=analysis_id,
                    conversation_id=cid,
                    turn_index=None,
                    category="single_speaker",
                    severity="medium",
                    detail=f"Conversation has only one active speaker role: '{list(speakers)[0]}'",
                    excerpt=None,
                )
            )
            flagged_conversations.add(cid)
            category_counts["single_speaker"] += 1

        agent_messages_history: list[str] = []

        for idx, turn in enumerate(sorted_turns):
            turn_idx = turn.get("turn_index", idx)
            speaker = turn["speaker"]
            msg = turn["message"]
            msg_clean = msg.strip()

            # Empty response check
            if speaker == "agent" and not msg_clean:
                all_findings.append(
                    TranscriptFinding(
                        analysis_id=analysis_id,
                        conversation_id=cid,
                        turn_index=turn_idx,
                        category="empty_response",
                        severity="high",
                        detail=f"Turn {turn_idx}: Agent message is empty or whitespace only",
                        excerpt="",
                    )
                )
                flagged_conversations.add(cid)
                category_counts["empty_response"] += 1

            # Prohibited claim check
            if msg_clean:
                msg_lower = msg_clean.lower()
                for phrase in phrases:
                    if phrase in msg_lower:
                        excerpt = msg_clean[:200] if store_excerpts else None
                        all_findings.append(
                            TranscriptFinding(
                                analysis_id=analysis_id,
                                conversation_id=cid,
                                turn_index=turn_idx,
                                category="prohibited_claim",
                                severity="high",
                                detail=f"Turn {turn_idx} ({speaker}): Contains prohibited phrase '{phrase}'",
                                excerpt=excerpt,
                            )
                        )
                        flagged_conversations.add(cid)
                        category_counts["prohibited_claim"] += 1
                        break  # once per turn

            if speaker == "agent" and msg_clean:
                # Length violation check (>120 words)
                word_count = len(msg_clean.split())
                if word_count > 120:
                    excerpt = msg_clean[:200] if store_excerpts else None
                    all_findings.append(
                        TranscriptFinding(
                            analysis_id=analysis_id,
                            conversation_id=cid,
                            turn_index=turn_idx,
                            category="length_violation",
                            severity="low",
                            detail=f"Turn {turn_idx}: Agent message length ({word_count} words) exceeds 120 words",
                            excerpt=excerpt,
                        )
                    )
                    flagged_conversations.add(cid)
                    category_counts["length_violation"] += 1

                # Repetition check (similarity >= 0.9 with prior agent turn in same conversation)
                norm_curr = " ".join(msg_clean.lower().split())
                for prior in agent_messages_history:
                    norm_prior = " ".join(prior.lower().split())
                    sim = difflib.SequenceMatcher(None, norm_curr, norm_prior).ratio()
                    if sim >= 0.9:
                        excerpt = msg_clean[:200] if store_excerpts else None
                        all_findings.append(
                            TranscriptFinding(
                                analysis_id=analysis_id,
                                conversation_id=cid,
                                turn_index=turn_idx,
                                category="repetition",
                                severity="medium",
                                detail=f"Turn {turn_idx}: Agent message repeats earlier agent turn (similarity {sim:.2f})",
                                excerpt=excerpt,
                            )
                        )
                        flagged_conversations.add(cid)
                        category_counts["repetition"] += 1
                        break

                agent_messages_history.append(msg_clean)

        # Unanswered turn check (last turn is customer turn)
        if sorted_turns and sorted_turns[-1]["speaker"] == "customer":
            last_idx = sorted_turns[-1].get("turn_index", len(sorted_turns) - 1)
            all_findings.append(
                TranscriptFinding(
                    analysis_id=analysis_id,
                    conversation_id=cid,
                    turn_index=last_idx,
                    category="unanswered_turn",
                    severity="low",
                    detail=f"Conversation ends on an unanswered customer turn at index {last_idx}",
                    excerpt=None,
                )
            )
            flagged_conversations.add(cid)
            category_counts["unanswered_turn"] += 1

    summary = {
        "n_conversations": len(conversations),
        "n_messages": total_messages,
        "n_flagged_conversations": len(flagged_conversations),
        "n_findings": len(all_findings),
        "category_counts": category_counts,
    }

    return TranscriptAnalysis(
        analysis_id=analysis_id,
        source_filename=source_filename,
        file_format=file_format,  # type: ignore
        uploaded_at=datetime.now(timezone.utc).isoformat(),
        n_conversations=len(conversations),
        n_messages=total_messages,
        n_flagged_conversations=len(flagged_conversations),
        n_findings=len(all_findings),
        excerpts_stored=store_excerpts,
        summary=summary,
        findings=all_findings,
    )
