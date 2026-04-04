from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    model_name: str


def get_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = Path(os.environ.get("REQUIREMENTS_EVALUATOR_DATA_DIR", repo_root / "data"))
    model_name = os.environ.get("REQUIREMENTS_EVALUATOR_MODEL", "gpt-5.4")
    return Settings(data_dir=data_dir, model_name=model_name)
