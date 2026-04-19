import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_requirements.py"


def load_module():
    spec = importlib.util.spec_from_file_location("requirements_eval_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RequirementsEvaluatorPacketTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_build_dimensions_returns_default_rubric(self):
        dimensions = self.module.build_dimensions()
        by_key = {item["key"]: item for item in dimensions}
        self.assertEqual(by_key["dr_technical"]["weight"], 8)
        self.assertEqual(by_key["or_scenario"]["name"], "OR-应用场景")

    def test_build_review_packet_keeps_rows_and_core_fields(self):
        record = self.module.RowRecord(
            index=1,
            grouped={
                "OR需求编号": ["DOR-1"],
                "OR需求名称*": ["DNS配置"],
                "OR需求描述*": ["支持 DNS 服务器配置。"],
                "DR需求编号": ["DDR-1"],
                "DR需求描述*": ["IP 地址必填，分段输入，范围 0-255。"],
                "参数规格": ["0-255"],
                "系统测试要点": ["校验必填项和非法 IP"],
            },
        )

        packet = self.module.build_review_packet(
            input_path=Path("requirements.json"),
            dimensions=self.module.DEFAULT_DIMENSIONS,
            records=[record],
        )

        self.assertEqual(packet["item_count"], 1)
        self.assertEqual(packet["items"][0]["id"], "DOR-1")
        self.assertIn("raw_fields", packet["items"][0])
        self.assertIn("dimension_view", packet["items"][0])
        self.assertEqual(packet["items"][0]["core_fields"]["dr_desc"], "IP 地址必填，分段输入，范围 0-255。")
        self.assertIn("dr_testability", packet["items"][0]["dimension_view"])

    def test_dimension_view_is_based_on_rubric_relevance_not_on_non_empty_frequency(self):
        record = self.module.RowRecord(
            index=1,
            grouped={
                "OR需求编号": ["DOR-2"],
                "OR需求名称*": ["设备接入"],
                "OR需求描述*": ["支持设备接入。"],
                "DR需求描述*": ["设备接入需校验参数格式。"],
                "参数规格": ["字段长度 1-64"],
            },
        )

        packet = self.module.build_review_packet(
            input_path=Path("sample.json"),
            dimensions=self.module.DEFAULT_DIMENSIONS,
            records=[record],
        )
        dim_view = packet["items"][0]["dimension_view"]

        self.assertIn("dr_testability", dim_view)
        self.assertIn("系统测试要点", dim_view["dr_testability"]["mapped_fields"])
        self.assertIn("系统测试要点", dim_view["dr_testability"]["missing_fields"])
        self.assertEqual(dim_view["dr_testability"]["evidence_fields"]["参数规格"], ["字段长度 1-64"])

    def test_rendered_markdown_is_a_review_packet_not_a_scored_report(self):
        packet = {
            "input_path": "requirements.json",
            "item_count": 1,
            "dimension_count": 1,
            "dimensions": [{"key": "dr_technical", "name": "DR-技术描述", "weight": 10, "description": "desc"}],
            "header_summary": ["OR需求编号", "DR需求描述*"],
            "items": [
                {
                    "row_index": 1,
                    "id": "DOR-1",
                    "name": "DNS配置",
                    "core_fields": {"or_desc": "支持 DNS", "dr_desc": "IP 0-255"},
                    "dimension_view": {
                        "dr_technical": {
                            "name": "DR-技术描述",
                            "mapped_fields": ["DR需求描述*", "参数规格"],
                            "evidence_fields": {"DR需求描述*": ["IP 0-255"]},
                            "missing_fields": ["参数规格"],
                        }
                    },
                    "raw_fields": {"OR需求编号": ["DOR-1"], "DR需求描述*": ["IP 0-255"]},
                }
            ],
        }

        rendered = self.module.render_review_packet_markdown(packet)

        self.assertIn("# 需求评审任务包", rendered)
        self.assertIn("## 评审维度", rendered)
        self.assertIn("维度视图", rendered)
        self.assertNotIn("总分:", rendered)
        self.assertNotIn("等级:", rendered)

    def test_cli_json_output_writes_packet(self):
        rows = [
            {
                "OR需求编号": "DOR-1",
                "OR需求名称*": "DNS配置",
                "OR需求描述*": "支持 DNS 服务器配置。",
                "DR需求描述*": "IP 地址必填，分段输入，范围 0-255。",
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / "requirements.json"
            output_path = tmp / "packet.json"
            input_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

            self.module.main(
                [
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--format",
                    "json",
                ]
            )

            packet = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(packet["item_count"], 1)
        self.assertEqual(packet["items"][0]["name"], "DNS配置")

    def test_missing_excel_dependency_message_contains_install_command(self):
        original_find_spec = self.module.importlib.util.find_spec

        def fake_find_spec(name):
            if name == "openpyxl":
                return None
            return original_find_spec(name)

        self.module.importlib.util.find_spec = fake_find_spec
        try:
            with self.assertRaises(SystemExit) as ctx:
                self.module.ensure_runtime_dependencies(Path("input.xlsx"))
        finally:
            self.module.importlib.util.find_spec = original_find_spec

        message = str(ctx.exception)
        self.assertIn("openpyxl", message)
        self.assertIn("python3 -m pip install openpyxl", message)


if __name__ == "__main__":
    unittest.main()
