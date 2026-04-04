from datetime import datetime, timezone

from app.adapters.packet_builder import build_review_packet
from app.core.paths import REPORT_TEMPLATE_FILE, SKILL_FILE


class EvaluationRunner:
    def __init__(self, *, store, model_client) -> None:
        self.store = store
        self.model_client = model_client

    def run(self, evaluation_id: str) -> None:
        metadata = self.store.update_metadata(
            evaluation_id,
            {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()},
        )
        try:
            directory = self.store.evaluation_dir(evaluation_id)
            input_path = directory / metadata["filename"]
            packet_path = directory / "review-packet.md"
            build_review_packet(input_path=input_path, output_path=packet_path)
            report = self.model_client.generate_report(
                skill_text=SKILL_FILE.read_text(encoding="utf-8"),
                template_text=REPORT_TEMPLATE_FILE.read_text(encoding="utf-8"),
                packet_text=packet_path.read_text(encoding="utf-8"),
            )
            report_path = directory / "report.md"
            report_path.write_text(report, encoding="utf-8")
            self.store.update_metadata(
                evaluation_id,
                {
                    "status": "succeeded",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "report_path": str(report_path),
                },
            )
        except Exception as exc:
            self.store.update_metadata(
                evaluation_id,
                {
                    "status": "failed",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": str(exc),
                },
            )
            raise
