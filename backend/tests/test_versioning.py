from app.core.versioning import build_dedupe_key, sha256_bytes, sha256_text


def test_sha256_text_is_stable() -> None:
    assert sha256_text("abc") == sha256_text("abc")


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
