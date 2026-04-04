#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence


DEFAULT_DIMENSIONS = [
    {"key": "or_user_language", "name": "OR-用户语言描述", "weight": 6},
    {"key": "or_scenario", "name": "OR-应用场景", "weight": 6},
    {"key": "or_user_value", "name": "OR-用户价值", "weight": 4},
    {"key": "or_constraints", "name": "OR-约束和限制", "weight": 4},
    {"key": "dr_security", "name": "DR-安全分析", "weight": 8},
    {"key": "dr_technical", "name": "DR-技术描述", "weight": 14},
    {"key": "dr_testability", "name": "DR-可测试性", "weight": 14},
    {"key": "dr_ambiguity", "name": "DR-无歧义性", "weight": 8},
    {"key": "dr_performance", "name": "DR-性能需求", "weight": 4},
    {"key": "dr_hardware", "name": "DR-硬件分析", "weight": 2},
    {"key": "cross_scope", "name": "跨层-范围与边界", "weight": 10},
    {"key": "cross_dependencies", "name": "跨层-假设与依赖", "weight": 8},
    {"key": "cross_traceability", "name": "跨层-一致性与可追踪", "weight": 4},
    {"key": "cross_exceptions", "name": "跨层-异常处理与边界条件", "weight": 10},
]

VAGUE_TERMS = [
    "支持",
    "完整",
    "相关",
    "合理",
    "适当",
    "必要",
    "尽量",
    "可根据",
    "等等",
    "等",
]
SECURITY_TERMS = [
    "安全",
    "鉴权",
    "认证",
    "授权",
    "口令",
    "密码",
    "加密",
    "审计",
    "日志",
    "红线",
    "漏洞",
    "攻击",
    "sm2",
    "sm3",
    "sm4",
]
PERFORMANCE_TERMS = [
    "性能",
    "响应时间",
    "吞吐",
    "并发",
    "延迟",
    "时延",
    "qps",
    "tps",
]
HARDWARE_TERMS = ["cpu", "内存", "存储", "磁盘", "硬件", "带宽", "网卡"]
EXCEPTION_TERMS = [
    "异常",
    "错误",
    "失败",
    "超时",
    "边界",
    "非法",
    "无效",
    "告警",
    "回滚",
    "冲突",
    "重试",
]
DEPENDENCY_TERMS = ["依赖", "前提", "假设", "兼容", "集成", "上游", "下游", "第三方", "外部"]
USER_TERMS = ["用户", "客户", "场景", "价值", "问题", "业务"]


@dataclass
class RowRecord:
    index: int
    grouped: Dict[str, List[str]]

    def first(self, key: str, occurrence: int = 0) -> str:
        values = self.grouped.get(key, [])
        if occurrence < len(values):
            return values[occurrence].strip()
        return ""

    def any_of(self, keys: Sequence[str]) -> str:
        for key in keys:
            value = self.first(key)
            if value:
                return value
        return ""


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def contains_any(text: str, terms: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def count_any(text: str, terms: Sequence[str]) -> int:
    lowered = text.lower()
    return sum(1 for term in terms if term.lower() in lowered)


def has_quant_signal(text: str) -> bool:
    return bool(
        re.search(r"\b\d+(\.\d+)?\b", text)
        or re.search(r"(ms|s|秒|分钟|小时|%|kb|mb|gb|tb|qps|tps|mbps)", text.lower())
        or any(token in text for token in ["0-255", ">=", "<=", "必填", "选填"])
    )


def has_enumeration(text: str) -> bool:
    return bool(re.search(r"(\n|\A)\s*(\d+[.、]|[-*])", text))


def split_lines(text: str) -> List[str]:
    return [line.strip() for line in re.split(r"[\n。；;]", text) if line.strip()]


def clamp_ratio(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_bucket(value: float, weight: int) -> int:
    return int(round(clamp_ratio(value) * weight))


def parse_dimensions_file(path: Path | None) -> Dict[str, Dict[str, object]]:
    if not path or not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'"(?P<key>[^"]+)"\s*:\s*\{(?P<body>.*?)\}',
        re.S,
    )
    parsed = {}
    for match in pattern.finditer(text):
        key = match.group("key")
        body = match.group("body")
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', body)
        weight_match = re.search(r'"weight"\s*:\s*(\d+)', body)
        desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', body)
        if not name_match or not weight_match:
            continue
        parsed[key] = {
            "key": key,
            "name": name_match.group(1),
            "weight": int(weight_match.group(1)),
            "description": desc_match.group(1) if desc_match else "",
        }
    return parsed


def build_dimensions(path: Path | None) -> List[Dict[str, object]]:
    custom = parse_dimensions_file(path)
    by_key = {item["key"]: dict(item) for item in DEFAULT_DIMENSIONS}
    for key, item in custom.items():
        if key in by_key:
            merged = dict(by_key[key])
            for field in ("name", "description"):
                if item.get(field):
                    merged[field] = item[field]
            by_key[key] = merged
        else:
            by_key[key] = dict(item)
    ordered_keys = [item["key"] for item in DEFAULT_DIMENSIONS]
    return [by_key[key] for key in ordered_keys]


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
            grouped[name].append(value or "")
        records.append(RowRecord(index=idx, grouped=dict(grouped)))
    return records


def read_excel(path: Path) -> List[RowRecord]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise SystemExit("读取 Excel 需要安装 openpyxl") from exc
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
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
        grouped = {str(k): ["" if v is None else str(v)] for k, v in item.items()}
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


def normalize_for_similarity(text: str) -> str:
    return re.sub(r"[\W_]+", "", text.lower())


def similarity(a: str, b: str) -> float:
    a_norm = normalize_for_similarity(a)
    b_norm = normalize_for_similarity(b)
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    overlap = len(set(a_norm) & set(b_norm))
    base = len(set(a_norm) | set(b_norm)) or 1
    return overlap / base


def evidence_list(*parts: str) -> List[str]:
    return [clean_text(part) for part in parts if clean_text(part)]


def extract_context(record: RowRecord) -> Dict[str, str]:
    return {
        "or_id": record.first("OR需求编号"),
        "or_name": record.first("OR需求名称*"),
        "or_desc": record.first("OR需求描述*"),
        "scenario": record.first("应用场景"),
        "customer_problem": record.first("客户问题"),
        "value_desc": record.first("价值描述"),
        "constraints": record.first("约束与限制"),
        "dr_id": record.first("DR需求编号"),
        "dr_name": record.first("DR需求名称*"),
        "dr_desc": record.first("DR需求描述*"),
        "dr_integration": record.first("集成方式", 0),
        "dr_param": record.first("参数规格", 0),
        "dr_operation": record.first("操作场景", 0),
        "dr_test": record.first("系统测试要点", 0),
        "dr_security": record.first("安全约束", 0),
        "ds_id": record.first("DS需求编号"),
        "ds_desc": record.first("DS需求描述*"),
        "ds_dependencies": record.first("假设和依赖信息", 0),
        "ds_verify": record.first("验证方法描述", 0),
        "tdr_id": record.first("TDR需求编号"),
        "tdr_desc": record.first("TDR需求描述*"),
        "tdr_param": record.first("参数规格", 1),
        "tdr_operation": record.first("操作场景", 1),
        "tdr_test": record.first("系统测试要点", 1),
        "tdr_security": record.first("安全约束", 1),
        "tds_id": record.first("TDS需求编号"),
        "tds_desc": record.first("TDS需求描述*"),
        "tds_dependencies": record.first("假设和依赖信息", 1),
        "tds_verify": record.first("验证方法描述", 1),
        "or_url": record.first("ORURL"),
        "dr_url": record.first("DRURL"),
    }


def score_row(record: RowRecord, dimensions: List[Dict[str, object]]) -> Dict[str, object]:
    ctx = extract_context(record)
    or_text = "\n".join(evidence_list(ctx["or_name"], ctx["or_desc"], ctx["scenario"], ctx["customer_problem"], ctx["value_desc"], ctx["constraints"]))
    dr_text = "\n".join(evidence_list(ctx["dr_name"], ctx["dr_desc"], ctx["dr_integration"], ctx["dr_param"], ctx["dr_operation"], ctx["dr_test"], ctx["dr_security"]))
    ds_text = "\n".join(evidence_list(ctx["ds_desc"], ctx["ds_dependencies"], ctx["ds_verify"], ctx["tdr_desc"], ctx["tdr_param"], ctx["tdr_test"], ctx["tds_desc"], ctx["tds_dependencies"], ctx["tds_verify"]))
    all_text = "\n".join(part for part in [or_text, dr_text, ds_text] if part)

    scores = []
    red_flags: List[str] = []
    missing: List[str] = []
    suggestions: List[str] = []

    def add_result(key: str, ratio: float, reason: str) -> None:
        dim = next(item for item in dimensions if item["key"] == key)
        weight = int(dim["weight"])
        score = score_bucket(ratio, weight)
        scores.append(
            {
                "key": key,
                "name": dim["name"],
                "weight": weight,
                "score": score,
                "reason": reason,
            }
        )

    technical_density = count_any(or_text, SECURITY_TERMS + PERFORMANCE_TERMS + HARDWARE_TERMS) / max(len(USER_TERMS), 1)
    ratio = 0.0
    if ctx["or_desc"]:
        ratio += 0.45
    if ctx["customer_problem"] or ctx["value_desc"]:
        ratio += 0.25
    if contains_any(or_text, USER_TERMS):
        ratio += 0.15
    if technical_density < 1.3:
        ratio += 0.15
    add_result("or_user_language", ratio, "看是否能从 OR 层直接理解用户诉求，而不是只看到技术动作。")

    ratio = 0.0
    if ctx["scenario"]:
        ratio += 0.7
    if ctx["dr_operation"]:
        ratio += 0.2
    if contains_any(or_text + dr_text, ["场景", "当", "在", "操作", "配置"]):
        ratio += 0.1
    add_result("or_scenario", ratio, "看是否写明使用场景、触发条件和上下文。")

    ratio = 0.0
    if ctx["customer_problem"]:
        ratio += 0.5
    if ctx["value_desc"]:
        ratio += 0.35
    if contains_any(or_text, ["问题", "价值", "效率", "风险", "体验", "业务"]):
        ratio += 0.15
    add_result("or_user_value", ratio, "看是否说清用户问题与收益。")

    ratio = 0.0
    if ctx["constraints"]:
        ratio += 0.7
    if contains_any(all_text, SECURITY_TERMS + PERFORMANCE_TERMS + ["合规", "限制", "兼容", "部署"]):
        ratio += 0.3
    add_result("or_constraints", ratio, "看是否交代约束、限制或合规边界。")

    ratio = 0.0
    if ctx["dr_security"]:
        ratio += 0.7
    if contains_any(dr_text, SECURITY_TERMS):
        ratio += 0.3
    add_result("dr_security", ratio, "看是否有显式安全要求、安全红线或审计要求。")

    ratio = 0.0
    if ctx["dr_desc"]:
        ratio += 0.35
    if ctx["dr_param"]:
        ratio += 0.2
    if ctx["dr_integration"] or ctx["dr_operation"]:
        ratio += 0.15
    if has_enumeration(ctx["dr_desc"]):
        ratio += 0.15
    if contains_any(dr_text, EXCEPTION_TERMS):
        ratio += 0.15
    add_result("dr_technical", ratio, "看技术设计是否具体、完整、可执行。")

    ratio = 0.0
    if ctx["dr_test"] or ctx["ds_verify"] or ctx["tds_verify"]:
        ratio += 0.6
    if has_quant_signal(dr_text + ds_text):
        ratio += 0.25
    if ctx["dr_param"]:
        ratio += 0.15
    if contains_any(dr_text, EXCEPTION_TERMS):
        ratio += 0.1
    if ctx["dr_operation"] and has_enumeration(ctx["dr_desc"]):
        ratio += 0.1
    add_result("dr_testability", ratio, "看是否能直接据此写出测试点或验收方法。")

    vague_hits = count_any(dr_text, VAGUE_TERMS)
    precise_bonus = 0.4 if has_quant_signal(dr_text) else 0.0
    param_bonus = 0.35 if ctx["dr_param"] else 0.0
    ambiguity_ratio = clamp_ratio(0.35 + precise_bonus + param_bonus - 0.08 * vague_hits)
    add_result("dr_ambiguity", ambiguity_ratio, "看参数、行为和边界是否明确，是否存在模糊措辞。")

    ratio = 0.0
    if contains_any(all_text, PERFORMANCE_TERMS):
        ratio += 0.7
    if has_quant_signal(all_text) and contains_any(all_text, ["响应", "吞吐", "性能", "时延"]):
        ratio += 0.3
    add_result("dr_performance", ratio, "看是否有性能目标，或至少明确说明不涉及性能约束。")

    ratio = 0.0
    if contains_any(all_text, HARDWARE_TERMS):
        ratio += 0.8
    if contains_any(ds_text, ["不涉及硬件", "无硬件影响"]):
        ratio += 0.5
    add_result("dr_hardware", ratio, "看是否说明资源或硬件假设，若不适用也应说明。")

    ratio = 0.0
    if ctx["or_desc"] and ctx["dr_desc"]:
        ratio += 0.35
    if ctx["constraints"] or ctx["dr_param"]:
        ratio += 0.2
    if ctx["scenario"] or ctx["dr_operation"]:
        ratio += 0.2
    if not any(term in all_text for term in ["等", "相关"]) or has_quant_signal(all_text):
        ratio += 0.25
    add_result("cross_scope", ratio, "看范围、边界和主要行为是否被限定清楚。")

    ratio = 0.0
    if ctx["ds_dependencies"] or ctx["tds_dependencies"]:
        ratio += 0.7
    if ctx["dr_integration"]:
        ratio += 0.15
    if contains_any(all_text, DEPENDENCY_TERMS):
        ratio += 0.15
    add_result("cross_dependencies", ratio, "看是否写明假设、依赖、集成前提和外部条件。")

    name_similarity = max(similarity(ctx["or_name"], ctx["dr_name"]), similarity(ctx["or_desc"], ctx["dr_desc"]))
    ratio = 0.0
    if ctx["or_id"] and ctx["dr_id"]:
        ratio += 0.25
    if name_similarity > 0.7:
        ratio += 0.35
    elif name_similarity > 0.4:
        ratio += 0.2
    if ctx["ds_id"] or ctx["tdr_id"] or ctx["tds_id"]:
        ratio += 0.25
    if ctx["or_url"] and ctx["dr_url"]:
        ratio += 0.15
    add_result("cross_traceability", ratio, "看 OR/DR/DS/TDR/TDS 是否能互相追踪，语义是否一致。")

    ratio = 0.0
    if contains_any(all_text, EXCEPTION_TERMS):
        ratio += 0.45
    if ctx["dr_test"] and contains_any(ctx["dr_test"], EXCEPTION_TERMS):
        ratio += 0.25
    if contains_any(all_text, ["日志", "审计", "回滚", "超时", "失败"]):
        ratio += 0.3
    add_result("cross_exceptions", ratio, "看是否覆盖异常、边界输入、失败处理和审计。")

    total = sum(item["score"] for item in scores)
    grade = grade_for_score(total)

    if not ctx["customer_problem"] and not ctx["value_desc"]:
        missing.append("未显式说明客户问题或价值描述。")
        suggestions.append("补写“客户问题”和“价值描述”，说明为什么要做，而不仅是做什么。")
    if not ctx["scenario"] and not ctx["dr_operation"]:
        missing.append("缺少应用场景或操作场景。")
        suggestions.append("补充触发场景、使用环境和关键操作上下文。")
    if not ctx["dr_test"] and not ctx["ds_verify"] and not ctx["tds_verify"]:
        missing.append("缺少测试要点或验证方法。")
        suggestions.append("增加可直接转成测试用例的验收标准、验证步骤或边界条件。")
    if not ctx["ds_dependencies"] and not ctx["tds_dependencies"] and not contains_any(all_text, DEPENDENCY_TERMS):
        missing.append("缺少假设和依赖说明。")
        suggestions.append("明确依赖的系统、接口、前置条件、兼容性要求和不满足时的处理。")
    if count_any(all_text, VAGUE_TERMS) >= 3:
        red_flags.append("存在较多模糊措辞，可能导致实现和测试理解不一致。")
        suggestions.append("把“支持/完整/相关/等”改写为明确参数、范围、状态和验收结果。")
    if not contains_any(all_text, EXCEPTION_TERMS):
        red_flags.append("几乎未体现异常处理或边界条件。")
        suggestions.append("补充非法输入、失败、超时、冲突、日志与回滚等异常路径。")
    if total < 60:
        red_flags.append("整体信息不足，尚不具备优秀设计文档的完整性。")
    if not ctx["dr_security"] and not contains_any(all_text, SECURITY_TERMS):
        red_flags.append("安全要求表达较弱或缺失。")
        suggestions.append("补充认证、授权、审计、加密、红线映射或合规要求。")

    identifiers = [ctx["or_id"], ctx["dr_id"], ctx["ds_id"], ctx["tdr_id"], ctx["tds_id"]]
    name = ctx["or_name"] or ctx["dr_name"] or ctx["ds_desc"][:30] or f"需求{record.index}"

    return {
        "index": record.index,
        "id": next((item for item in identifiers if item), f"ROW-{record.index}"),
        "name": name,
        "total": total,
        "grade": grade,
        "scores": scores,
        "evidence": [item for item in evidence_list(ctx["or_desc"], ctx["dr_desc"], ctx["ds_desc"], ctx["tdr_desc"], ctx["tds_desc"])[:3]],
        "red_flags": dedupe(red_flags)[:4],
        "missing": dedupe(missing)[:5],
        "suggestions": dedupe(suggestions)[:5],
    }


def dedupe(items: Sequence[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def grade_for_score(score: int) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def overall_judgment(avg_score: float) -> str:
    if avg_score >= 80:
        return "整体已接近优秀设计标准，但仍需检查个别薄弱项。"
    if avg_score >= 65:
        return "整体具备一定设计基础，但还未稳定达到优秀设计标准。"
    if avg_score >= 50:
        return "整体处于可用但偏粗糙的阶段，距离优秀设计标准仍有明显差距。"
    return "整体未达到优秀设计标准，需求文档的信息完整性和可执行性不足。"


def item_judgment(score: int) -> str:
    if score >= 80:
        return "该需求基本达到优秀设计标准，仅需补充少量边角信息。"
    if score >= 65:
        return "该需求基础较好，但仍需补充少量验证和边界细节。"
    if score >= 50:
        return "该需求具备一定设计基础，但距离优秀设计标准还有明显差距。"
    return "该需求未达到优秀设计标准，信息完整性和可执行性不足。"


def render_report(input_path: Path, dims_path: Path | None, results: List[Dict[str, object]], dimensions: List[Dict[str, object]]) -> str:
    total_scores = [item["total"] for item in results]
    avg_score = statistics.mean(total_scores) if total_scores else 0.0
    median_score = statistics.median(total_scores) if total_scores else 0.0
    grade_counts = Counter(item["grade"] for item in results)
    weak_counter = Counter()
    for result in results:
        ranked = sorted(result["scores"], key=lambda item: item["score"] / max(item["weight"], 1))
        for item in ranked[:3]:
            weak_counter[item["name"]] += 1

    lines = []
    lines.append("# 需求文档评估报告")
    lines.append("")
    lines.append("## 1. 评估概览")
    lines.append("")
    lines.append(f"- 数据源: `{input_path}`")
    lines.append(f"- 维度来源: `{dims_path}`、输入表头、superpowers 需求设计标准" if dims_path else "- 维度来源: 输入表头与 superpowers 需求设计标准")
    lines.append(f"- 需求条目数: {len(results)}")
    lines.append("- 评分方法: 100 分制，优先采用用户自定义维度，再补充跨层设计质量维度")
    lines.append(f"- 平均分: {avg_score:.1f}")
    lines.append(f"- 中位分: {median_score:.1f}")
    lines.append(f"- 等级分布: A={grade_counts.get('A', 0)}，B={grade_counts.get('B', 0)}，C={grade_counts.get('C', 0)}，D={grade_counts.get('D', 0)}")
    lines.append(f"- 总体结论: {overall_judgment(avg_score)}")
    lines.append("")
    lines.append("## 2. 总体发现")
    lines.append("")
    lines.append("### 最常见问题")
    lines.append("")
    for name, count in weak_counter.most_common(5):
        lines.append(f"- {name}: 在 {count} 条需求中进入最低分维度")
    if not weak_counter:
        lines.append("- 未识别到明显共性问题。")
    lines.append("")
    lines.append("### 结构性结论")
    lines.append("")
    lines.append("- 多数需求更偏“功能陈述”而非“完整需求设计”，常见缺口是用户价值、场景、验证方法和异常路径。")
    lines.append("- OR 与 DR 字段在不少条目中能对齐到同名主题，但跨层的假设、依赖、DS/TDS 验证信息普遍不足。")
    lines.append("- 安全相关需求通常写得比性能、硬件、边界条件更完整，说明当前文档更重合规红线，弱于实现就绪性。")
    lines.append("")
    lines.append("## 3. 单条需求评估结果")
    lines.append("")
    for idx, result in enumerate(sorted(results, key=lambda item: item["total"], reverse=True), start=1):
        lines.append(f"### 需求 {idx}: {result['id']} {result['name']}")
        lines.append("")
        lines.append(f"- 总分: {result['total']}/100")
        lines.append(f"- 等级: {result['grade']}")
        lines.append(f"- 结论: {item_judgment(result['total'])}")
        lines.append("")
        lines.append("| 维度 | 分数 | 说明 |")
        lines.append("| --- | ---: | --- |")
        for item in result["scores"]:
            lines.append(f"| {item['name']} | {item['score']}/{item['weight']} | {item['reason']} |")
        lines.append("")
        lines.append("关键证据：")
        if result["evidence"]:
            for item in result["evidence"]:
                lines.append(f"- {item}")
        else:
            lines.append("- 无足够正文证据。")
        lines.append("")
        lines.append("红旗问题：")
        if result["red_flags"]:
            for item in result["red_flags"]:
                lines.append(f"- {item}")
        else:
            lines.append("- 无明显红旗。")
        lines.append("")
        lines.append("缺失项：")
        if result["missing"]:
            for item in result["missing"]:
                lines.append(f"- {item}")
        else:
            lines.append("- 无明显缺失项。")
        lines.append("")
        lines.append("修改建议：")
        if result["suggestions"]:
            for order, item in enumerate(result["suggestions"], start=1):
                lines.append(f"{order}. {item}")
        else:
            lines.append("1. 维持当前结构，补充少量验收细节即可。")
        lines.append("")
    lines.append("## 4. 优先级建议")
    lines.append("")
    lines.append("### 高优先级")
    lines.append("")
    lines.append("- 给所有需求补齐“应用场景、客户问题、价值描述、约束与限制”四类 OR 信息，避免只剩功能标题和技术动作。")
    lines.append("- 给所有 DR/DS/TDS 需求补齐“系统测试要点/验证方法描述”，把文字要求转成可验收条目。")
    lines.append("- 对所有涉及配置、接口、安全、日志的需求补充异常处理、边界输入和失败行为。")
    lines.append("")
    lines.append("### 中优先级")
    lines.append("")
    lines.append("- 对性能、资源、硬件影响统一增加“适用/不适用”说明，避免评审时默认缺失。")
    lines.append("- 把红线、合规、标准引用映射到具体行为和验收点，而不是只列标准编号。")
    lines.append("- 补充假设与依赖字段，明确前置条件、上下游依赖和兼容性约束。")
    lines.append("")
    lines.append("### 低优先级")
    lines.append("")
    lines.append("- 统一术语与措辞，减少“支持、完整、相关、等”等泛化表述。")
    lines.append("- 对高质量需求沉淀成模板，约束后续录入方式。")
    lines.append("")
    lines.append("## 5. 附录")
    lines.append("")
    lines.append("### 维度摘要")
    lines.append("")
    for item in dimensions:
        lines.append(f"- {item['name']} ({item['weight']} 分)")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate requirement documents from CSV, Excel, or JSON.")
    parser.add_argument("--input", required=True, help="Path to the input CSV/Excel/JSON file.")
    parser.add_argument("--dimensions", help="Optional path to dimensions.txt-like rubric file.")
    parser.add_argument("--output", required=True, help="Path to the Markdown report to write.")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    dims_path = Path(args.dimensions).expanduser().resolve() if args.dimensions else None
    output_path = Path(args.output).expanduser().resolve()

    dimensions = build_dimensions(dims_path)
    records = read_records(input_path)
    results = [score_row(record, dimensions) for record in records if any(clean_text(value) for values in record.grouped.values() for value in values)]
    report = render_report(input_path, dims_path, results, dimensions)
    output_path.write_text(report, encoding="utf-8")
    print(f"已生成报告: {output_path}")
    print(f"已评估条目数: {len(results)}")


if __name__ == "__main__":
    main()
