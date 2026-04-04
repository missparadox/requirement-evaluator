from app.clients.model_client import StaticModelClient


def test_static_model_client_returns_markdown() -> None:
    client = StaticModelClient()
    report = client.generate_report(skill_text="skill", template_text="template", packet_text="packet")
    assert report.startswith("#")
