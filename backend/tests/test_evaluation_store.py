import json
from pathlib import Path

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
