import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "aggregate_reviews.py"


def load_module():
    spec = importlib.util.spec_from_file_location("aggregate_reviews_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AggregateReviewTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_aggregate_reviews_builds_summary_and_distribution(self):
        manifest = {
            "input_path": "requirements.xlsm",
            "source_info": {"input_format": "xlsm", "sheet_name": "Sheet1"},
            "or_count": 3,
            "dr_count": 4,
            "shard_count": 2,
            "shards": [
                {"shard_id": "shard-001", "or_ids": ["OR-1", "OR-2"]},
                {"shard_id": "shard-002", "or_ids": ["OR-3"]},
            ],
        }
        partials = [
            {
                "shard_id": "shard-001",
                "cross_shard_notes": {"weak_dimensions": ["OR-用户价值", "DR-可测试性"]},
                "or_results": [
                    {"or_id": "OR-1", "or_name": "需求1", "or_total_score": 82, "grade": "良好"},
                    {"or_id": "OR-2", "or_name": "需求2", "or_total_score": 46, "grade": "较弱"},
                ],
            },
            {
                "shard_id": "shard-002",
                "cross_shard_notes": {"weak_dimensions": ["DR-可测试性"]},
                "or_results": [
                    {"or_id": "OR-3", "or_name": "需求3", "or_total_score": 71, "grade": "良好"},
                ],
            },
        ]

        aggregated = self.module.aggregate_reviews(manifest, partials)

        self.assertTrue(aggregated["coverage_ok"])
        self.assertEqual(aggregated["overall_average_score"], 66.33)
        self.assertEqual(aggregated["grade_distribution"]["良好"], 2)
        self.assertEqual(aggregated["grade_distribution"]["较弱"], 1)
        self.assertEqual(aggregated["recurring_weak_dimensions"][0], "DR-可测试性")
        self.assertEqual(aggregated["or_results"][0]["or_id"], "OR-1")
        self.assertEqual(aggregated["top_risks"][0]["or_id"], "OR-2")

    def test_aggregate_reviews_marks_missing_or_coverage(self):
        manifest = {
            "input_path": "requirements.xlsm",
            "source_info": {"input_format": "xlsm", "sheet_name": "Sheet1"},
            "or_count": 2,
            "dr_count": 2,
            "shard_count": 1,
            "shards": [{"shard_id": "shard-001", "or_ids": ["OR-1", "OR-2"]}],
        }
        partials = [
            {
                "shard_id": "shard-001",
                "cross_shard_notes": {},
                "or_results": [
                    {"or_id": "OR-1", "or_name": "需求1", "or_total_score": 60},
                ],
            }
        ]

        aggregated = self.module.aggregate_reviews(manifest, partials)

        self.assertFalse(aggregated["coverage_ok"])
        self.assertEqual(aggregated["missing_or_ids"], ["OR-2"])

    def test_cli_aggregates_partial_review_files(self):
        manifest = {
            "input_path": "requirements.xlsm",
            "source_info": {"input_format": "xlsm", "sheet_name": "Sheet1"},
            "or_count": 2,
            "dr_count": 2,
            "shard_count": 1,
            "shards": [{"shard_id": "shard-001", "or_ids": ["OR-1", "OR-2"]}],
        }
        partial = {
            "shard_id": "shard-001",
            "cross_shard_notes": {"weak_dimensions": ["OR-用户价值"]},
            "or_results": [
                {"or_id": "OR-1", "or_name": "需求1", "or_total_score": 60},
                {"or_id": "OR-2", "or_name": "需求2", "or_total_score": 40},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            manifest_path = tmp / "manifest.json"
            partials_dir = tmp / "partials"
            output_path = tmp / "aggregate.json"
            partials_dir.mkdir()
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            (partials_dir / "partial-review-shard-001.json").write_text(
                json.dumps(partial, ensure_ascii=False),
                encoding="utf-8",
            )

            self.module.main(
                [
                    "--manifest",
                    str(manifest_path),
                    "--partials-dir",
                    str(partials_dir),
                    "--output",
                    str(output_path),
                ]
            )

            aggregated = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertTrue(aggregated["coverage_ok"])
        self.assertEqual(aggregated["or_results"][1]["or_id"], "OR-2")
        self.assertEqual(aggregated["grade_distribution"]["中等"], 1)
        self.assertEqual(aggregated["grade_distribution"]["较弱"], 1)


if __name__ == "__main__":
    unittest.main()
