from pathlib import Path

from app.storage.evaluation_store import EvaluationStore


def test_create_evaluation_directory_and_metadata(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path)
    record = store.create_evaluation(
        evaluation_id="eval_001",
        filename="requirements.csv",
        file_bytes=b"hello",
    )
    assert record["metadata_path"].exists()
    assert record["original_file_path"].exists()
