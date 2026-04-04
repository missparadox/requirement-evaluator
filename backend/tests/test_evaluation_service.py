import json
from pathlib import Path

from app.clients.model_client import StaticModelClient
from app.services.evaluation_service import EvaluationService
from app.storage.evaluation_store import EvaluationStore


def test_static_model_client_returns_markdown() -> None:
    client = StaticModelClient()
    report = client.generate_report(skill_text="skill", template_text="template", packet_text="packet")
    assert report.startswith("#")


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
