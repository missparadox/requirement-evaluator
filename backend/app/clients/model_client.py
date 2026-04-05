from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI

from app.core.config import Settings


class ModelClient(Protocol):
    def generate_report(self, *, skill_text: str, template_text: str, packet_text: str) -> str: ...


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
            instructions=(
                "You are a requirements evaluation assistant. "
                "Follow the rubric and produce the final answer in Chinese Markdown using the template."
            ),
            input=(
                "[SKILL]\n"
                f"{skill_text}\n\n"
                "[TEMPLATE]\n"
                f"{template_text}\n\n"
                "[PACKET]\n"
                f"{packet_text}\n"
            ),
        )
        if not response.output_text:
            raise RuntimeError("OpenAI response did not contain output_text.")
        return response.output_text


@dataclass(frozen=True)
class ResolvedModelRuntime:
    provider_name: str
    model_name: str
    api_key: str | None = None
    base_url: str | None = None


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
    if settings.debug_fallback_enabled:
        return ResolvedModelRuntime(provider_name="debug", model_name="debug-fallback")
    return ResolvedModelRuntime(provider_name="static", model_name="static")


def model_provider_name(settings: Settings) -> str:
    return resolve_model_runtime(settings).provider_name


def build_model_client(settings: Settings) -> ModelClient:
    runtime = resolve_model_runtime(settings)
    if runtime.api_key is not None and runtime.base_url is not None:
        return OpenAIModelClient(
            model_name=runtime.model_name,
            client=OpenAI(api_key=runtime.api_key, base_url=runtime.base_url),
        )
    return StaticModelClient()
