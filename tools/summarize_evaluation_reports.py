#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def discover_summary_paths(inputs: Sequence[str]) -> List[Path]:
    discovered: List[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"输入路径不存在: {path}")
        if path.is_dir():
            discovered.extend(sorted(path.rglob("*.summary.json")))
            continue
        if path.suffix == ".md":
            candidate = path.with_suffix(".summary.json")
            if not candidate.exists():
                raise SystemExit(f"未找到对应摘要JSON: {candidate}")
            discovered.append(candidate)
            continue
        if path.name.endswith(".summary.json"):
            discovered.append(path)
            continue
        raise SystemExit(f"不支持的输入文件类型: {path}")

    unique_paths: List[Path] = []
    seen = set()
    for path in discovered:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    if not unique_paths:
        raise SystemExit("未找到任何 summary JSON 文件")
    return unique_paths


def load_projects(summary_paths: Sequence[Path]) -> List[Dict[str, object]]:
    projects = []
    for path in summary_paths:
        payload = read_json(path)
        if "dimension_summary" not in payload or "average_score" not in payload:
            raise SystemExit(f"摘要JSON缺少必要字段: {path}")
        payload["summary_path"] = str(path)
        projects.append(payload)
    return projects


def project_dimension_index(project: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    return {
        str(item["key"]): item
        for item in project.get("dimension_summary", [])
        if isinstance(item, dict) and item.get("key")
    }


def build_dimension_baseline(projects: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    if not projects:
        return []
    dimension_keys = [
        str(item["key"])
        for item in projects[0].get("dimension_summary", [])
        if isinstance(item, dict) and item.get("key")
    ]
    baselines = []
    for key in dimension_keys:
        values = []
        name = key
        for project in projects:
            item = project_dimension_index(project).get(key)
            if not item:
                continue
            name = str(item.get("name", key))
            values.append(float(item.get("normalized_average_score", 0)))
        average_value = round(sum(values) / len(values), 2) if values else 0.0
        baselines.append(
            {
                "key": key,
                "name": name,
                "average_normalized_score": average_value,
            }
        )
    return baselines


def rank_projects(projects: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    return sorted(projects, key=lambda item: float(item.get("average_score", 0)), reverse=True)


def summarize_project_dimensions(
    project: Dict[str, object],
    baselines: Sequence[Dict[str, object]],
) -> Dict[str, List[Dict[str, object]]]:
    dimension_map = project_dimension_index(project)
    comparisons = []
    for baseline in baselines:
        key = str(baseline["key"])
        item = dimension_map.get(key)
        if not item:
            continue
        score = float(item.get("normalized_average_score", 0))
        gap = round(score - float(baseline["average_normalized_score"]), 2)
        comparisons.append(
            {
                "key": key,
                "name": str(item.get("name", key)),
                "normalized_average_score": score,
                "gap_to_portfolio": gap,
            }
        )
    return {
        "strengths": sorted(comparisons, key=lambda item: item["gap_to_portfolio"], reverse=True)[:3],
        "weaknesses": sorted(comparisons, key=lambda item: item["gap_to_portfolio"])[:3],
    }


def format_dimension_items(items: Sequence[Dict[str, object]]) -> str:
    if not items:
        return "无"
    return "; ".join(
        f"{item['name']}({float(item['normalized_average_score']):.2f}, 相对项目集 {float(item['gap_to_portfolio']):+.2f})"
        for item in items
    )


def format_top_counts(items: Sequence[Sequence[object]]) -> str:
    if not items:
        return "无"
    return "; ".join(f"{name}({count})" for name, count in items[:3])


def render_markdown_summary(projects: Sequence[Dict[str, object]]) -> str:
    ranked = rank_projects(projects)
    baselines = build_dimension_baseline(ranked)
    portfolio_average = round(
        sum(float(project.get("average_score", 0)) for project in ranked) / len(ranked),
        2,
    )

    lines = [
        "# 需求评估项目对比报告",
        "",
        "## 1. 总览",
        "",
        f"- 项目数: {len(ranked)}",
        f"- 项目集平均分: {portfolio_average:.2f}",
        f"- 对比口径: 基于单项目 summary JSON 中的 {len(baselines)} 维度标准化均分进行横向比较。",
        "",
        "## 2. 项目总分对比",
        "",
        "| 排名 | 项目 | 平均分 | 成功OR | 未评估OR | excellent | good | fair | poor | 相对项目集均值 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, project in enumerate(ranked, start=1):
        dist = project.get("grade_distribution", {})
        delta = round(float(project.get("average_score", 0)) - portfolio_average, 2)
        lines.append(
            f"| {index} | {markdown_cell(project.get('project_name', ''))} | {float(project.get('average_score', 0)):.2f} | "
            f"{project.get('scored_or_count', 0)} | {project.get('unscored_or_count', 0)} | "
            f"{dist.get('excellent', 0)} | {dist.get('good', 0)} | {dist.get('fair', 0)} | {dist.get('poor', 0)} | {delta:+.2f} |"
        )

    lines.extend(
        [
            "",
            "## 3. 维度基准",
            "",
            "| 维度 | 项目集标准化均分 | 最优项目 | 最优值 | 最弱项目 | 最弱值 |",
            "| --- | ---: | --- | ---: | --- | ---: |",
        ]
    )
    for baseline in baselines:
        key = str(baseline["key"])
        ranked_by_dimension = sorted(
            ranked,
            key=lambda project: float(project_dimension_index(project)[key]["normalized_average_score"]),
            reverse=True,
        )
        best = ranked_by_dimension[0]
        worst = ranked_by_dimension[-1]
        best_value = float(project_dimension_index(best)[key]["normalized_average_score"])
        worst_value = float(project_dimension_index(worst)[key]["normalized_average_score"])
        lines.append(
            f"| {markdown_cell(baseline['name'])} | {float(baseline['average_normalized_score']):.2f} | "
            f"{markdown_cell(best.get('project_name', ''))} | {best_value:.2f} | "
            f"{markdown_cell(worst.get('project_name', ''))} | {worst_value:.2f} |"
        )

    lines.extend(["", "## 4. 项目画像", ""])
    for project in ranked:
        dimension_view = summarize_project_dimensions(project, baselines)
        lines.extend(
            [
                f"### {project.get('project_name', '')}",
                "",
                f"- 平均分: {float(project.get('average_score', 0)):.2f}",
                f"- 相对项目集均值: {float(project.get('average_score', 0)) - portfolio_average:+.2f}",
                f"- 优势维度: {format_dimension_items(dimension_view['strengths'])}",
                f"- 薄弱维度: {format_dimension_items(dimension_view['weaknesses'])}",
                f"- 高频缺失项: {format_top_counts(project.get('missing_counts', []))}",
                f"- 高频修改建议: {format_top_counts(project.get('revision_counts', []))}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def build_json_summary(projects: Sequence[Dict[str, object]]) -> Dict[str, object]:
    ranked = rank_projects(projects)
    baselines = build_dimension_baseline(ranked)
    enriched_projects = []
    for project in ranked:
        enriched = dict(project)
        enriched["comparison_view"] = summarize_project_dimensions(project, baselines)
        enriched_projects.append(enriched)
    return {
        "project_count": len(ranked),
        "portfolio_average_score": round(
            sum(float(project.get("average_score", 0)) for project in ranked) / len(ranked),
            2,
        ) if ranked else 0.0,
        "dimension_baseline": baselines,
        "projects": enriched_projects,
    }


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Summarize multiple requirement evaluation summary JSON files.")
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Summary JSON file, report markdown file, or directory containing *.summary.json files. Repeat for multiple inputs.",
    )
    parser.add_argument("--output", required=True, help="Output markdown summary path.")
    parser.add_argument("--json-output", help="Optional JSON summary path.")
    args = parser.parse_args(argv)

    summary_paths = discover_summary_paths(args.input)
    projects = load_projects(summary_paths)
    markdown = render_markdown_summary(projects)

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"已生成项目对比报告: {output_path}")
    print(f"输入摘要数: {len(projects)}")

    if args.json_output:
        json_path = Path(args.json_output).expanduser().resolve()
        write_json(json_path, build_json_summary(projects))
        print(f"已生成项目对比JSON: {json_path}")


if __name__ == "__main__":
    main()
