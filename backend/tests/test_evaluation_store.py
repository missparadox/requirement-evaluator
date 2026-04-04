import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from app.adapters.packet_builder import build_review_packet
from app.storage.evaluation_store import EvaluationStore


def test_create_evaluation_directory_and_metadata(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path)
    file_bytes = b"hello"
    record = store.create_evaluation(
        evaluation_id="eval_001",
        filename="requirements.csv",
        file_bytes=file_bytes,
    )
    assert record["original_file_path"].read_bytes() == file_bytes
    metadata = json.loads(record["metadata_path"].read_text(encoding="utf-8"))
    assert metadata["evaluation_id"] == "eval_001"
    assert metadata["status"] == "pending"
    assert metadata["filename"] == "requirements.csv"


def test_create_evaluation_normalizes_filename_to_block_traversal(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path)
    record = store.create_evaluation(
        evaluation_id="eval_002",
        filename="../outside.txt",
        file_bytes=b"safe",
    )
    evaluation_dir = tmp_path / "eval_002"
    assert record["original_file_path"] == evaluation_dir / "outside.txt"
    assert record["original_file_path"].parent == evaluation_dir
    assert record["original_file_path"].read_bytes() == b"safe"
    metadata = json.loads(record["metadata_path"].read_text(encoding="utf-8"))
    assert metadata["filename"] == "outside.txt"


def test_update_metadata_persists_status_and_report_path(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path)
    store.create_evaluation(evaluation_id="eval_001", filename="requirements.csv", file_bytes=b"abc")
    store.update_metadata("eval_001", {"status": "running", "report_path": "report.md"})
    metadata = store.read_metadata("eval_001")
    assert metadata["status"] == "running"
    assert metadata["report_path"] == "report.md"


def test_build_review_packet_creates_markdown_file(tmp_path: Path) -> None:
    input_path = tmp_path / "requirements.csv"
    input_path.write_text("OR需求编号,OR需求名称*,OR需求描述*\nD1,Name,Desc\n", encoding="utf-8")
    output_path = tmp_path / "packet.md"
    build_review_packet(input_path=input_path, output_path=output_path)
    assert output_path.exists()


def test_build_review_packet_raises_runtime_error_on_subprocess_failure(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "requirements.csv"
    output_path = tmp_path / "packet.md"
    failing_result = SimpleNamespace(returncode=1, stderr="boom", stdout="")
    run_mock = Mock(return_value=failing_result)
    monkeypatch.setattr("app.adapters.packet_builder.subprocess.run", run_mock)

    try:
        build_review_packet(input_path=input_path, output_path=output_path)
    except RuntimeError as exc:
        message = str(exc)
        assert str(input_path) in message
        assert str(output_path) in message
        assert "boom" in message
    else:
        raise AssertionError("build_review_packet() did not raise RuntimeError")
