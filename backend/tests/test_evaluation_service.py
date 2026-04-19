import json
import subprocess
from pathlib import Path
from unittest.mock import Mock

from app.clients.model_client import (
    CODEX_CLI_TIMEOUT_SECONDS,
    CodexModelClient,
    OpenAIModelClient,
    StaticModelClient,
    build_model_client,
    model_provider_name,
)
from app.core.config import Settings, get_settings
from app.runners.evaluation_runner import EvaluationRunner
from app.services.evaluation_service import EvaluationService
from app.storage.evaluation_store import EvaluationStore


def make_settings(
    *,
    openai_api_key: str | None = None,
    openai_model: str = "gpt-5.4",
    openai_base_url: str = "https://api.openai.com/v1",
    zhipu_api_key: str | None = None,
    zhipu_model: str = "glm-5",
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4",
    codex_model: str = "gpt-5.4",
    debug_fallback_enabled: bool = False,
) -> Settings:
    return Settings(
        data_dir=Path("/tmp/data"),
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_base_url=openai_base_url,
        zhipu_api_key=zhipu_api_key,
        zhipu_model=zhipu_model,
        zhipu_base_url=zhipu_base_url,
        codex_model=codex_model,
        debug_fallback_enabled=debug_fallback_enabled,
    )


def test_static_model_client_returns_markdown() -> None:
    client = StaticModelClient()
    report = client.generate_report(skill_text="skill", template_text="template", packet_text="packet")
    assert report.startswith("#")


def test_build_model_client_returns_static_client_without_provider_or_debug_fallback(monkeypatch) -> None:
    monkeypatch.setattr("app.clients.model_client.shutil.which", Mock(return_value=None))
    client = build_model_client(make_settings())
    assert isinstance(client, StaticModelClient)


def test_build_model_client_returns_static_client_for_debug_fallback_when_codex_is_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.clients.model_client.shutil.which", Mock(return_value=None))
    settings = make_settings(debug_fallback_enabled=True, codex_model="debug-codex-model")

    assert model_provider_name(settings) == "debug"
    client = build_model_client(settings)

    assert isinstance(client, StaticModelClient)


def test_build_model_client_prefers_openai_over_zhipu_codex_and_debug(monkeypatch) -> None:
    created_client = object()
    openai_factory = Mock(return_value=created_client)
    monkeypatch.setattr("app.clients.model_client.OpenAI", openai_factory)
    monkeypatch.setattr("app.clients.model_client.shutil.which", Mock(return_value="/usr/local/bin/codex"))
    settings = make_settings(
        openai_api_key="openai-key",
        openai_model="openai-model",
        openai_base_url="https://example.com/openai",
        zhipu_api_key="zhipu-key",
        zhipu_model="zhipu-model",
        zhipu_base_url="https://example.com/zhipu",
        debug_fallback_enabled=True,
    )

    assert model_provider_name(settings) == "openai"
    client = build_model_client(settings)

    assert isinstance(client, OpenAIModelClient)
    assert client.model_name == "openai-model"
    assert client.client is created_client
    openai_factory.assert_called_once_with(
        api_key="openai-key",
        base_url="https://example.com/openai",
    )


def test_build_model_client_uses_zhipu_over_codex_and_debug_when_openai_unavailable(monkeypatch) -> None:
    created_client = object()
    openai_factory = Mock(return_value=created_client)
    monkeypatch.setattr("app.clients.model_client.OpenAI", openai_factory)
    monkeypatch.setattr("app.clients.model_client.shutil.which", Mock(return_value="/usr/local/bin/codex"))
    settings = make_settings(
        zhipu_api_key="zhipu-key",
        zhipu_model="zhipu-model",
        zhipu_base_url="https://example.com/zhipu",
        debug_fallback_enabled=True,
    )

    assert model_provider_name(settings) == "zhipu"
    client = build_model_client(settings)

    assert isinstance(client, OpenAIModelClient)
    assert client.model_name == "zhipu-model"
    assert client.client is created_client
    openai_factory.assert_called_once_with(
        api_key="zhipu-key",
        base_url="https://example.com/zhipu",
    )


def test_build_model_client_returns_codex_when_cli_present_and_api_providers_absent(monkeypatch) -> None:
    monkeypatch.setattr("app.clients.model_client.shutil.which", Mock(return_value="/usr/local/bin/codex"))
    settings = make_settings(codex_model="codex-model", debug_fallback_enabled=True)

    assert model_provider_name(settings) == "codex"
    client = build_model_client(settings)

    assert isinstance(client, CodexModelClient)
    assert client.model_name == "codex-model"


def test_build_model_client_prefers_codex_over_debug_fallback(monkeypatch) -> None:
    monkeypatch.setattr("app.clients.model_client.shutil.which", Mock(return_value="/usr/local/bin/codex"))
    settings = make_settings(codex_model="codex-model", debug_fallback_enabled=True)

    assert model_provider_name(settings) == "codex"
    client = build_model_client(settings)

    assert isinstance(client, CodexModelClient)


def test_get_settings_normalizes_blank_provider_values_to_defaults(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "")
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.setenv("ZHIPU_API_KEY", "")
    monkeypatch.setenv("ZHIPU_MODEL", "")
    monkeypatch.setenv("ZHIPU_BASE_URL", "")
    monkeypatch.setenv("CODEX_MODEL", "")
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "")

    settings = get_settings()

    assert settings.openai_api_key is None
    assert settings.openai_model == "gpt-5.4"
    assert settings.openai_base_url == "https://api.openai.com/v1"
    assert settings.zhipu_api_key is None
    assert settings.zhipu_model == "glm-5"
    assert settings.zhipu_base_url == "https://open.bigmodel.cn/api/paas/v4"
    assert settings.codex_model == "gpt-5.4"
    assert settings.debug_fallback_enabled is False
    assert not hasattr(settings, "model_name")


def test_get_settings_enables_debug_fallback_only_for_one(monkeypatch) -> None:
    monkeypatch.setattr("app.clients.model_client.shutil.which", Mock(return_value=None))
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")
    assert get_settings().debug_fallback_enabled is True

    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "true")
    assert get_settings().debug_fallback_enabled is False

    monkeypatch.delenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", raising=False)
    assert model_provider_name(get_settings()) == "static"

    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")
    assert model_provider_name(get_settings()) == "debug"


def test_get_settings_reads_explicit_provider_values_unchanged(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "openai-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/openai")
    monkeypatch.setenv("ZHIPU_API_KEY", "zhipu-key")
    monkeypatch.setenv("ZHIPU_MODEL", "zhipu-model")
    monkeypatch.setenv("ZHIPU_BASE_URL", "https://example.com/zhipu")
    monkeypatch.setenv("CODEX_MODEL", "codex-model")
    monkeypatch.setenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", "1")

    settings = get_settings()

    assert settings.openai_api_key == "openai-key"
    assert settings.openai_model == "openai-model"
    assert settings.openai_base_url == "https://example.com/openai"
    assert settings.zhipu_api_key == "zhipu-key"
    assert settings.zhipu_model == "zhipu-model"
    assert settings.zhipu_base_url == "https://example.com/zhipu"
    assert settings.codex_model == "codex-model"
    assert settings.debug_fallback_enabled is True
    assert not hasattr(settings, "model_name")


def test_normalized_settings_drive_provider_selection_when_openai_key_is_blank(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "ignored-openai-model")
    monkeypatch.setenv("ZHIPU_API_KEY", "zhipu-key")
    monkeypatch.setenv("ZHIPU_MODEL", "zhipu-model")

    settings = get_settings()

    assert settings.openai_api_key is None
    assert model_provider_name(settings) == "zhipu"
    client = build_model_client(settings)
    assert isinstance(client, OpenAIModelClient)
    assert client.model_name == "zhipu-model"


def test_create_returns_new_evaluation_id_when_no_match(tmp_path: Path) -> None:
    service = EvaluationService(store=EvaluationStore(tmp_path))
    result = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")
    assert result.status == "pending"
    assert result.dedupe_hit is False


def test_create_reuses_existing_evaluation_when_dedupe_key_matches(tmp_path: Path) -> None:
    service = EvaluationService(store=EvaluationStore(tmp_path))
    first = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")
    second = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")
    assert second.evaluation_id == first.evaluation_id
    assert second.dedupe_hit is True


def test_create_makes_new_evaluation_when_matching_task_failed(tmp_path: Path) -> None:
    service = EvaluationService(store=EvaluationStore(tmp_path))
    first = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")
    metadata_path = tmp_path / first.evaluation_id / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["status"] = "failed"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    second = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")

    assert second.evaluation_id != first.evaluation_id
    assert second.dedupe_hit is False


def test_create_makes_new_evaluation_when_model_provider_changes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.delenv("REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK", raising=False)
    service = EvaluationService(store=EvaluationStore(tmp_path))
    first = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")

    monkeypatch.setenv("ZHIPU_API_KEY", "zhipu-key")
    monkeypatch.setenv("ZHIPU_MODEL", "zhipu-model")
    second = EvaluationService(store=EvaluationStore(tmp_path)).create_or_reuse(
        filename="requirements.csv",
        file_bytes=b"abc",
    )

    assert second.evaluation_id != first.evaluation_id
    assert second.dedupe_hit is False


def test_create_records_resolved_runtime_in_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ZHIPU_API_KEY", "zhipu-key")
    monkeypatch.setenv("ZHIPU_MODEL", "zhipu-model")
    monkeypatch.setenv("CODEX_MODEL", "codex-model")

    service = EvaluationService(store=EvaluationStore(tmp_path))
    result = service.create_or_reuse(filename="requirements.csv", file_bytes=b"abc")

    metadata = EvaluationStore(tmp_path).read_metadata(result.evaluation_id)
    assert metadata["model_provider"] == "zhipu"
    assert metadata["model_name"] == "zhipu-model"


def test_runner_writes_report_and_marks_success(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path)
    store.create_evaluation(
        evaluation_id="eval_001",
        filename="requirements.json",
        file_bytes=json.dumps(
            [{"OR需求编号": "D1", "OR需求名称*": "N", "OR需求描述*": "D"}],
            ensure_ascii=False,
        ).encode("utf-8"),
    )
    runner = EvaluationRunner(store=store, model_client=StaticModelClient())
    runner.run("eval_001")
    metadata = store.read_metadata("eval_001")
    assert metadata["status"] == "succeeded"


def test_runner_marks_evaluation_failed_when_packet_building_raises(tmp_path: Path, monkeypatch) -> None:
    store = EvaluationStore(tmp_path)
    store.create_evaluation(
        evaluation_id="eval_001",
        filename="requirements.csv",
        file_bytes="OR需求编号,OR需求名称*,OR需求描述*\nD1,N,D\n".encode("utf-8"),
    )
    monkeypatch.setattr(
        "app.runners.evaluation_runner.build_review_packet",
        Mock(side_effect=RuntimeError("boom")),
    )
    runner = EvaluationRunner(store=store, model_client=StaticModelClient())

    try:
        runner.run("eval_001")
    except RuntimeError:
        pass
    else:
        raise AssertionError("runner.run() did not re-raise packet builder failure")

    metadata = store.read_metadata("eval_001")
    assert metadata["status"] == "failed"
    assert metadata["error_message"] == "boom"


def test_openai_model_client_uses_responses_api_instructions_and_input() -> None:
    responses = Mock()
    responses.create.return_value = Mock(output_text="# Real Report")
    sdk_client = Mock(responses=responses)
    client = OpenAIModelClient(model_name="gpt-5.4", client=sdk_client)

    report = client.generate_report(
        skill_text="skill text",
        template_text="template text",
        packet_text="packet text",
    )

    assert report == "# Real Report"
    responses.create.assert_called_once_with(
        model="gpt-5.4",
        instructions=(
            "You are a requirements evaluation assistant. "
            "Follow the rubric and produce the final answer in Chinese Markdown using the template."
        ),
        input=(
            "[SKILL]\nskill text\n\n"
            "[TEMPLATE]\ntemplate text\n\n"
            "[PACKET]\npacket text\n"
        ),
    )


def test_codex_model_client_runs_subprocess_and_returns_trimmed_stdout(monkeypatch) -> None:
    run_mock = Mock(
        return_value=subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout="  # Codex Report  \n",
            stderr="",
        )
    )
    monkeypatch.setattr("app.clients.model_client.subprocess.run", run_mock)
    client = CodexModelClient(model_name="gpt-5.4")

    report = client.generate_report(
        skill_text="skill text",
        template_text="template text",
        packet_text="packet text",
    )

    assert report == "# Codex Report"
    run_mock.assert_called_once_with(
        [
            "codex",
            "exec",
            "--model",
            "gpt-5.4",
            (
                "You are a requirements evaluation assistant. "
                "Follow the rubric and produce the final answer in Chinese Markdown using the template.\n\n"
                "[SKILL]\n"
                "skill text\n\n"
                "[TEMPLATE]\n"
                "template text\n\n"
                "[PACKET]\n"
                "packet text\n"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=CODEX_CLI_TIMEOUT_SECONDS,
    )


def test_codex_model_client_raises_on_empty_stdout(monkeypatch) -> None:
    run_mock = Mock(
        return_value=subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout=" \n\t ",
            stderr="",
        )
    )
    monkeypatch.setattr("app.clients.model_client.subprocess.run", run_mock)
    client = CodexModelClient(model_name="gpt-5.4")

    try:
        client.generate_report(
            skill_text="skill text",
            template_text="template text",
            packet_text="packet text",
        )
    except RuntimeError as exc:
        assert str(exc) == "Codex CLI returned empty stdout."
    else:
        raise AssertionError("CodexModelClient.generate_report() did not raise on empty stdout")


def test_codex_model_client_raises_on_non_zero_exit_with_stderr_context(monkeypatch) -> None:
    run_mock = Mock(
        return_value=subprocess.CompletedProcess(
            args=["codex"],
            returncode=7,
            stdout="",
            stderr="authentication failed",
        )
    )
    monkeypatch.setattr("app.clients.model_client.subprocess.run", run_mock)
    client = CodexModelClient(model_name="gpt-5.4")

    try:
        client.generate_report(
            skill_text="skill text",
            template_text="template text",
            packet_text="packet text",
        )
    except RuntimeError as exc:
        assert str(exc) == "Codex CLI failed with exit code 7: authentication failed"
    else:
        raise AssertionError("CodexModelClient.generate_report() did not raise on non-zero exit")


def test_codex_model_client_raises_on_subprocess_timeout(monkeypatch) -> None:
    run_mock = Mock(
        side_effect=subprocess.TimeoutExpired(
            cmd=["codex", "exec"],
            timeout=CODEX_CLI_TIMEOUT_SECONDS,
        )
    )
    monkeypatch.setattr("app.clients.model_client.subprocess.run", run_mock)
    client = CodexModelClient(model_name="gpt-5.4")

    try:
        client.generate_report(
            skill_text="skill text",
            template_text="template text",
            packet_text="packet text",
        )
    except RuntimeError as exc:
        assert str(exc) == f"Codex CLI timed out after {CODEX_CLI_TIMEOUT_SECONDS} seconds."
    else:
        raise AssertionError("CodexModelClient.generate_report() did not raise on timeout")
