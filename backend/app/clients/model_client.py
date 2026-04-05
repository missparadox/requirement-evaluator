import shutil
import subprocess
from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI

from app.core.config import Settings

REPORT_INSTRUCTIONS = (
    "You are a requirements evaluation assistant. "
    "Follow the rubric and produce the final answer in Chinese Markdown using the template."
)
CODEX_CLI_TIMEOUT_SECONDS = 300


class ModelClient(Protocol):
    def generate_report(self, *, skill_text: str, template_text: str, packet_text: str) -> str: ...


def _build_tagged_prompt(*, skill_text: str, template_text: str, packet_text: str) -> str:
    return (
        "[SKILL]\n"
        f"{skill_text}\n\n"
        "[TEMPLATE]\n"
        f"{template_text}\n\n"
        "[PACKET]\n"
        f"{packet_text}\n"
    )


class StaticModelClient:
    def generate_report(self, *, skill_text: str, template_text: str, packet_text: str) -> str:
        return "# Mock Report\n\nReplace this client with the real model integration.\n"


@dataclass
class OpenAIModelClient:
    model_name: str
    client: OpenAI

    def generate_report(self, *, skill_text: str, template_text: str, packet_text: str) -> str:
        response = self.client.responses.create(
            model=self.model_name,
            instructions=REPORT_INSTRUCTIONS,
            input=_build_tagged_prompt(
                skill_text=skill_text,
                template_text=template_text,
                packet_text=packet_text,
            ),
        )
        if not response.output_text:
            raise RuntimeError("OpenAI response did not contain output_text.")
        return response.output_text


@dataclass
class CodexModelClient:
    model_name: str

    def generate_report(self, *, skill_text: str, template_text: str, packet_text: str) -> str:
        prompt = f"{REPORT_INSTRUCTIONS}\n\n" + _build_tagged_prompt(
            skill_text=skill_text,
            template_text=template_text,
            packet_text=packet_text,
        )
        try:
            result = subprocess.run(
                ["codex", "exec", "--model", self.model_name, prompt],
                capture_output=True,
                text=True,
                timeout=CODEX_CLI_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Codex CLI timed out after {CODEX_CLI_TIMEOUT_SECONDS} seconds."
            ) from exc
        if result.returncode != 0:
            stderr = result.stderr.strip() or "no stderr output"
            raise RuntimeError(
                f"Codex CLI failed with exit code {result.returncode}: {stderr}"
            )

        report = result.stdout.strip()
        if not report:
            raise RuntimeError("Codex CLI returned empty stdout.")
        return report


@dataclass(frozen=True)
class ResolvedModelRuntime:
    provider_name: str
    model_name: str
    api_key: str | None = None
    base_url: str | None = None


NO_MODEL_PROVIDER_ERROR_MESSAGE = (
    "No model provider is available. Checked OPENAI_API_KEY, ZHIPU_API_KEY, "
    "Codex CLI availability on PATH via `codex`, and "
    "REQUIREMENTS_EVALUATOR_DEBUG_FALLBACK=1 for local debugging. "
    "The static placeholder runtime is not valid for application startup."
)


def resolve_model_runtime(settings: Settings) -> ResolvedModelRuntime:
    if settings.openai_api_key is not None:
        return ResolvedModelRuntime(
            provider_name="openai",
            model_name=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
    if settings.zhipu_api_key is not None:
        return ResolvedModelRuntime(
            provider_name="zhipu",
            model_name=settings.zhipu_model,
            api_key=settings.zhipu_api_key,
            base_url=settings.zhipu_base_url,
        )
    if shutil.which("codex") is not None:
        return ResolvedModelRuntime(
            provider_name="codex",
            model_name=settings.codex_model,
        )
    if settings.debug_fallback_enabled:
        return ResolvedModelRuntime(provider_name="debug", model_name="debug-fallback")
    return ResolvedModelRuntime(provider_name="static", model_name="static")


def validate_model_runtime_available(settings: Settings) -> ResolvedModelRuntime:
    runtime = resolve_model_runtime(settings)
    if runtime.provider_name == "static":
        raise RuntimeError(NO_MODEL_PROVIDER_ERROR_MESSAGE)
    return runtime


def model_provider_name(settings: Settings) -> str:
    return resolve_model_runtime(settings).provider_name


def build_model_client(settings: Settings) -> ModelClient:
    runtime = resolve_model_runtime(settings)
    if runtime.api_key is not None and runtime.base_url is not None:
        return OpenAIModelClient(
            model_name=runtime.model_name,
            client=OpenAI(api_key=runtime.api_key, base_url=runtime.base_url),
        )
    if runtime.provider_name == "codex":
        return CodexModelClient(model_name=runtime.model_name)
    return StaticModelClient()
