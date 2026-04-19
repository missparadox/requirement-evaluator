#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = SKILL_ROOT.parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.clients.model_client import StaticModelClient, build_model_client  # noqa: E402
from app.core.config import get_settings  # noqa: E402

from aggregate_reviews import aggregate_reviews  # noqa: E402
from evaluate_requirements import (  # noqa: E402
    build_dimensions,
    build_packet_manifest,
    build_review_packet,
    build_shard_packets,
    read_records,
)


SHARD_REVIEW_INSTRUCTIONS = (
    "You are a requirements evaluation assistant. "
    "Evaluate only the OR units in the provided shard packet. "
    "Return JSON only. Do not include markdown fences or extra commentary."
)

FINAL_REPORT_INSTRUCTIONS = (
    "You are a requirements evaluation assistant. "
    "Write the final Chinese Markdown report using the provided aggregate input, "
    "skill rubric, scoring anchors, and report template. "
    "The final report must cover every OR through the full score table and selected detailed cards."
)


def extract_json_object(text: str) -> Dict[str, object]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.startswith("```")]
        stripped = "\n".join(lines).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise
        return json.loads(stripped[start : end + 1])


def build_shard_prompt(
    *,
    skill_text: str,
    anchors_text: str,
    shard_packet: Dict[str, object],
) -> str:
    schema_hint = {
        "shard_id": shard_packet["shard_id"],
        "sheet_name": shard_packet.get("source_info", {}).get("sheet_name"),
        "cross_shard_notes": {"weak_dimensions": ["OR-用户价值", "DR-可测试性"]},
        "or_results": [
            {
                "or_id": "OR编号",
                "or_name": "OR名称",
                "or_total_score": 76,
                "grade": "良好",
                "or_part_score": 24,
                "dr_scores": [{"dr_id": "DR编号", "dr_name": "DR名称", "score": 34}],
                "dr_average_score": 34,
                "traceability_score": 18,
                "review_conclusion": "正式评审结论",
                "design_review_readiness": "可进入",
                "development_readiness": "有条件进入",
                "test_design_readiness": "有条件进入",
                "blocking_issues": ["如无可返回空数组"],
                "triggered_red_line_rules": ["R1"],
                "evidence_bullets": ["关键证据1", "关键证据2"],
                "red_flags": ["红旗问题"],
                "missing_items": ["缺失项"],
                "revision_actions": ["修改建议1", "修改建议2"],
            }
        ],
    }
    return (
        "[TASK]\nPARTIAL_REVIEW\n\n"
        "[SKILL]\n"
        f"{skill_text}\n\n"
        "[SCORING_ANCHORS]\n"
        f"{anchors_text}\n\n"
        "[OUTPUT_SCHEMA_EXAMPLE]\n"
        f"{json.dumps(schema_hint, ensure_ascii=False, indent=2)}\n\n"
        "[SHARD_PACKET_JSON]\n"
        f"{json.dumps(shard_packet, ensure_ascii=False, indent=2)}\n"
    )


def build_final_report_prompt(
    *,
    skill_text: str,
    anchors_text: str,
    template_text: str,
    aggregate_result: Dict[str, object],
) -> str:
    return (
        "[TASK]\nFINAL_REPORT\n\n"
        "[SKILL]\n"
        f"{skill_text}\n\n"
        "[SCORING_ANCHORS]\n"
        f"{anchors_text}\n\n"
        "[REPORT_TEMPLATE]\n"
        f"{template_text}\n\n"
        "[AGGREGATE_RESULT_JSON]\n"
        f"{json.dumps(aggregate_result, ensure_ascii=False, indent=2)}\n"
    )


def validate_partial_result(shard_packet: Dict[str, object], partial: Dict[str, object]) -> None:
    expected_or_ids = [group["id"] for group in shard_packet["groups"]]
    shard_id = shard_packet["shard_id"]
    if partial.get("shard_id") != shard_id:
        raise RuntimeError(
            f"Partial result shard_id mismatch: expected {shard_id}, got {partial.get('shard_id')}"
        )
    actual_or_ids = [item["or_id"] for item in partial.get("or_results", [])]
    missing = [or_id for or_id in expected_or_ids if or_id not in actual_or_ids]
    extra = [or_id for or_id in actual_or_ids if or_id not in expected_or_ids]
    if missing or extra:
        raise RuntimeError(
            f"Partial result OR coverage mismatch for {shard_id}: missing={missing}, extra={extra}"
        )


def run_pipeline(
    *,
    input_path: Path,
    report_output_path: Path,
    work_dir: Path,
    shard_size: int,
    max_chars_per_shard: int | None,
    provider: str,
) -> Dict[str, object]:
    settings = get_settings()
    model_client = StaticModelClient() if provider == "static" else build_model_client(settings)

    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    anchors_text = (SKILL_ROOT / "references" / "scoring-anchors.md").read_text(encoding="utf-8")
    template_text = (SKILL_ROOT / "references" / "report-template.md").read_text(encoding="utf-8")

    packets_dir = work_dir / "packets"
    partials_dir = work_dir / "partials"
    packets_dir.mkdir(parents=True, exist_ok=True)
    partials_dir.mkdir(parents=True, exist_ok=True)

    dimensions = build_dimensions()
    read_result = read_records(input_path)
    packet = build_review_packet(
        input_path=input_path,
        dimensions=dimensions,
        records=read_result.records,
        source_info=read_result.source_info,
    )
    manifest = build_packet_manifest(
        packet,
        shard_size=shard_size,
        max_chars_per_shard=max_chars_per_shard,
    )
    manifest_path = packets_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    shard_packets = build_shard_packets(packet, manifest)
    partial_results: List[Dict[str, object]] = []
    for shard_packet in shard_packets:
        shard_path = packets_dir / f"{shard_packet['shard_id']}.json"
        shard_path.write_text(json.dumps(shard_packet, ensure_ascii=False, indent=2), encoding="utf-8")
        response_text = model_client.generate_text(
            instructions=SHARD_REVIEW_INSTRUCTIONS,
            input_text=build_shard_prompt(
                skill_text=skill_text,
                anchors_text=anchors_text,
                shard_packet=shard_packet,
            ),
        )
        partial = extract_json_object(response_text)
        validate_partial_result(shard_packet, partial)
        partial_path = partials_dir / f"partial-review-{shard_packet['shard_id']}.json"
        partial_path.write_text(json.dumps(partial, ensure_ascii=False, indent=2), encoding="utf-8")
        partial_results.append(partial)

    aggregate_result = aggregate_reviews(manifest, partial_results)
    aggregate_path = work_dir / "aggregate.json"
    aggregate_path.write_text(json.dumps(aggregate_result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not aggregate_result["coverage_ok"]:
        raise RuntimeError(
            f"Aggregate coverage check failed: missing_shards={aggregate_result['missing_shards']} "
            f"missing_or_ids={aggregate_result['missing_or_ids']}"
        )

    final_report = model_client.generate_text(
        instructions=FINAL_REPORT_INSTRUCTIONS,
        input_text=build_final_report_prompt(
            skill_text=skill_text,
            anchors_text=anchors_text,
            template_text=template_text,
            aggregate_result=aggregate_result,
        ),
    )
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text(final_report, encoding="utf-8")

    return {
        "manifest_path": str(manifest_path),
        "partials_dir": str(partials_dir),
        "aggregate_path": str(aggregate_path),
        "report_path": str(report_output_path),
        "shard_count": manifest["shard_count"],
        "or_count": manifest["or_count"],
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the full sharded requirements evaluation pipeline.")
    parser.add_argument("--input", required=True, help="Path to the input Excel/JSON file.")
    parser.add_argument(
        "--report-output",
        default="",
        help="Path to write the final report. Defaults to reports/<input-stem>.md under repo root.",
    )
    parser.add_argument(
        "--work-dir",
        default="",
        help="Working directory for manifest, shard packets, partial reviews, and aggregate output.",
    )
    parser.add_argument("--shard-size", type=int, default=8, help="Maximum OR units per shard.")
    parser.add_argument(
        "--provider",
        choices=("auto", "static"),
        default="auto",
        help="Model provider mode. Use static for local dry-runs without a remote model.",
    )
    parser.add_argument(
        "--max-chars-per-shard",
        type=int,
        default=120000,
        help="Approximate character cap per shard. Set 0 to disable.",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    report_output_path = (
        Path(args.report_output).expanduser().resolve()
        if args.report_output
        else (REPO_ROOT / "reports" / f"{input_path.stem}.md")
    )
    work_dir = (
        Path(args.work_dir).expanduser().resolve()
        if args.work_dir
        else (REPO_ROOT / "tmp" / f"{input_path.stem}-eval")
    )
    result = run_pipeline(
        input_path=input_path,
        report_output_path=report_output_path,
        work_dir=work_dir,
        shard_size=args.shard_size,
        max_chars_per_shard=args.max_chars_per_shard if args.max_chars_per_shard > 0 else None,
        provider=args.provider,
    )
    print(f"已完成自动评估: {result['report_path']}")
    print(f"分片数: {result['shard_count']}")
    print(f"OR条目数: {result['or_count']}")


if __name__ == "__main__":
    main()
