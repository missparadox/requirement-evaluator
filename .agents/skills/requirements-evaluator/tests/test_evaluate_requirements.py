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
        self.assertEqual(by_key["or_user_language"]["weight"], 12)
        self.assertEqual(by_key["dr_technical"]["weight"], 10)
        self.assertEqual(by_key["cross_scope"]["weight"], 6)
        self.assertEqual(sum(item["weight"] for item in dimensions if item["key"].startswith("or_")), 40)
        self.assertEqual(sum(item["weight"] for item in dimensions if item["key"].startswith("dr_")), 40)
        self.assertEqual(sum(item["weight"] for item in dimensions if item["key"].startswith("cross_")), 20)
        self.assertEqual(by_key["or_scenario"]["name"], "OR-应用场景")

    def test_build_review_packet_keeps_rows_and_core_fields(self):
        record_1 = self.module.RowRecord(
            index=1,
            grouped={
                "OR需求编号": ["DOR-1"],
                "OR需求名称*": ["网络检测与诊断"],
                "OR需求描述*": ["提供网络检测与维护功能。"],
                "需求来源": ["客户定制"],
                "国家/区域": ["中国"],
                "DR需求编号": ["DDR-1"],
                "DR需求名称*": ["Ping检测"],
                "DR需求描述*": ["支持 Ping 检测。"],
                "参数规格": ["次数 1-10"],
                "系统测试要点": ["校验 Ping 输入"],
                "DS需求名称*": ["Ping规格"],
                "规格分类": ["接口规格"],
                "所属子系统": ["网络管理"],
            },
        )
        record_2 = self.module.RowRecord(
            index=2,
            grouped={
                "OR需求编号": ["DOR-1"],
                "OR需求名称*": ["网络检测与诊断"],
                "OR需求描述*": ["提供网络检测与维护功能。"],
                "需求来源": ["客户定制"],
                "国家/区域": ["中国"],
                "DR需求编号": ["DDR-2"],
                "DR需求名称*": ["Telnet检测"],
                "DR需求描述*": ["支持 Telnet 检测。"],
                "参数规格": ["端口 1-65535"],
                "系统测试要点": ["校验 Telnet 输入"],
                "DS需求名称*": ["Telnet规格"],
                "规格分类": ["接口规格"],
                "所属子系统": ["网络管理"],
            },
        )

        packet = self.module.build_review_packet(
            input_path=Path("requirements.json"),
            dimensions=self.module.DEFAULT_DIMENSIONS,
            records=[record_1, record_2],
            source_info={"input_format": "json"},
        )

        self.assertEqual(packet["item_count"], 1)
        self.assertEqual(packet["or_count"], 1)
        self.assertEqual(packet["dr_count"], 2)
        self.assertEqual(packet["score_structure"]["or_total_weight"], 40)
        self.assertEqual(packet["score_structure"]["dr_total_weight"], 40)
        self.assertEqual(packet["score_structure"]["cross_total_weight"], 20)
        self.assertEqual(packet["source_info"]["input_format"], "json")
        self.assertEqual(packet["groups"][0]["id"], "DOR-1")
        self.assertIn("raw_fields", packet["groups"][0])
        self.assertIn("or_dimension_view", packet["groups"][0])
        self.assertIn("cross_dimension_view", packet["groups"][0])
        self.assertEqual(packet["groups"][0]["or_core_fields"]["requirement_source"], "客户定制")
        self.assertEqual(packet["groups"][0]["or_core_fields"]["region"], "中国")
        self.assertEqual(packet["groups"][0]["dr_count"], 2)
        self.assertEqual(packet["groups"][0]["review_skeleton"]["or_total_score"]["max_score"], 100)
        self.assertEqual(packet["groups"][0]["review_skeleton"]["or_part"]["max_score"], 40)
        self.assertEqual(packet["groups"][0]["review_skeleton"]["dr_average"]["max_score"], 40)
        self.assertEqual(packet["groups"][0]["review_skeleton"]["decomposition_quality"]["max_score"], 20)
        self.assertEqual(len(packet["groups"][0]["review_skeleton"]["dr_parts"]), 2)
        self.assertEqual(packet["groups"][0]["dr_items"][0]["core_fields"]["dr_desc"], "支持 Ping 检测。")
        self.assertEqual(packet["groups"][0]["dr_items"][0]["core_fields"]["spec_type"], "接口规格")
        self.assertEqual(packet["groups"][0]["dr_items"][0]["core_fields"]["subsystem"], "网络管理")
        self.assertIn("dr_testability", packet["groups"][0]["dr_items"][0]["dimension_view"])
        self.assertEqual(packet["groups"][0]["or_dimension_view"]["or_constraints"]["evidence_fields"]["国家/区域"], ["中国"])
        self.assertEqual(packet["groups"][0]["dr_items"][0]["dimension_view"]["dr_technical"]["evidence_fields"]["规格分类"], ["接口规格"])
        self.assertEqual(packet["groups"][0]["cross_dimension_view"]["cross_dependencies"]["evidence_fields"]["所属子系统"], ["网络管理"])

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
            source_info={"input_format": "json"},
        )
        dim_view = packet["groups"][0]["dr_items"][0]["dimension_view"]

        self.assertIn("dr_testability", dim_view)
        self.assertIn("系统测试要点", dim_view["dr_testability"]["mapped_fields"])
        self.assertIn("系统测试要点", dim_view["dr_testability"]["missing_fields"])
        self.assertEqual(dim_view["dr_testability"]["evidence_fields"]["参数规格"], ["字段长度 1-64"])

    def test_rendered_markdown_is_a_review_packet_not_a_scored_report(self):
        packet = {
            "input_path": "requirements.json",
            "source_info": {"input_format": "json", "sheet_name": "Sheet1"},
            "score_structure": {"or_total_weight": 40, "dr_total_weight": 40, "cross_total_weight": 20},
            "item_count": 1,
            "or_count": 1,
            "dr_count": 2,
            "dimension_count": 1,
            "dimensions": [{"key": "dr_technical", "name": "DR-技术描述", "weight": 10, "description": "desc"}],
            "header_summary": ["OR需求编号", "DR需求描述*"],
            "groups": [
                {
                    "row_indices": [1, 2],
                    "id": "DOR-1",
                    "name": "DNS配置",
                    "or_core_fields": {"or_desc": "支持 DNS"},
                    "or_dimension_view": {},
                    "dr_count": 2,
                    "dr_items": [
                        {
                            "row_indices": [1],
                            "id": "DDR-1",
                            "name": "Ping检测",
                            "core_fields": {"dr_desc": "IP 0-255"},
                            "dimension_view": {
                                "dr_technical": {
                                    "name": "DR-技术描述",
                                    "mapped_fields": ["DR需求描述*", "参数规格"],
                                    "evidence_fields": {"DR需求描述*": ["IP 0-255"]},
                                    "missing_fields": ["参数规格"],
                                }
                            },
                            "raw_fields": {"DR需求描述*": ["IP 0-255"]},
                        }
                    ],
                    "cross_dimension_view": {
                        "cross_dependencies": {
                            "name": "需求分解边界清晰度",
                            "mapped_fields": ["假设和依赖信息"],
                            "evidence_fields": {},
                            "missing_fields": ["假设和依赖信息"],
                        }
                    },
                    "review_skeleton": {
                        "or_total_score": {"max_score": 100, "score": None, "grade": None, "review_conclusion": None},
                        "or_part": {"max_score": 40, "score": None, "dimension_scores": []},
                        "dr_parts": [{"dr_id": "DDR-1", "dr_name": "Ping检测", "max_score": 40, "score": None, "dimension_scores": []}],
                        "dr_average": {"max_score": 40, "score": None},
                        "decomposition_quality": {"max_score": 20, "score": None, "dimension_scores": []},
                        "review_decision": {
                            "design_review_readiness": None,
                            "development_readiness": None,
                            "test_design_readiness": None,
                            "blocking_issues": [],
                            "triggered_red_line_rules": [],
                        },
                    },
                    "raw_fields": {"OR需求编号": ["DOR-1"], "DR需求描述*": ["IP 0-255"]},
                }
            ],
        }

        rendered = self.module.render_review_packet_markdown(packet)

        self.assertIn("# 需求评审任务包", rendered)
        self.assertIn("## 评分结构", rendered)
        self.assertIn("- OR部分: 40", rendered)
        self.assertIn("- DR数量: 2", rendered)
        self.assertIn("- sheet_name: `Sheet1`", rendered)
        self.assertIn("DR评审单元", rendered)
        self.assertIn("需求分解与追踪维度视图", rendered)
        self.assertIn("评分骨架", rendered)
        self.assertIn("- OR总分槽位: 100", rendered)
        self.assertNotIn("总分:", rendered)
        self.assertNotIn("等级:", rendered)

    def test_cli_json_output_writes_packet(self):
        rows = [
            {
                "OR需求编号": "DOR-1",
                "OR需求名称*": "网络检测与诊断",
                "OR需求描述*": "提供网络检测与维护功能。",
                "DR需求编号": "DDR-1",
                "DR需求名称*": "Ping检测",
                "DR需求描述*": "支持 Ping 检测。",
            },
            {
                "OR需求编号": "DOR-1",
                "OR需求名称*": "网络检测与诊断",
                "OR需求描述*": "提供网络检测与维护功能。",
                "DR需求编号": "DDR-2",
                "DR需求名称*": "Telnet检测",
                "DR需求描述*": "支持 Telnet 检测。",
            },
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
        self.assertEqual(packet["or_count"], 1)
        self.assertEqual(packet["dr_count"], 2)
        self.assertEqual(packet["source_info"]["input_format"], "json")
        self.assertEqual(packet["groups"][0]["name"], "网络检测与诊断")
        self.assertIn("review_skeleton", packet["groups"][0])

    def test_build_packet_manifest_splits_groups_by_shard_size(self):
        record_1 = self.module.RowRecord(
            index=1,
            grouped={
                "OR需求编号": ["DOR-1"],
                "OR需求名称*": ["需求1"],
                "OR需求描述*": ["描述1"],
                "DR需求编号": ["DDR-1"],
                "DR需求名称*": ["设计1"],
                "DR需求描述*": ["设计描述1"],
            },
        )
        record_2 = self.module.RowRecord(
            index=2,
            grouped={
                "OR需求编号": ["DOR-2"],
                "OR需求名称*": ["需求2"],
                "OR需求描述*": ["描述2"],
                "DR需求编号": ["DDR-2"],
                "DR需求名称*": ["设计2"],
                "DR需求描述*": ["设计描述2"],
            },
        )
        record_3 = self.module.RowRecord(
            index=3,
            grouped={
                "OR需求编号": ["DOR-3"],
                "OR需求名称*": ["需求3"],
                "OR需求描述*": ["描述3"],
                "DR需求编号": ["DDR-3"],
                "DR需求名称*": ["设计3"],
                "DR需求描述*": ["设计描述3"],
            },
        )

        packet = self.module.build_review_packet(
            input_path=Path("requirements.json"),
            dimensions=self.module.DEFAULT_DIMENSIONS,
            records=[record_1, record_2, record_3],
            source_info={"input_format": "json"},
        )
        manifest = self.module.build_packet_manifest(packet, shard_size=2, max_chars_per_shard=None)
        shard_packets = self.module.build_shard_packets(packet, manifest)

        self.assertEqual(manifest["shard_count"], 2)
        self.assertEqual(manifest["shards"][0]["or_ids"], ["DOR-1", "DOR-2"])
        self.assertEqual(manifest["shards"][1]["or_ids"], ["DOR-3"])
        self.assertEqual(shard_packets[0]["shard_id"], "shard-001")
        self.assertEqual(shard_packets[0]["or_count"], 2)
        self.assertEqual(shard_packets[1]["or_count"], 1)
        self.assertEqual(shard_packets[0]["groups"][0]["id"], "DOR-1")

    def test_cli_shard_mode_writes_manifest_and_shards(self):
        rows = [
            {
                "OR需求编号": "DOR-1",
                "OR需求名称*": "需求1",
                "OR需求描述*": "描述1",
                "DR需求编号": "DDR-1",
                "DR需求名称*": "设计1",
                "DR需求描述*": "设计描述1",
            },
            {
                "OR需求编号": "DOR-2",
                "OR需求名称*": "需求2",
                "OR需求描述*": "描述2",
                "DR需求编号": "DDR-2",
                "DR需求名称*": "设计2",
                "DR需求描述*": "设计描述2",
            },
            {
                "OR需求编号": "DOR-3",
                "OR需求名称*": "需求3",
                "OR需求描述*": "描述3",
                "DR需求编号": "DDR-3",
                "DR需求名称*": "设计3",
                "DR需求描述*": "设计描述3",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / "requirements.json"
            output_dir = tmp / "packets"
            input_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

            self.module.main(
                [
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_dir),
                    "--format",
                    "json",
                    "--shard-size",
                    "2",
                    "--emit-manifest",
                ]
            )

            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
            shard_1 = json.loads((output_dir / "shard-001.json").read_text(encoding="utf-8"))
            shard_2 = json.loads((output_dir / "shard-002.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["shard_count"], 2)
        self.assertEqual(manifest["or_count"], 3)
        self.assertEqual(shard_1["packet_type"], "review_packet_shard")
        self.assertEqual(shard_1["or_count"], 2)
        self.assertEqual(shard_2["or_count"], 1)
        self.assertEqual(shard_2["groups"][0]["id"], "DOR-3")

    def test_read_excel_records_active_sheet_name_in_source_info(self):
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl is not installed in the current test environment")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / "requirements.xlsx"

            workbook = openpyxl.Workbook()
            default_sheet = workbook.active
            default_sheet.title = "Sheet1"
            default_sheet["A1"] = "OR需求编号"
            default_sheet["B1"] = "OR需求名称*"
            default_sheet["C1"] = "OR需求描述*"
            default_sheet["D1"] = "DR需求编号"
            default_sheet["E1"] = "DR需求名称*"
            default_sheet["F1"] = "DR需求描述*"

            default_sheet["A2"] = "DOR-1"
            default_sheet["B2"] = "网络检测与诊断"
            default_sheet["C2"] = "提供网络检测与维护功能。"
            default_sheet["D2"] = "DDR-1"
            default_sheet["E2"] = "Ping检测"
            default_sheet["F2"] = "支持 Ping 检测。"
            default_sheet["D3"] = "DDR-2"
            default_sheet["E3"] = "Telnet检测"
            default_sheet["F3"] = "支持 Telnet 检测。"
            default_sheet.merge_cells("A2:A3")
            default_sheet.merge_cells("B2:B3")
            default_sheet.merge_cells("C2:C3")
            workbook.create_sheet("OtherSheet")
            workbook.save(input_path)

            result = self.module.read_excel(input_path)

        self.assertEqual(result.source_info["sheet_name"], "Sheet1")
        self.assertEqual(result.source_info["input_format"], "xlsx")
        self.assertEqual(len(result.records), 2)
        self.assertEqual(result.records[1].first("OR需求编号"), "DOR-1")
        self.assertEqual(result.records[1].first("OR需求名称*"), "网络检测与诊断")


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
