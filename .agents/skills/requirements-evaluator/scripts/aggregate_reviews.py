#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def grade_for_score(score: float) -> str:
    if score >= 85:
        return "优秀"
    if score >= 70:
        return "良好"
    if score >= 50:
        return "中等"
    if score >= 35:
        return "较弱"
    return "较差"


def find_partial_files(input_dir: Path) -> List[Path]:
    return sorted(input_dir.glob("partial-review-*.json"))


def normalize_or_result(item: Dict[str, object], *, shard_id: str) -> Dict[str, object]:
    score = float(item["or_total_score"])
    return {
        "shard_id": shard_id,
        "or_id": item["or_id"],
        "or_name": item["or_name"],
        "or_total_score": score,
        "grade": item.get("grade") or grade_for_score(score),
        "or_part_score": item.get("or_part_score"),
        "dr_average_score": item.get("dr_average_score"),
        "traceability_score": item.get("traceability_score"),
        "review_conclusion": item.get("review_conclusion"),
        "design_review_readiness": item.get("design_review_readiness"),
        "development_readiness": item.get("development_readiness"),
        "test_design_readiness": item.get("test_design_readiness"),
        "blocking_issues": item.get("blocking_issues", []),
        "triggered_red_line_rules": item.get("triggered_red_line_rules", []),
        "dr_scores": item.get("dr_scores", []),
        "evidence_bullets": item.get("evidence_bullets", []),
        "red_flags": item.get("red_flags", []),
        "missing_items": item.get("missing_items", []),
        "revision_actions": item.get("revision_actions", []),
    }


def aggregate_reviews(manifest: Dict[str, object], partials: Sequence[Dict[str, object]]) -> Dict[str, object]:
    shard_lookup = {item["shard_id"]: item for item in manifest["shards"]}
    expected_or_ids = [or_id for shard in manifest["shards"] for or_id in shard["or_ids"]]
    all_results = []
    recurring_weak_dimensions = Counter()
    seen_or_ids = set()
    seen_shard_ids = set()

    for partial in partials:
        shard_id = partial["shard_id"]
        seen_shard_ids.add(shard_id)
        if shard_id not in shard_lookup:
            raise SystemExit(f"Unknown shard_id in partial review: {shard_id}")
        for dimension in partial.get("cross_shard_notes", {}).get("weak_dimensions", []):
            recurring_weak_dimensions[str(dimension)] += 1
        for item in partial.get("or_results", []):
            normalized = normalize_or_result(item, shard_id=shard_id)
            or_id = normalized["or_id"]
            if or_id in seen_or_ids:
                raise SystemExit(f"Duplicate OR result found during aggregation: {or_id}")
            seen_or_ids.add(or_id)
            all_results.append(normalized)

    missing_shards = [shard_id for shard_id in shard_lookup if shard_id not in seen_shard_ids]
    missing_or_ids = [or_id for or_id in expected_or_ids if or_id not in seen_or_ids]
    unexpected_or_ids = [item["or_id"] for item in all_results if item["or_id"] not in expected_or_ids]
    if unexpected_or_ids:
        raise SystemExit(f"Unexpected OR ids found during aggregation: {', '.join(unexpected_or_ids)}")

    ordered_results = sorted(
        all_results,
        key=lambda item: expected_or_ids.index(item["or_id"]),
    )
    scores = [float(item["or_total_score"]) for item in ordered_results]
    distribution = Counter(item["grade"] for item in ordered_results)

    top_strengths = sorted(ordered_results, key=lambda item: (-float(item["or_total_score"]), item["or_id"]))[:5]
    top_risks = sorted(ordered_results, key=lambda item: (float(item["or_total_score"]), item["or_id"]))[:5]

    return {
        "input_path": manifest["input_path"],
        "source_info": manifest.get("source_info", {}),
        "or_count_expected": manifest["or_count"],
        "dr_count_expected": manifest["dr_count"],
        "shard_count_expected": manifest["shard_count"],
        "partial_count": len(partials),
        "missing_shards": missing_shards,
        "missing_or_ids": missing_or_ids,
        "coverage_ok": not missing_shards and not missing_or_ids,
        "overall_average_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "grade_distribution": {
            "优秀": distribution.get("优秀", 0),
            "良好": distribution.get("良好", 0),
            "中等": distribution.get("中等", 0),
            "较弱": distribution.get("较弱", 0),
            "较差": distribution.get("较差", 0),
        },
        "recurring_weak_dimensions": [item for item, _ in recurring_weak_dimensions.most_common()],
        "top_strengths": top_strengths,
        "top_risks": top_risks,
        "or_results": ordered_results,
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Aggregate shard review results into one structured summary.")
    parser.add_argument("--manifest", required=True, help="Path to the packet manifest JSON.")
    parser.add_argument(
        "--partials-dir",
        required=True,
        help="Directory containing partial-review-*.json files.",
    )
    parser.add_argument("--output", required=True, help="Path to write the aggregated JSON.")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest).expanduser().resolve()
    partials_dir = Path(args.partials_dir).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    manifest = load_json(manifest_path)
    partial_files = find_partial_files(partials_dir)
    partials = [load_json(path) for path in partial_files]
    aggregated = aggregate_reviews(manifest, partials)
    output_path.write_text(json.dumps(aggregated, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已生成汇总结果: {output_path}")
    print(f"partial文件数: {len(partial_files)}")
    print(f"OR覆盖完整: {aggregated['coverage_ok']}")


if __name__ == "__main__":
    main()
