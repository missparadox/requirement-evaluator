import os
from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI


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


def model_provider_name() -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "static"


def build_model_client(model_name: str) -> ModelClient:
    if model_provider_name() == "openai":
        return OpenAIModelClient(model_name=model_name, client=OpenAI())
    return StaticModelClient()
