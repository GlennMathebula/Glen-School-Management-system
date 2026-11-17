"""Pure FISA scoring rules for competency and percentage sittings.

No database access: testable without production learner records.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from fastapi import HTTPException


def number(value):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise HTTPException(400, "Invalid numeric mark")
    if not d.is_finite():
        raise HTTPException(400, "Marks must be finite")
    return d


def validate_marking(method, criteria, maxima, decisions):
    if method not in {"competency", "percentage"}:
        raise HTTPException(409, "Unknown FISA marking method")
    if len(decisions) != len(criteria) or {d.get("criterion") for d in decisions} != set(range(len(criteria))):
        raise HTTPException(400, "Each criterion must be marked exactly once")
    result = []
    for d in sorted(decisions, key=lambda item: item["criterion"]):
        if not isinstance(d.get("comment"), str) or not d["comment"].strip():
            raise HTTPException(400, "Every criterion requires a marking comment")
        row = {"criterion": d["criterion"], "comment": d["comment"].strip()}
        if method == "competency":
            if d.get("result") not in {"C", "NYC"} or d.get("awarded_marks") is not None:
                raise HTTPException(400, "Competency requires C/NYC and no numeric mark")
            row["result"] = d["result"]
        else:
            if d.get("result") is not None:
                raise HTTPException(400, "Percentage criteria require marks, not C/NYC")
            if d.get("awarded_marks") is None:
                raise HTTPException(400, "Every percentage criterion requires awarded marks")
            maximum = number(maxima[d["criterion"]])
            awarded = number(d["awarded_marks"])
            if maximum <= 0 or awarded < 0 or awarded > maximum:
                raise HTTPException(400, "Awarded marks must be between zero and criterion maximum")
            row["awarded_marks"] = float(awarded)
        result.append(row)
    return result


def render_result(sitting, raw_decisions):
    if not isinstance(raw_decisions, list):
        raise HTTPException(409, "Moderation decisions missing")
    method = sitting["marking_method"]
    # Revalidate stored JSON rather than trusting a prior UI submission.
    decisions = validate_marking(method, sitting["criteria"], sitting["criterion_max_marks"], raw_decisions)
    if method == "competency":
        outcome = "C" if all(d["result"] == "C" for d in decisions) else "NYC"
        return outcome, None, None, None
    total = sum((number(d["awarded_marks"]) for d in decisions), Decimal(0))
    maximum = sum((number(x) for x in sitting["criterion_max_marks"]), Decimal(0))
    if maximum <= 0:
        raise HTTPException(409, "FISA maximum mark is invalid")
    percentage = (total / maximum * Decimal(100)).quantize(Decimal("0.01"))
    cutoff = number(sitting["pass_percentage"])
    outcome = "Pass" if total / maximum * Decimal(100) >= cutoff else "Fail"
    return outcome, float(percentage), float(total), float(maximum)


def valid_rendered(sitting, script):
    method = sitting.get("marking_method")
    outcome = script.get("rendered_outcome")
    score = script.get("rendered_percentage")
    if method == "competency":
        return outcome in {"C", "NYC"} and score is None
    if method == "percentage":
        if outcome not in {"Pass", "Fail"} or score is None:
            return False
        try:
            value = number(score)
        except HTTPException:
            return False
        return Decimal(0) <= value <= Decimal(100)
    return False
