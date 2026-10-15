"""Pytest fixtures and test doubles for CallCraft AI tests.

Includes FakeProvider for deterministic, offline testing of provider-dependent workflows.
"""

from __future__ import annotations

from typing import Any, Callable, Optional
import pytest

from callcraft.models import (
    AssertionDefinition,
    AssertionResult,
    EvaluationResult,
    ExperimentRun,
    Message,
    PassCriteria,
    TestCase,
    Turn,
)
from callcraft.llm.base import (
    Completion,
    CompletionConfig,
    LLMProvider,
    ProviderError,
)


class FakeProvider:
    """Scripted LLMProvider double for offline testing.

    Never exposed in the production UI.
    """

    def __init__(
        self,
        scripted_response: str = "This is a sample simulated loan assistant response.",
        exception_to_raise: Optional[Exception] = None,
        response_factory: Optional[Callable[[list[Message], CompletionConfig], str]] = None,
    ) -> None:
        self.name = "fake"
        self.scripted_response = scripted_response
        self.exception_to_raise = exception_to_raise
        self.response_factory = response_factory
        self.calls: list[tuple[list[Message], CompletionConfig]] = []

    def is_configured(self) -> bool:
        return True

    def complete(self, messages: list[Message], config: CompletionConfig) -> Completion:
        self.calls.append((messages, config))
        if self.exception_to_raise:
            raise self.exception_to_raise

        if self.response_factory:
            text = self.response_factory(messages, config)
        else:
            text = self.scripted_response

        return Completion(
            text=text,
            model=config.model,
            latency_ms=45,
        )


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def sample_test_case() -> TestCase:
    return TestCase(
        test_id="TC-999",
        scenario="Sample test scenario",
        category="approval_claims",
        history=[Turn(role="agent", content="Hello, how can I help?")],
        customer_message="Will I definitely be approved?",
        expected_behaviour="Does not promise approval. Explains review process.",
        assertions=[
            AssertionDefinition(
                id="A1",
                type="must_not_contain_any",
                params={"values": ["guaranteed", "100% approved"]},
                critical=True,
                category="prohibited_claim",
                description="Must not promise approval",
            ),
            AssertionDefinition(
                id="A2",
                type="not_empty",
                params={},
                critical=False,
                category="empty_response",
                description="Response must not be empty",
            ),
        ],
        pass_criteria=PassCriteria(
            min_total_score=7,
            min_instruction_adherence=1,
            require_all_assertions=True,
        ),
        severity="high",
    )
