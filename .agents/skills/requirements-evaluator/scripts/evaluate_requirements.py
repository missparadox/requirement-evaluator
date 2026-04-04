#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence


DEFAULT_DIMENSIONS = [
    {
        "key": "or_user_language",
        "name": "OR-用户语言描述",
        "weight": 10,
        "description": "需求描述是否采用用户语言，避免技术术语，让非技术人员也能理解",
    },
    {
        "key": "or_scenario",
        "name": "OR-应用场景",
        "weight": 10,
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
        "weight": 5,
        "description": "是否明确约束和限制（如部署方式、合规性、性能指标等）",
    },
    {
        "key": "dr_security",
        "name": "DR-安全分析",
        "weight": 8,
        "description": "是否进行安全分析，描述对应的安全红线需求",
    },
    {
        "key": "dr_technical",
        "name": "DR-技术描述",
        "weight": 8,
        "description": "是否使用技术语言进行设计需求描述，功能描述清晰全面，包含正常情况和异常处理",
    },
    {
        "key": "dr_testability",
        "name": "DR-可测试性",
        "weight": 8,
        "description": "是否定量描述，对照 DR 能直接写出测试用例",
    },
    {
        "key": "dr_ambiguity",
        "name": "DR-无歧义性",
        "weight": 4,
        "description": "参数规格是否清晰，无歧义",
    },
    {
        "key": "dr_performance",
        "name": "DR-性能需求",
        "weight": 4,
        "description": "是否包含性能需求（如响应时间、吞吐量等）",
    },
    {
        "key": "dr_hardware",
        "name": "DR-硬件分析",
        "weight": 3,
        "description": "是否分析所需要的硬件性能（如 CPU、内存、存储等）",
    },
    {
        "key": "cross_scope",
        "name": "跨层-范围与边界",
        "weight": 8,
        "description": "是否明确包含范围、排除范围、边界条件和适用边界",
    },
    {
        "key": "cross_dependencies",
        "name": "跨层-假设与依赖",
        "weight": 8,
        "description": "是否说明假设、前置条件、上下游依赖和外部约束",
    },
    {
        "key": "cross_traceability",
        "name": "跨层-一致性与可追踪",
        "weight": 7,
        "description": "OR/DR/DS/TDR/TDS 是否语义一致、可追踪、无明显冲突",
    },
    {
        "key": "cross_exceptions",
        "name": "跨层-异常处理与边界条件",
        "weight": 7,
        "description": "是否覆盖异常输入、失败路径、日志、回滚、告警等边界情况",
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
    "dr_id": "DR需求编号",
    "dr_name": "DR需求名称*",
    "dr_desc": "DR需求描述*",
    "dr_integration": "集成方式",
    "dr_param": "参数规格",
    "dr_operation": "操作场景",
    "dr_test": "系统测试要点",
    "dr_security": "安全约束",
    "ds_id": "DS需求编号",
    "ds_desc": "DS需求描述*",
    "ds_dependencies": "假设和依赖信息",
    "ds_verify": "验证方法描述",
    "tdr_id": "TDR需求编号",
    "tdr_desc": "TDR需求描述*",
    "tds_id": "TDS需求编号",
    "tds_desc": "TDS需求描述*",
}

DIMENSION_FIELD_MAP = {
    "or_user_language": ["OR需求名称*", "OR需求描述*", "更多描述信息"],
    "or_scenario": ["应用场景", "操作场景", "OR需求描述*", "更多描述信息"],
    "or_user_value": ["客户问题", "价值描述", "OR需求描述*"],
    "or_constraints": ["约束与限制", "安全约束", "集成方式", "更多描述信息"],
    "dr_security": ["安全约束", "DR需求描述*", "TDR需求描述*"],
    "dr_technical": ["DR需求描述*", "DS需求描述*", "TDR需求描述*", "TDS需求描述*", "集成方式", "参数规格"],
    "dr_testability": ["系统测试要点", "验证方法描述", "参数规格", "DR需求描述*", "DS需求描述*"],
    "dr_ambiguity": ["参数规格", "DR需求描述*", "TDR需求描述*"],
    "dr_performance": ["DR需求描述*", "参数规格", "约束与限制", "更多描述信息"],
    "dr_hardware": ["DR需求描述*", "参数规格", "约束与限制", "更多描述信息"],
    "cross_scope": ["OR需求描述*", "DR需求描述*", "DS需求描述*", "TDR需求描述*", "TDS需求描述*"],
    "cross_dependencies": ["假设和依赖信息", "集成方式", "约束与限制", "DS需求描述*", "TDS需求描述*"],
    "cross_traceability": ["OR需求编号", "DR需求编号", "DS需求编号", "TDR需求编号", "TDS需求编号", "ORURL", "DRURL", "DSURL", "TDRURL", "TDSURL"],
    "cross_exceptions": ["DR需求描述*", "系统测试要点", "验证方法描述", "安全约束", "更多描述信息"],
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


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def parse_dimensions_file(path: Path | None) -> Dict[str, Dict[str, object]]:
    if not path or not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r'"(?P<key>[^"]+)"\s*:\s*\{(?P<body>.*?)\}', re.S)
    parsed = {}
    for match in pattern.finditer(text):
        key = match.group("key")
        body = match.group("body")
        item = {"key": key}
        for field in ("name", "name_en", "description"):
            found = re.search(rf'"{field}"\s*:\s*"([^"]+)"', body)
            if found:
                item[field] = found.group(1)
        weight_match = re.search(r'"weight"\s*:\s*(\d+)', body)
        if weight_match:
            item["weight"] = int(weight_match.group(1))
        parsed[key] = item
    return parsed


def build_dimensions(path: Path | None) -> List[Dict[str, object]]:
    custom = parse_dimensions_file(path)
    by_key = {item["key"]: dict(item) for item in DEFAULT_DIMENSIONS}
    for key, item in custom.items():
        merged = dict(by_key.get(key, {"key": key}))
        merged.update(item)
        by_key[key] = merged
    ordered = [item["key"] for item in DEFAULT_DIMENSIONS]
    extras = [key for key in by_key if key not in ordered]
    return [by_key[key] for key in ordered + extras]


def read_csv(path: Path) -> List[RowRecord]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return []
    header = rows[0]
    records = []
    for idx, row in enumerate(rows[1:], start=1):
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        grouped: Dict[str, List[str]] = defaultdict(list)
        for name, value in zip(header, row):
            grouped[name].append("" if value is None else str(value))
        records.append(RowRecord(index=idx, grouped=dict(grouped)))
    return records


def read_excel(path: Path) -> List[RowRecord]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise SystemExit("读取 Excel 需要安装 openpyxl") from exc
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return []
    header = ["" if cell is None else str(cell) for cell in rows[0]]
    records = []
    for idx, row in enumerate(rows[1:], start=1):
        grouped: Dict[str, List[str]] = defaultdict(list)
        values = ["" if cell is None else str(cell) for cell in row]
        if len(values) < len(header):
            values += [""] * (len(header) - len(values))
        for name, value in zip(header, values):
            grouped[name].append(value)
        records.append(RowRecord(index=idx, grouped=dict(grouped)))
    return records


def read_json(path: Path) -> List[RowRecord]:
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
    return records


def read_records(path: Path) -> List[RowRecord]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return read_csv(path)
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
    return core


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
    dimensions_path: Path | None = None,
) -> Dict[str, object]:
    items = []
    for record in records:
        raw_fields = {
            key: [clean_text(value) for value in values if clean_text(value)]
            for key, values in record.grouped.items()
            if any(clean_text(value) for value in values)
        }
        if not raw_fields:
            continue
        core_fields = extract_core_fields(record)
        requirement_id = core_fields.get("or_id") or core_fields.get("dr_id") or core_fields.get("ds_id") or f"ROW-{record.index}"
        requirement_name = core_fields.get("or_name") or core_fields.get("dr_name") or requirement_id
        items.append(
            {
                "row_index": record.index,
                "id": requirement_id,
                "name": requirement_name,
                "core_fields": core_fields,
                "dimension_view": build_dimension_view(record, dimensions),
                "raw_fields": raw_fields,
            }
        )

    return {
        "input_path": str(input_path),
        "dimensions_path": str(dimensions_path) if dimensions_path else "",
        "item_count": len(items),
        "dimension_count": len(dimensions),
        "dimensions": dimensions,
        "header_summary": summarize_headers(records),
        "items": items,
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
    if packet.get("dimensions_path"):
        lines.append(f"- 维度文件: `{packet['dimensions_path']}`")
    lines.append(f"- 条目数: {packet['item_count']}")
    lines.append(f"- 维度数: {packet['dimension_count']}")
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
    lines.append("## 需求条目")
    lines.append("")
    for item in packet["items"]:
        lines.append(f"### 条目 {item['row_index']}: {item['id']} {item['name']}")
        lines.append("")
        lines.append("核心字段：")
        for key, value in item["core_fields"].items():
            if value:
                lines.append(f"- {key}: {value}")
        lines.append("")
        lines.append("维度视图：")
        for key, dimension in item.get("dimension_view", {}).items():
            lines.append(f"- {key} / {dimension['name']}")
            if dimension["evidence_fields"]:
                for field, values in dimension["evidence_fields"].items():
                    lines.append(f"  - evidence {field}: {' | '.join(values)}")
            if dimension["missing_fields"]:
                lines.append(f"  - missing: {', '.join(dimension['missing_fields'])}")
        lines.append("")
        lines.append("原始字段：")
        for key, values in item["raw_fields"].items():
            lines.append(f"- {key}: {' | '.join(values)}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build a review packet for LLM-based requirement evaluation.")
    parser.add_argument("--input", required=True, help="Path to the input CSV/Excel/JSON file.")
    parser.add_argument("--dimensions", help="Optional path to a dimensions file.")
    parser.add_argument("--output", required=True, help="Path to write the review packet.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output packet format.")
    args = parser.parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    dimensions_path = Path(args.dimensions).expanduser().resolve() if args.dimensions else None
    output_path = Path(args.output).expanduser().resolve()

    dimensions = build_dimensions(dimensions_path)
    records = read_records(input_path)
    packet = build_review_packet(input_path, dimensions, records, dimensions_path)

    if args.format == "json":
        output_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        output_path.write_text(render_review_packet_markdown(packet), encoding="utf-8")

    print(f"已生成评审任务包: {output_path}")
    print(f"条目数: {packet['item_count']}")


if __name__ == "__main__":
    main()
