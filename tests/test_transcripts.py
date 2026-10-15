"""Unit tests for transcript parser, validation error reporting, and defect detection."""

from pathlib import Path
import pytest

from callcraft.transcripts import (
    analyze_transcripts,
    parse_and_validate_transcripts,
)


def test_parse_sample_transcripts_csv():
    """Verify that SAMPLE_transcripts.csv parses and detects expected defects."""
    path = Path("data/samples/SAMPLE_transcripts.csv")
    assert path.exists()

    content = path.read_bytes()
    rows, fmt, errs = parse_and_validate_transcripts(content, path.name)
    assert len(errs) == 0, f"Validation errors: {errs}"
    assert fmt == "csv"
    assert len(rows) > 0

    analysis = analyze_transcripts(rows, path.name, fmt)
    assert analysis.n_conversations == 5
    assert analysis.n_flagged_conversations > 0

    cats = [f.category for f in analysis.findings]
    assert "prohibited_claim" in cats  # C-102 has "100% approved guaranteed approval"
    assert "repetition" in cats        # C-103 repeated turn
    assert "empty_response" in cats    # C-104 empty agent turn
    assert "unanswered_turn" in cats   # C-105 customer alone


def test_parse_sample_transcripts_jsonl():
    """Verify that SAMPLE_transcripts.jsonl parses and analyzes properly."""
    path = Path("data/samples/SAMPLE_transcripts.jsonl")
    assert path.exists()

    content = path.read_bytes()
    rows, fmt, errs = parse_and_validate_transcripts(content, path.name)
    assert len(errs) == 0
    assert fmt == "jsonl"

    analysis = analyze_transcripts(rows, path.name, fmt)
    assert analysis.n_conversations == 3
    cats = [f.category for f in analysis.findings]
    assert "prohibited_claim" in cats  # C-202 has "guaranteed approval"


def test_reject_malformed_csv_missing_columns():
    """PC-10: Transcript upload validates and rejects malformed files with clear messages."""
    bad_csv = "conv_id,text\nC-1,Hello"  # missing speaker, message
    rows, fmt, errs = parse_and_validate_transcripts(bad_csv, "bad.csv")
    assert len(errs) > 0
    assert any("conversation_id" in e for e in errs)
    assert any("speaker" in e for e in errs)


def test_reject_invalid_speaker():
    bad_json = '[{"conversation_id": "C-1", "speaker": "alien", "message": "hello"}]'
    rows, fmt, errs = parse_and_validate_transcripts(bad_json, "bad.json")
    assert len(errs) > 0
    assert any("alien" in e for e in errs)


def test_reject_empty_conversation_id():
    bad_jsonl = '{"conversation_id": "", "speaker": "agent", "message": "hello"}'
    rows, fmt, errs = parse_and_validate_transcripts(bad_jsonl, "bad.jsonl")
    assert len(errs) > 0
    assert any("conversation_id" in e for e in errs)
