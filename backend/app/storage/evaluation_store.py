from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvaluationStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def evaluation_dir(self, evaluation_id: str) -> Path:
        return self.root / evaluation_id

    def metadata_path(self, evaluation_id: str) -> Path:
        return self.evaluation_dir(evaluation_id) / "metadata.json"

    def create_evaluation(self, *, evaluation_id: str, filename: str, file_bytes: bytes) -> dict[str, Any]:
        directory = self.evaluation_dir(evaluation_id)
        directory.mkdir(parents=True, exist_ok=False)
        safe_filename = Path(filename).name
        original_file_path = directory / safe_filename
        original_file_path.write_bytes(file_bytes)
        metadata_path = self.metadata_path(evaluation_id)
        metadata = {
            "evaluation_id": evaluation_id,
            "status": "pending",
            "filename": safe_filename,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "directory": directory,
            "original_file_path": original_file_path,
            "metadata_path": metadata_path,
        }

    def read_metadata(self, evaluation_id: str) -> dict[str, Any]:
        return json.loads(self.metadata_path(evaluation_id).read_text(encoding="utf-8"))

    def update_metadata(self, evaluation_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        metadata = self.read_metadata(evaluation_id)
        metadata.update(patch)
        self.metadata_path(evaluation_id).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return metadata
