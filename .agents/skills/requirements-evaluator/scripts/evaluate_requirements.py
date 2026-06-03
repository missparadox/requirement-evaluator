#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence


EVALUATED_REQUIREMENT_CATEGORY = "功能"
CATEGORY_FIELD_CANDIDATES = (
    "分类类型",
    "需求分类",
    "OR需求分类",
    "需求类型",
    "需求类别",
    "OR需求类型",
    "需求分类类型",
)

DEFAULT_DIMENSIONS = [
    {
        "key": "or_user_language",
        "name": "OR-用户语言描述",
        "weight": 12,
        "description": "需求描述是否采用用户语言，避免技术术语，让非技术人员也能理解",
    },
    {
        "key": "or_scenario",
        "name": "OR-应用场景",
        "weight": 12,
        "description": "是否清晰描述了用户需求的应用场景，包括使用环境和上下文",
    },
    {
        "key": "or_user_value",
        "name": "OR-用户价值",
        "weight": 10,
        "description": "是否讲清楚解决的用户问题和带来的用户价值",
    },
    {
        "key": "or_constraints",
        "name": "OR-约束和限制",
        "weight": 6,
        "description": "是否明确约束和限制（如部署方式、合规性、性能指标等）",
    },
    {
        "key": "dr_security",
        "name": "DR-安全分析",
        "weight": 5,
        "description": "是否进行安全分析，描述对应的安全红线需求",
    },
    {
        "key": "dr_technical",
        "name": "DR-技术描述",
        "weight": 10,
        "description": "是否使用技术语言进行设计需求描述，功能描述清晰全面，包含正常情况和异常处理",
    },
    {
        "key": "dr_testability",
        "name": "DR-可测试性",
        "weight": 10,
        "description": "是否定量描述，对照 DR 能直接写出测试用例",
    },
    {
        "key": "dr_ambiguity",
        "name": "DR-无歧义性",
        "weight": 8,
        "description": "参数规格是否清晰，无歧义",
    },
    {
        "key": "dr_exception",
        "name": "DR-异常描述",
        "weight": 7,
        "description": "是否明确异常路径、错误条件、非法输入处理、失败行为和边界场景",
    },
    {
        "key": "cross_scope",
        "name": "需求分解完整性",
        "weight": 7,
        "description": "是否覆盖 OR 的关键能力点，多个 DR 合起来是否形成完整分解，是否存在明显漏拆",
    },
    {
        "key": "cross_dependencies",
        "name": "需求分解边界清晰度",
        "weight": 6,
        "description": "各 DR 之间的职责边界是否清楚，是否存在交叉、重复拆解或责任不清",
    },
    {
        "key": "cross_traceability",
        "name": "需求映射一致性",
        "weight": 7,
        "description": "OR 与各 DR 是否语义一致、范围匹配、无明显偏题或冲突，且 DS/TDR/TDS 与该链路一致",
    },
]

CORE_FIELD_MAP = {
    "or_id": "OR需求编号",
    "or_name": "OR需求名称*",
    "or_desc": "OR需求描述*",
    "scenario": "应用场景",
    "customer_problem": "客户问题",
    "value_desc": "价值描述",
    "constraints": "约束与限制",
    "requirement_source": "需求来源",
    "region": "国家/区域",
    "dr_id": "DR需求编号",
    "dr_name": "DR需求名称*",
    "dr_desc": "DR需求描述*",
    "dr_integration": "集成方式",
    "dr_param": "参数规格",
    "dr_operation": "操作场景",
    "dr_test": "系统测试要点",
    "dr_security": "安全约束",
    "ds_id": "DS需求编号",
    "ds_name": "DS需求名称*",
    "ds_desc": "DS需求描述*",
    "spec_type": "规格分类",
    "subsystem": "所属子系统",
    "ds_dependencies": "假设和依赖信息",
    "ds_verify": "验证方法描述",
    "tdr_id": "TDR需求编号",
    "tdr_name": "TDR需求名称*",
    "tdr_desc": "TDR需求描述*",
    "tds_id": "TDS需求编号",
    "tds_name": "TDS需求名称*",
    "tds_desc": "TDS需求描述*",
}

OR_CORE_ALIASES = (
    "or_id",
    "or_name",
    "or_desc",
    "scenario",
    "customer_problem",
    "value_desc",
    "constraints",
    "requirement_source",
    "region",
    "requirement_category",
)

DR_CORE_ALIASES = (
    "dr_id",
    "dr_name",
    "dr_desc",
    "dr_integration",
    "dr_param",
    "dr_operation",
    "dr_test",
    "dr_security",
    "ds_id",
    "ds_name",
    "ds_desc",
    "spec_type",
    "subsystem",
    "ds_dependencies",
    "ds_verify",
    "tdr_id",
    "tdr_name",
    "tdr_desc",
    "tds_id",
    "tds_name",
    "tds_desc",
)

DIMENSION_FIELD_MAP = {
    "or_user_language": ["OR需求名称*", "OR需求描述*", "更多描述信息"],
    "or_scenario": ["应用场景", "操作场景", "OR需求描述*", "更多描述信息"],
    "or_user_value": ["客户问题", "价值描述", "需求来源", "OR需求描述*"],
    "or_constraints": ["约束与限制", "国家/区域", "安全约束", "集成方式", "更多描述信息"],
    "dr_security": ["安全约束", "DR需求描述*", "TDR需求描述*"],
    "dr_technical": ["DR需求描述*", "DS需求描述*", "TDR需求描述*", "TDS需求描述*", "集成方式", "参数规格", "规格分类", "所属子系统"],
    "dr_testability": ["系统测试要点", "验证方法描述", "参数规格", "DR需求描述*", "DS需求描述*"],
    "dr_ambiguity": ["参数规格", "DR需求描述*", "TDR需求描述*"],
    "dr_exception": ["DR需求描述*", "系统测试要点", "验证方法描述", "安全约束", "更多描述信息"],
    "cross_scope": ["OR需求描述*", "DR需求描述*", "DS需求描述*", "TDR需求描述*", "TDS需求描述*"],
    "cross_dependencies": ["假设和依赖信息", "所属子系统", "国家/区域", "需求来源", "集成方式", "约束与限制", "DS需求描述*", "TDS需求描述*"],
    "cross_traceability": ["OR需求编号", "DR需求编号", "DS需求编号", "TDR需求编号", "TDS需求编号", "ORURL", "DRURL", "DSURL", "TDRURL", "TDSURL"],
}


@dataclass
class RowRecord:
    index: int
    grouped: Dict[str, List[str]]

    def first(self, key: str, occurrence: int = 0) -> str:
        values = self.grouped.get(key, [])
        if occurrence < len(values):
            return clean_text(values[occurrence])
        return ""


@dataclass
class ReadResult:
    records: List[RowRecord]
    source_info: Dict[str, object]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def build_dimensions() -> List[Dict[str, object]]:
    return [dict(item) for item in DEFAULT_DIMENSIONS]


def missing_runtime_dependencies(path: Path) -> List[str]:
    suffix = path.suffix.lower()
    missing = []
    if suffix in {".xlsx", ".xlsm"} and importlib.util.find_spec("openpyxl") is None:
        missing.append("openpyxl")
    return missing


def dependency_install_hint(packages: Sequence[str]) -> str:
    joined = " ".join(packages)
    return f"python3 -m pip install {joined}"


def ensure_runtime_dependencies(path: Path) -> None:
    missing = missing_runtime_dependencies(path)
    if not missing:
        return
    package_list = ", ".join(missing)
    hint = dependency_install_hint(missing)
    raise SystemExit(f"缺少运行依赖: {package_list}。请先执行: {hint}")


def read_excel(path: Path) -> ReadResult:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise SystemExit("读取 Excel 需要安装 openpyxl") from exc
    workbook = load_workbook(path, read_only=False, data_only=True)
    sheet = workbook.active
    source_info = {
        "input_format": path.suffix.lower().lstrip("."),
        "sheet_name": sheet.title,
    }
    if sheet.max_row < 1:
        return ReadResult(records=[], source_info=source_info)
    merged_values = {}
    for merged_range in sheet.merged_cells.ranges:
        min_col, min_row, max_col, max_row = merged_range.bounds
        anchor_value = sheet.cell(min_row, min_col).value
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                merged_values[(row, col)] = anchor_value

    def cell_value(row: int, col: int) -> str:
        value = sheet.cell(row, col).value
        if value is None and (row, col) in merged_values:
            value = merged_values[(row, col)]
        return "" if value is None else str(value)

    header = [cell_value(1, col) for col in range(1, sheet.max_column + 1)]
    while header and not clean_text(header[-1]):
        header.pop()
    if not header:
        return ReadResult(records=[], source_info=source_info)

    records = []
    for row_index in range(2, sheet.max_row + 1):
        grouped: Dict[str, List[str]] = defaultdict(list)
        values = [cell_value(row_index, col) for col in range(1, len(header) + 1)]
        for name, value in zip(header, values):
            grouped[name].append(value)
        records.append(RowRecord(index=row_index - 1, grouped=dict(grouped)))
    return ReadResult(records=records, source_info=source_info)


def read_json(path: Path) -> ReadResult:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                data = value
                break
    if not isinstance(data, list):
        raise SystemExit("JSON 输入必须是对象数组，或包含数组字段的对象")
    records = []
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            continue
        grouped = {str(key): ["" if value is None else str(value)] for key, value in item.items()}
        records.append(RowRecord(index=idx, grouped=grouped))
    return ReadResult(
        records=records,
        source_info={
            "input_format": path.suffix.lower().lstrip("."),
        },
    )


def read_records(path: Path) -> ReadResult:
    ensure_runtime_dependencies(path)
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        return read_excel(path)
    if suffix == ".json":
        return read_json(path)
    raise SystemExit(f"不支持的输入格式: {suffix}")


def summarize_headers(records: Sequence[RowRecord]) -> List[str]:
    if not records:
        return []
    headers = []
    seen = set()
    for record in records:
        for key in record.grouped:
            if key not in seen:
                seen.add(key)
                headers.append(key)
    return headers


def extract_core_fields(record: RowRecord) -> Dict[str, str]:
    core = {}
    for alias, source in CORE_FIELD_MAP.items():
        core[alias] = record.first(source)
    core["requirement_category"] = requirement_category(record)["value"]
    return core


def select_core_fields(core_fields: Dict[str, str], aliases: Sequence[str]) -> Dict[str, str]:
    return {alias: core_fields.get(alias, "") for alias in aliases}


def filter_dimensions(dimensions: Sequence[Dict[str, object]], prefix: str) -> List[Dict[str, object]]:
    return [dimension for dimension in dimensions if str(dimension["key"]).startswith(prefix)]


def score_structure(dimensions: Sequence[Dict[str, object]]) -> Dict[str, int]:
    return {
        "or_total_weight": sum(int(d["weight"]) for d in dimensions if str(d["key"]).startswith("or_")),
        "dr_total_weight": sum(int(d["weight"]) for d in dimensions if str(d["key"]).startswith("dr_")),
        "cross_total_weight": sum(int(d["weight"]) for d in dimensions if str(d["key"]).startswith("cross_")),
    }


def merge_records(records: Sequence[RowRecord]) -> RowRecord:
    grouped: Dict[str, List[str]] = defaultdict(list)
    for record in records:
        for key, values in record.grouped.items():
            for value in values:
                text = clean_text(value)
                if not text:
                    continue
                if text not in grouped[key]:
                    grouped[key].append(text)
    return RowRecord(index=records[0].index if records else 0, grouped=dict(grouped))


def build_raw_fields(record: RowRecord) -> Dict[str, List[str]]:
    return {
        key: [clean_text(value) for value in values if clean_text(value)]
        for key, values in record.grouped.items()
        if any(clean_text(value) for value in values)
    }


def requirement_category(record: RowRecord) -> Dict[str, str]:
    for field in CATEGORY_FIELD_CANDIDATES:
        values = [clean_text(value) for value in record.grouped.get(field, []) if clean_text(value)]
        if values:
            return {"field": field, "value": values[0]}
    return {"field": "", "value": ""}


def category_display_name(category: str) -> str:
    return category or "未分类"


def is_evaluated_category(category: str) -> bool:
    return clean_text(category) == EVALUATED_REQUIREMENT_CATEGORY


def build_category_counts(or_groups: Sequence[Sequence[RowRecord]]) -> List[Dict[str, object]]:
    total = len(or_groups)
    counts: Dict[str, int] = {}
    fields: Dict[str, str] = {}

    for or_records in or_groups:
        merged_record = merge_records(or_records)
        category = requirement_category(merged_record)
        value = category_display_name(category["value"])
        counts[value] = counts.get(value, 0) + 1
        if category["field"] and value not in fields:
            fields[value] = category["field"]

    category_counts = []
    for value, count in counts.items():
        included = is_evaluated_category(value)
        percentage = round((count / total * 100), 2) if total else 0
        category_counts.append(
            {
                "category": value,
                "count": count,
                "percentage": percentage,
                "included_in_evaluation": included,
                "exclusion_reason": "" if included else f"分类类型不是{EVALUATED_REQUIREMENT_CATEGORY}",
                "source_field": fields.get(value, ""),
            }
        )
    return category_counts


def build_or_review_skeleton(score_weights: Dict[str, int], dr_items: Sequence[Dict[str, object]]) -> Dict[str, object]:
    return {
        "or_total_score": {
            "max_score": score_weights["or_total_weight"] + score_weights["dr_total_weight"] + score_weights["cross_total_weight"],
            "score": None,
            "review_conclusion": None,
        },
        "or_part": {
            "max_score": score_weights["or_total_weight"],
            "score": None,
            "dimension_scores": [],
        },
        "dr_parts": [
            {
                "dr_id": item["id"],
                "dr_name": item["name"],
                "max_score": score_weights["dr_total_weight"],
                "score": None,
                "dimension_scores": [],
            }
            for item in dr_items
        ],
        "dr_average": {
            "max_score": score_weights["dr_total_weight"],
            "score": None,
        },
        "decomposition_quality": {
            "max_score": score_weights["cross_total_weight"],
            "score": None,
            "dimension_scores": [],
        },
        "review_decision": {
            "blocking_issues": [],
            "triggered_red_line_rules": [],
        },
    }


def group_records_by_or(records: Sequence[RowRecord]) -> List[List[RowRecord]]:
    groups: List[List[RowRecord]] = []
    current: List[RowRecord] = []
    current_key = ""

    for record in records:
        core = extract_core_fields(record)
        or_key = core.get("or_id") or ""
        if current and or_key and or_key != current_key:
            groups.append(current)
            current = [record]
            current_key = or_key
            continue
        if current:
            current.append(record)
            if or_key:
                current_key = or_key
            continue
        current = [record]
        current_key = or_key or f"ROW-{record.index}"

    if current:
        groups.append(current)
    return groups


def group_records_by_dr(records: Sequence[RowRecord]) -> List[List[RowRecord]]:
    groups: List[List[RowRecord]] = []
    current: List[RowRecord] = []
    current_key = ""

    for record in records:
        core = extract_core_fields(record)
        dr_key = core.get("dr_id") or f"ROW-{record.index}"
        if current and dr_key != current_key:
            groups.append(current)
            current = [record]
            current_key = dr_key
            continue
        if current:
            current.append(record)
            continue
        current = [record]
        current_key = dr_key

    if current:
        groups.append(current)
    return groups


def build_dimension_view(record: RowRecord, dimensions: Sequence[Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    view = {}
    for dimension in dimensions:
        key = str(dimension["key"])
        mapped_fields = DIMENSION_FIELD_MAP.get(key, [])
        evidence_fields = {}
        missing_fields = []
        for field in mapped_fields:
            values = [clean_text(value) for value in record.grouped.get(field, []) if clean_text(value)]
            if values:
                evidence_fields[field] = values
            else:
                missing_fields.append(field)
        view[key] = {
            "name": dimension["name"],
            "mapped_fields": mapped_fields,
            "evidence_fields": evidence_fields,
            "missing_fields": missing_fields,
        }
    return view


def build_review_packet(
    input_path: Path,
    dimensions: List[Dict[str, object]],
    records: Sequence[RowRecord],
    source_info: Dict[str, object] | None = None,
) -> Dict[str, object]:
    or_dimensions = filter_dimensions(dimensions, "or_")
    dr_dimensions = filter_dimensions(dimensions, "dr_")
    cross_dimensions = filter_dimensions(dimensions, "cross_")

    score_weights = score_structure(dimensions)
    or_record_groups = group_records_by_or(records)
    all_category_counts = build_category_counts(or_record_groups)
    groups = []
    total_dr_count = 0
    for or_records in or_record_groups:
        merged_or_record = merge_records(or_records)
        raw_fields = build_raw_fields(merged_or_record)
        if not raw_fields:
            continue
        category = requirement_category(merged_or_record)
        if not is_evaluated_category(category["value"]):
            continue
        full_core_fields = extract_core_fields(merged_or_record)
        or_core_fields = select_core_fields(full_core_fields, OR_CORE_ALIASES)
        requirement_id = full_core_fields.get("or_id") or full_core_fields.get("dr_id") or full_core_fields.get("ds_id") or f"ROW-{or_records[0].index}"
        requirement_name = full_core_fields.get("or_name") or full_core_fields.get("dr_name") or requirement_id

        dr_items = []
        for dr_records in group_records_by_dr(or_records):
            merged_dr_record = merge_records(dr_records)
            full_dr_core_fields = extract_core_fields(merged_dr_record)
            dr_core_fields = select_core_fields(full_dr_core_fields, DR_CORE_ALIASES)
            dr_id = full_dr_core_fields.get("dr_id") or f"ROW-{dr_records[0].index}"
            dr_name = full_dr_core_fields.get("dr_name") or dr_id
            dr_raw_fields = build_raw_fields(merged_dr_record)
            if not dr_raw_fields:
                continue
            dr_items.append(
                {
                    "row_indices": [record.index for record in dr_records],
                    "id": dr_id,
                    "name": dr_name,
                    "core_fields": dr_core_fields,
                    "dimension_view": build_dimension_view(merged_dr_record, dr_dimensions),
                    "raw_fields": dr_raw_fields,
                }
            )
        total_dr_count += len(dr_items)

        groups.append(
            {
                "row_indices": [record.index for record in or_records],
                "id": requirement_id,
                "name": requirement_name,
                "category": category_display_name(category["value"]),
                "category_field": category["field"],
                "or_core_fields": or_core_fields,
                "or_dimension_view": build_dimension_view(merged_or_record, or_dimensions),
                "dr_items": dr_items,
                "dr_count": len(dr_items),
                "cross_dimension_view": build_dimension_view(merged_or_record, cross_dimensions),
                "review_skeleton": build_or_review_skeleton(score_weights, dr_items),
                "raw_fields": raw_fields,
            }
        )

    return {
        "input_path": str(input_path),
        "source_info": dict(source_info or {}),
        "score_structure": score_weights,
        "evaluation_filter": {
            "category_field_candidates": list(CATEGORY_FIELD_CANDIDATES),
            "included_category": EVALUATED_REQUIREMENT_CATEGORY,
            "rule": f"only OR units whose requirement category is exactly `{EVALUATED_REQUIREMENT_CATEGORY}` are included in evaluation",
        },
        "all_category_counts": all_category_counts,
        "excluded_or_count": sum(
            int(item["count"]) for item in all_category_counts if not bool(item["included_in_evaluation"])
        ),
        "item_count": len(groups),
        "or_count": len(groups),
        "dr_count": total_dr_count,
        "dimension_count": len(dimensions),
        "dimensions": dimensions,
        "header_summary": summarize_headers(records),
        "groups": groups,
    }


def render_review_packet_markdown(packet: Dict[str, object]) -> str:
    lines = []
    lines.append("# 需求评审任务包")
    lines.append("")
    lines.append("本文件不是评分结果，而是提供给大模型使用的评审输入材料。模型应根据 skill 与 rubric 自主评分并输出正式中文报告。")
    lines.append("")
    lines.append("## 数据概览")
    lines.append("")
    lines.append(f"- 输入文件: `{packet['input_path']}`")
    for key, value in packet.get("source_info", {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.append(f"- OR条目数: {packet['or_count']}")
    lines.append(f"- DR条目数: {packet['dr_count']}")
    lines.append(f"- 排除OR条目数: {packet.get('excluded_or_count', 0)}")
    lines.append(f"- 维度数: {packet['dimension_count']}")
    evaluation_filter = packet.get("evaluation_filter", {})
    if evaluation_filter:
        lines.append(f"- 评估分类过滤: `{evaluation_filter.get('included_category', '')}`")
    lines.append("")
    if packet.get("all_category_counts"):
        lines.append("## OR需求分类统计")
        lines.append("")
        lines.append("| 需求分类 | OR条目数 | 占比 | 是否参与评审 | 排除原因 | 来源字段 |")
        lines.append("| --- | ---: | ---: | --- | --- | --- |")
        for item in packet["all_category_counts"]:
            included = "是" if item.get("included_in_evaluation") else "否"
            reason = item.get("exclusion_reason") or ""
            source_field = item.get("source_field") or ""
            lines.append(
                f"| {item.get('category', '')} | {item.get('count', 0)} | {item.get('percentage', 0)}% | {included} | {reason} | {source_field} |"
            )
        lines.append("")
    lines.append("## 评分结构")
    lines.append("")
    lines.append(f"- OR部分: {packet['score_structure']['or_total_weight']}")
    lines.append(f"- DR部分: {packet['score_structure']['dr_total_weight']}，每个 OR 下的多个 DR 分别评分后取平均")
    lines.append(f"- 需求分解与追踪质量部分: {packet['score_structure']['cross_total_weight']}，每个 OR 只评一次")
    lines.append("")
    lines.append("## 表头摘要")
    lines.append("")
    for header in packet["header_summary"]:
        lines.append(f"- {header}")
    lines.append("")
    lines.append("## 评审维度")
    lines.append("")
    for item in packet["dimensions"]:
        desc = item.get("description", "")
        weight = item.get("weight", "")
        lines.append(f"- {item['name']} ({weight}): {desc}")
    lines.append("")
    lines.append("## OR评审单元")
    lines.append("")
    for item in packet["groups"]:
        lines.append(f"### OR {item['id']} {item['name']}")
        lines.append("")
        lines.append(f"- 覆盖行: {', '.join(str(idx) for idx in item['row_indices'])}")
        lines.append(f"- 分类类型: {item.get('category', '')}")
        if item.get("category_field"):
            lines.append(f"- 分类来源字段: {item.get('category_field')}")
        lines.append(f"- DR数量: {item['dr_count']}")
        lines.append("")
        lines.append("OR核心字段：")
        for key, value in item["or_core_fields"].items():
            if value:
                lines.append(f"- {key}: {value}")
        lines.append("")
        lines.append("OR维度视图：")
        for key, dimension in item.get("or_dimension_view", {}).items():
            lines.append(f"- {key} / {dimension['name']}")
            if dimension["evidence_fields"]:
                for field, values in dimension["evidence_fields"].items():
                    lines.append(f"  - evidence {field}: {' | '.join(values)}")
            if dimension["missing_fields"]:
                lines.append(f"  - missing: {', '.join(dimension['missing_fields'])}")
        lines.append("")
        lines.append("DR评审单元：")
        for dr_item in item["dr_items"]:
            lines.append(f"- DR {dr_item['id']} {dr_item['name']}")
            lines.append(f"  - row_indices: {', '.join(str(idx) for idx in dr_item['row_indices'])}")
            for key, value in dr_item["core_fields"].items():
                if value and key.startswith(("dr_", "ds_", "tdr_", "tds_")):
                    lines.append(f"  - {key}: {value}")
            for key, dimension in dr_item.get("dimension_view", {}).items():
                lines.append(f"  - {key} / {dimension['name']}")
                if dimension["evidence_fields"]:
                    for field, values in dimension["evidence_fields"].items():
                        lines.append(f"    - evidence {field}: {' | '.join(values)}")
                if dimension["missing_fields"]:
                    lines.append(f"    - missing: {', '.join(dimension['missing_fields'])}")
        lines.append("")
        lines.append("需求分解与追踪维度视图：")
        for key, dimension in item.get("cross_dimension_view", {}).items():
            lines.append(f"- {key} / {dimension['name']}")
            if dimension["evidence_fields"]:
                for field, values in dimension["evidence_fields"].items():
                    lines.append(f"  - evidence {field}: {' | '.join(values)}")
            if dimension["missing_fields"]:
                lines.append(f"  - missing: {', '.join(dimension['missing_fields'])}")
        lines.append("")
        lines.append("评分骨架：")
        lines.append(f"- OR总分槽位: {item['review_skeleton']['or_total_score']['max_score']}")
        lines.append(f"- OR部分槽位: {item['review_skeleton']['or_part']['max_score']}")
        lines.append(f"- DR平均分槽位: {item['review_skeleton']['dr_average']['max_score']}")
        lines.append(f"- 需求分解与追踪质量槽位: {item['review_skeleton']['decomposition_quality']['max_score']}")
        lines.append(f"- DR评分槽位数: {len(item['review_skeleton']['dr_parts'])}")
        lines.append(f"- 评审决策槽位: review conclusion, blocking issues, red-line rules")
        lines.append("")
        lines.append("聚合原始字段：")
        for key, values in item["raw_fields"].items():
            lines.append(f"- {key}: {' | '.join(values)}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build a review packet for LLM-based requirement evaluation.")
    parser.add_argument("--input", required=True, help="Path to the input Excel/JSON file.")
    parser.add_argument("--output", required=True, help="Path to write the review packet.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output packet format.")
    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    dimensions = build_dimensions()
    read_result = read_records(input_path)
    packet = build_review_packet(
        input_path,
        dimensions,
        read_result.records,
        source_info=read_result.source_info,
    )

    if args.format == "json":
        output_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        output_path.write_text(render_review_packet_markdown(packet), encoding="utf-8")

    print(f"已生成评审任务包: {output_path}")
    print(f"条目数: {packet['item_count']}")


if __name__ == "__main__":
    main()
