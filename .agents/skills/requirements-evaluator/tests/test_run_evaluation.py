import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "run_evaluation.py"
BACKEND_ROOT = Path(__file__).resolve().parents[4] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.clients.model_client import StaticModelClient  # noqa: E402
from app.core.config import Settings  # noqa: E402


def load_module():
    spec = importlib.util.spec_from_file_location("run_evaluation_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RunEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_run_pipeline_generates_report_without_human_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / "requirements.json"
            work_dir = tmp / "work"
            report_path = tmp / "report.md"
            input_path.write_text(
                json.dumps(
                    [
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
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            self.module.build_model_client = lambda settings: StaticModelClient()
            self.module.get_settings = lambda: Settings(
                data_dir=tmp / "data",
                openai_api_key=None,
                openai_model="gpt-5.4",
                openai_base_url="https://api.openai.com/v1",
                zhipu_api_key=None,
                zhipu_model="glm-5",
                zhipu_base_url="https://open.bigmodel.cn/api/paas/v4",
                codex_model="gpt-5.4",
                debug_fallback_enabled=True,
            )

            result = self.module.run_pipeline(
                input_path=input_path,
                report_output_path=report_path,
                work_dir=work_dir,
                shard_size=1,
                max_chars_per_shard=10000,
                provider="static",
            )

            aggregate = json.loads((work_dir / "aggregate.json").read_text(encoding="utf-8"))
            self.assertEqual(result["shard_count"], 2)
            self.assertTrue(report_path.exists())
            self.assertIn("# Mock Report", report_path.read_text(encoding="utf-8"))
            self.assertTrue((work_dir / "packets" / "manifest.json").exists())
            self.assertTrue((work_dir / "partials" / "partial-review-shard-001.json").exists())
            self.assertTrue(aggregate["coverage_ok"])
            self.assertEqual(len(aggregate["or_results"]), 2)


if __name__ == "__main__":
    unittest.main()
