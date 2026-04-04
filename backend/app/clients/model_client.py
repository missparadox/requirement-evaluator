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
        prompt = (
            "Use the requirement evaluation rubric and template below.\n\n"
            f"[SKILL]\n{skill_text}\n\n"
            f"[TEMPLATE]\n{template_text}\n\n"
            f"[PACKET]\n{packet_text}\n"
        )
        response = self.client.responses.create(
            model=self.model_name,
            input=prompt,
        )
        return response.output_text


def build_model_client(model_name: str) -> ModelClient:
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIModelClient(model_name=model_name, client=OpenAI())
    return StaticModelClient()
