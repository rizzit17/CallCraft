"""Unit tests for prompt A/B experiments runner."""

import json
import tempfile
from pathlib import Path
import pytest

from callcraft.config import Settings
from callcraft.experiments import run_experiment
from callcraft.models import (
    AssertionDefinition,
    PassCriteria,
    PromptVersion,
    TestCase,
)
from callcraft.storage import Storage
from tests.conftest import FakeProvider


@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "exp_test.db"
        yield Storage(db_path)


def test_run_experiment_ab_success(temp_storage):
    """PC-05: A/B experiment runs both prompts on identical test cases and stores results."""
    # Seed prompts
    p_a = PromptVersion(
        prompt_id="P-A",
        label="Prompt A",
        content="System Prompt A",
        content_sha256="hash-a",
    )
    p_b = PromptVersion(
        prompt_id="P-B",
        label="Prompt B",
        content="System Prompt B",
        content_sha256="hash-b",
    )
    temp_storage.save_prompt_version(p_a)
    temp_storage.save_prompt_version(p_b)

    cases = [
        TestCase(
            test_id="TC-001",
            scenario="Scenario 1",
            customer_message="Help with loan",
            expected_behaviour="Help customer",
            assertions=[AssertionDefinition(id="A1", type="not_empty", critical=True)],
        ),
        TestCase(
            test_id="TC-002",
            scenario="Scenario 2",
            customer_message="What rate?",
            expected_behaviour="Explain rate review",
            assertions=[
                AssertionDefinition(
                    id="A1",
                    type="must_not_contain_any",
                    params={"values": ["100% approved"]},
                    critical=True,
                )
            ],
        ),
    ]

    fake = FakeProvider(scripted_response="Sample response from assistant.")
    settings = Settings(groq_model="fake-model")

    exp_id, run_a, run_b, comp = run_experiment(
        prompt_a_id="P-A",
        prompt_b_id="P-B",
        test_cases=cases,
        storage=temp_storage,
        provider=fake,
        settings=settings,
        enable_judge=False,
    )

    assert exp_id.startswith("E-")
    assert run_a.status == "complete"
    assert run_b.status == "complete"
    assert run_a.test_set_hash == run_b.test_set_hash
    assert run_a.config_hash == run_b.config_hash
    assert comp.is_comparable is True

    # Check results in storage
    res_a = temp_storage.get_evaluation_results(run_id=run_a.run_id)
    res_b = temp_storage.get_evaluation_results(run_id=run_b.run_id)
    assert len(res_a) == 2
    assert len(res_b) == 2
    assert all(r.status == "passed" for r in res_a)
    assert all(r.status == "passed" for r in res_b)


def test_run_experiment_missing_prompt(temp_storage):
    cases = [TestCase(test_id="TC-001", scenario="S", customer_message="M", expected_behaviour="B", assertions=[])]
    with pytest.raises(ValueError, match="Prompt A not found"):
        run_experiment("P-missing", "P-B", cases, temp_storage, FakeProvider(), Settings())
