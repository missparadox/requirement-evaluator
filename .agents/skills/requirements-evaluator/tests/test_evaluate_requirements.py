import importlib.util
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


def make_record(module, mapping):
    grouped = {key: [value] for key, value in mapping.items()}
    return module.RowRecord(index=1, grouped=grouped)


class RequirementsEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.dimensions = self.module.DEFAULT_DIMENSIONS

    def test_technical_requirement_can_score_well_when_non_applicable_dimensions_are_absent(self):
        record = make_record(
            self.module,
            {
                "OR需求编号": "DOR-1",
                "OR需求名称*": "调阅方配置",
                "OR需求描述*": "支持配置调阅方信息。",
                "DR需求编号": "DDR-1",
                "DR需求名称*": "调阅方配置",
                "DR需求描述*": (
                    "用户通过界面添加调阅平台。正常过程包括参数校验、唯一性校验、"
                    "调用 API 和记录日志。异常过程包括名称重复、模板无效、参数格式错误、API 调用失败。"
                ),
                "参数规格": "端口 1-65535，名称 1-20 字符，IP 为 IPv4 地址。",
                "操作场景": "管理员在平台配置页面新增调阅方。",
                "安全约束": "记录审计日志，仅管理员可配置。",
            },
        )

        result = self.module.score_row(record, self.dimensions)

        self.assertGreaterEqual(result["total"], 65)
        self.assertIn(result["grade"], {"B", "A"})

    def test_non_performance_requirement_does_not_get_performance_credit_without_explicit_target(self):
        record = make_record(
            self.module,
            {
                "OR需求编号": "DOR-2",
                "OR需求名称*": "满足红线",
                "OR需求描述*": "产品需满足安全红线。",
                "DR需求编号": "DDR-2",
                "DR需求名称*": "满足红线",
                "DR需求描述*": "所有信息存储满足红线要求，开放端口满足业务必须原则。",
            },
        )

        result = self.module.score_row(record, self.dimensions)
        by_key = {item["key"]: item for item in result["scores"]}

        self.assertEqual(by_key["dr_performance"]["score"], 0)

    def test_missing_testability_and_exceptions_keeps_requirement_low(self):
        record = make_record(
            self.module,
            {
                "OR需求编号": "DOR-3",
                "OR需求名称*": "DNS配置",
                "OR需求描述*": "支持 DNS 服务器配置，包括首选和备选 DNS。",
                "DR需求编号": "DDR-3",
                "DR需求名称*": "DNS配置",
                "DR需求描述*": "IP 地址必填，分段输入，范围 0-255。",
            },
        )

        result = self.module.score_row(record, self.dimensions)
        by_key = {item["key"]: item for item in result["scores"]}

        self.assertLess(result["total"], 55)
        self.assertLessEqual(by_key["dr_testability"]["score"], 4)
        self.assertLessEqual(by_key["cross_exceptions"]["score"], 2)

    def test_custom_dimension_file_keeps_names_but_uses_internal_weight_profile_for_known_keys(self):
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as handle:
            handle.write(
                '"dr_technical": {\n'
                '  "name": "DR-技术描述",\n'
                '  "weight": 8,\n'
                '  "description": "custom"\n'
                '}\n'
            )
            handle.flush()
            dimensions = self.module.build_dimensions(Path(handle.name))

        by_key = {item["key"]: item for item in dimensions}

        self.assertEqual(by_key["dr_technical"]["name"], "DR-技术描述")
        self.assertEqual(by_key["dr_technical"]["weight"], 14)


if __name__ == "__main__":
    unittest.main()
