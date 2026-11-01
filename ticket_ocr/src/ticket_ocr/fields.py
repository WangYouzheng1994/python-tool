"""仅从通用 OCR 明细提取总累计；不依赖 OCR 引擎，不推断其他业务字段。"""

from decimal import Decimal
import re
from typing import Any
import unicodedata


_NUMBER = re.compile(r"([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)([^\d.,+\-]*)")
_UNITS = {"公斤", "千克", "kg", "KG", "吨", "克", "g", "t", "元"}


def _normalize(text: str) -> str:
    """统一全角字符和空白，不将字母猜改为数字。"""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def _bounds(item: dict[str, Any]) -> tuple[float, float, float, float]:
    points = item["box"]
    return (min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points))


def _same_row(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """同时约束重叠比例与中心线，拒绝仅在边缘相交的邻行。"""
    _, y1, _, y2 = _bounds(left)
    _, v1, _, v2 = _bounds(right)
    height = min(y2 - y1, v2 - v1)
    return (height > 0 and min(y2, v2) - max(y1, v1) >= height * 0.6
            and abs((y1 + y2 - v1 - v2) / 2) <= height * 0.35)


def _parse(text: str) -> tuple[str | None, str | None]:
    match = _NUMBER.fullmatch(text)
    if match is None or (match[2] and match[2] not in _UNITS):
        return None, None
    return format(Decimal(match[1].replace(",", "")), "f"), match[2] or None


def _following_unit(
    items: list[dict[str, Any]], value_index: int,
) -> int | None:
    """只关联数值框右侧最近的同行单位，文字阻隔与距离限制两种布局共用。"""
    value_item = items[value_index]
    _, top, end, bottom = _bounds(value_item)
    following = sorted(
        (i for i, item in enumerate(items)
         if i != value_index and _bounds(item)[0] >= end and _same_row(value_item, item)),
        key=lambda i: _bounds(items[i])[0],
    )
    if following:
        index = following[0]
        if (_normalize(items[index]["text"]) in _UNITS
                and _bounds(items[index])[0] - end <= (bottom - top) * 1.5):
            return index
    return None


def extract_total_accumulated(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按从上到下、从左到右返回每个精确标签，不相加、不复用数值框。

    先精确匹配去空白、冒号后的标签；合框只接受标签后紧跟数值。
    分框须位于右侧且同行，其他文字框会阻隔关联；多个数值候选不猜选。
    缺失、格式异常、低 OCR 置信度和歧义均保留空值及证据供人工确认。
    evidence 的 confidence 仅是原 OCR 分数，并非字段关联置信度。
    合框仅保留整个框，绝不伪造字符坐标。阈值是保守启发式而非准确率保证。
    """
    labels = []
    for index, item in enumerate(items):
        text = _normalize(item["text"])
        if text.rstrip(":") == "总累计":
            labels.append((index, ""))
        elif text.startswith("总累计"):
            remainder = text[len("总累计"):]
            suffix = remainder.lstrip(":")
            if suffix and (remainder.startswith(":")
                           or suffix[0].isdigit() or suffix[0] in "+-."):
                labels.append((index, suffix))
    labels.sort(key=lambda pair: (_bounds(items[pair[0]])[1],
                                  _bounds(items[pair[0]])[0]))
    results = []
    claims: dict[int, list[int]] = {}
    for index, suffix in labels:
        label = items[index]
        evidence = [index]
        value, unit = _parse(suffix) if suffix else (None, None)
        status = "ok" if value is not None else "invalid" if suffix else "missing"
        value_index = index
        if not suffix:
            right = _bounds(label)[2]
            row = sorted((i for i, item in enumerate(items)
                          if i != index and _bounds(item)[0] >= right
                          and _same_row(label, item)), key=lambda i: _bounds(items[i])[0])
            candidates = []
            for i in row:
                text = _normalize(items[i]["text"])
                parsed, parsed_unit = _parse(text)
                if parsed is None:
                    # 单位可跟在数字后，其他字段阻止跳过它寻找更远的数值。
                    if text in _UNITS and candidates:
                        continue
                    if not candidates:
                        evidence.append(i)
                        status = "invalid" if any(c.isdigit() for c in text) else "missing"
                    break
                candidates.append((i, parsed, parsed_unit))
            if candidates:
                evidence.extend(i for i, _, _ in candidates)
                for candidate_index, _, _ in candidates:
                    claims.setdefault(candidate_index, []).append(len(results))
                if len(candidates) > 1:
                    status = "ambiguous"
                else:
                    value_index, value, unit = candidates[0]
                    status = "ok"
        if status == "ok" and unit is None:
            unit_index = _following_unit(items, value_index)
            if unit_index is not None:
                unit = _normalize(items[unit_index]["text"])
                evidence.append(unit_index)
        if status == "ok" and any(items[i]["confidence"] < 0.9 for i in evidence):
            status = "low_confidence"
        results.append({"value": value if status == "ok" else None,
                        "unit": unit, "status": status, "label_box": label["box"],
                        "evidence": [{"item_index": i, **items[i]} for i in evidence]})
    for owners in claims.values():
        if len(owners) > 1:
            for owner in owners:
                results[owner].update(value=None, status="ambiguous")
    return results
