import json
from pathlib import Path
from unittest.mock import Mock

from app.clients.model_client import OpenAIModelClient, StaticModelClient, build_model_client
from app.runners.evaluation_runner import EvaluationRunner
from app.services.evaluation_service import EvaluationService
from app.storage.evaluation_store import EvaluationStore


def test_static_model_client_returns_markdown() -> None:
    client = StaticModelClient()
    report = client.generate_report(skill_text="skill", template_text="template", packet_text="packet")
    assert report.startswith("#")


def test_build_model_client_returns_static_client_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = build_model_client("gpt-5.4")
    assert isinstance(client, StaticModelClient)


def test_build_model_client_returns_openai_client_with_api_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = build_model_client("gpt-5.4")
    assert isinstance(client, OpenAIModelClient)
    assert client.model_name == "gpt-5.4"


def test_create_returns_new_evaluation_id_when_no_match(tmp_path: Path) -> None:
    service = EvaluationService(store=EvaluationStore(tmp_path))
    result = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")
    assert result.status == "pending"
    assert result.dedupe_hit is False


def test_create_reuses_existing_evaluation_when_dedupe_key_matches(tmp_path: Path) -> None:
    service = EvaluationService(store=EvaluationStore(tmp_path))
    first = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")
    second = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")
    assert second.evaluation_id == first.evaluation_id
    assert second.dedupe_hit is True


def test_create_makes_new_evaluation_when_matching_task_failed(tmp_path: Path) -> None:
    service = EvaluationService(store=EvaluationStore(tmp_path))
    first = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")
    metadata_path = tmp_path / first.evaluation_id / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["status"] = "failed"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    second = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")

    assert second.evaluation_id != first.evaluation_id
    assert second.dedupe_hit is False


def test_create_makes_new_evaluation_when_model_provider_changes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    service = EvaluationService(store=EvaluationStore(tmp_path))
    first = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    second = EvaluationService(store=EvaluationStore(tmp_path)).create_or_reuse(
        filename="requirements.csv",
        file_bytes=b"abc",
    )

    assert second.evaluation_id != first.evaluation_id
    assert second.dedupe_hit is False


def test_runner_writes_report_and_marks_success(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path)
    store.create_evaluation(
        evaluation_id="eval_001",
        filename="requirements.csv",
        file_bytes="OR需求编号,OR需求名称*,OR需求描述*\nD1,N,D\n".encode("utf-8"),
    )
    runner = EvaluationRunner(store=store, model_client=StaticModelClient())
    runner.run("eval_001")
    metadata = store.read_metadata("eval_001")
    assert metadata["status"] == "succeeded"


def test_runner_marks_evaluation_failed_when_packet_building_raises(tmp_path: Path, monkeypatch) -> None:
    store = EvaluationStore(tmp_path)
    store.create_evaluation(
        evaluation_id="eval_001",
        filename="requirements.csv",
        file_bytes="OR需求编号,OR需求名称*,OR需求描述*\nD1,N,D\n".encode("utf-8"),
    )
    monkeypatch.setattr(
        "app.runners.evaluation_runner.build_review_packet",
        Mock(side_effect=RuntimeError("boom")),
    )
    runner = EvaluationRunner(store=store, model_client=StaticModelClient())

    try:
        runner.run("eval_001")
    except RuntimeError:
        pass
    else:
        raise AssertionError("runner.run() did not re-raise packet builder failure")

    metadata = store.read_metadata("eval_001")
    assert metadata["status"] == "failed"
    assert metadata["error_message"] == "boom"


def test_openai_model_client_uses_responses_api_instructions_and_input() -> None:
    responses = Mock()
    responses.create.return_value = Mock(output_text="# Real Report")
    sdk_client = Mock(responses=responses)
    client = OpenAIModelClient(model_name="gpt-5.4", client=sdk_client)

    report = client.generate_report(
        skill_text="skill text",
        template_text="template text",
        packet_text="packet text",
    )

    assert report == "# Real Report"
    responses.create.assert_called_once_with(
        model="gpt-5.4",
        instructions=(
            "You are a requirements evaluation assistant. "
            "Follow the rubric and produce the final answer in Chinese Markdown using the template."
        ),
        input=(
            "[SKILL]\nskill text\n\n"
            "[TEMPLATE]\ntemplate text\n\n"
            "[PACKET]\npacket text\n"
        ),
    )
