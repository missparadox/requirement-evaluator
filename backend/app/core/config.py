from dataclasses import dataclass
from pathlib import Path
import os

from app.core.paths import REPO_ROOT


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    model_name: str


def get_settings() -> Settings:
    data_dir = Path(os.environ.get("REQUIREMENTS_EVALUATOR_DATA_DIR", REPO_ROOT / "data"))
    model_name = os.environ.get("REQUIREMENTS_EVALUATOR_MODEL", "gpt-5.4")
    return Settings(data_dir=data_dir, model_name=model_name)
