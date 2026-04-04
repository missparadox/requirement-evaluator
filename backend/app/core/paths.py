from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "requirements-evaluator"
SKILL_FILE = SKILL_ROOT / "SKILL.md"
REPORT_TEMPLATE_FILE = SKILL_ROOT / "references" / "report-template.md"
PACKET_BUILDER_FILE = SKILL_ROOT / "scripts" / "evaluate_requirements.py"
DATA_ROOT = REPO_ROOT / "data"
EVALUATIONS_ROOT = DATA_ROOT / "evaluations"
