import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "summarize_evaluation_reports.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_reports_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SummarizeEvaluationReportsTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_discover_summary_paths_accepts_markdown_with_sidecar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            report_path = tmp / "project-a.md"
            summary_path = tmp / "project-a.summary.json"
            report_path.write_text("# report\n", encoding="utf-8")
            summary_path.write_text("{}", encoding="utf-8")

            result = self.module.discover_summary_paths([str(report_path)])

        self.assertEqual(result, [summary_path.resolve()])

    def test_render_markdown_summary_compares_projects(self):
        projects = [
            {
                "project_name": "project-a",
                "average_score": 82.0,
                "scored_or_count": 10,
                "unscored_or_count": 0,
                "grade_distribution": {"excellent": 2, "good": 6, "fair": 2, "poor": 0},
                "missing_counts": [["验收标准", 3]],
                "revision_counts": [["补充验收标准", 2]],
                "dimension_summary": [
                    {"key": "or_user_language", "name": "OR-用户语言描述", "normalized_average_score": 88.0},
                    {"key": "dr_testability", "name": "DR-可测试性", "normalized_average_score": 79.0},
                ],
            },
            {
                "project_name": "project-b",
                "average_score": 68.0,
                "scored_or_count": 12,
                "unscored_or_count": 1,
                "grade_distribution": {"excellent": 0, "good": 4, "fair": 6, "poor": 2},
                "missing_counts": [["异常处理", 4]],
                "revision_counts": [["补充异常处理", 3]],
                "dimension_summary": [
                    {"key": "or_user_language", "name": "OR-用户语言描述", "normalized_average_score": 72.0},
                    {"key": "dr_testability", "name": "DR-可测试性", "normalized_average_score": 61.0},
                ],
            },
        ]

        report = self.module.render_markdown_summary(projects)

        self.assertIn("# 需求评估项目对比报告", report)
        self.assertIn("| 1 | project-a | 82.00 |", report)
        self.assertIn("| 2 | project-b | 68.00 |", report)
        self.assertIn("| OR-用户语言描述 | 80.00 | project-a | 88.00 | project-b | 72.00 |", report)
        self.assertIn("### project-b", report)
        self.assertIn("薄弱维度", report)

    def test_main_writes_markdown_and_json_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            summary_a = tmp / "project-a.summary.json"
            summary_b = tmp / "project-b.summary.json"
            output_md = tmp / "portfolio.md"
            output_json = tmp / "portfolio.json"
            payload_a = {
                "project_name": "project-a",
                "average_score": 82.0,
                "scored_or_count": 10,
                "unscored_or_count": 0,
                "grade_distribution": {"excellent": 2, "good": 6, "fair": 2, "poor": 0},
                "missing_counts": [["验收标准", 3]],
                "revision_counts": [["补充验收标准", 2]],
                "dimension_summary": [
                    {"key": "or_user_language", "name": "OR-用户语言描述", "normalized_average_score": 88.0},
                    {"key": "dr_testability", "name": "DR-可测试性", "normalized_average_score": 79.0},
                ],
            }
            payload_b = {
                "project_name": "project-b",
                "average_score": 68.0,
                "scored_or_count": 12,
                "unscored_or_count": 1,
                "grade_distribution": {"excellent": 0, "good": 4, "fair": 6, "poor": 2},
                "missing_counts": [["异常处理", 4]],
                "revision_counts": [["补充异常处理", 3]],
                "dimension_summary": [
                    {"key": "or_user_language", "name": "OR-用户语言描述", "normalized_average_score": 72.0},
                    {"key": "dr_testability", "name": "DR-可测试性", "normalized_average_score": 61.0},
                ],
            }
            summary_a.write_text(json.dumps(payload_a, ensure_ascii=False), encoding="utf-8")
            summary_b.write_text(json.dumps(payload_b, ensure_ascii=False), encoding="utf-8")

            self.module.main(
                [
                    "--input",
                    str(tmp),
                    "--output",
                    str(output_md),
                    "--json-output",
                    str(output_json),
                ]
            )

            markdown = output_md.read_text(encoding="utf-8")
            payload = json.loads(output_json.read_text(encoding="utf-8"))

        self.assertIn("project-a", markdown)
        self.assertEqual(payload["project_count"], 2)
        self.assertEqual(payload["projects"][0]["project_name"], "project-a")


if __name__ == "__main__":
    unittest.main()
