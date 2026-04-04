from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.core.paths import PACKET_BUILDER_FILE


def build_review_packet(*, input_path: Path, output_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PACKET_BUILDER_FILE),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Packet builder failed")
