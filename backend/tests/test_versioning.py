import subprocess
from pathlib import Path

from app.core.versioning import build_dedupe_key, sha256_bytes, sha256_text
from app.core import versioning


def test_sha256_text_is_stable() -> None:
    assert sha256_text("abc") == sha256_text("abc")


def test_sha256_bytes_known_digest() -> None:
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_dedupe_key_changes_when_model_changes() -> None:
    first = build_dedupe_key(
        input_fingerprint="input",
        skill_version="skill",
        report_template_version="template",
        model_name="gpt-5.4",
        app_version="commit-a",
    )
    second = build_dedupe_key(
        input_fingerprint="input",
        skill_version="skill",
        report_template_version="template",
        model_name="gpt-5.4-mini",
        app_version="commit-a",
    )
    assert first != second


def test_detect_app_version_returns_dev_when_git_is_missing(monkeypatch) -> None:
    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", raise_file_not_found)
    assert versioning.detect_app_version(Path(".")) == "dev"
