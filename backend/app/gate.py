from __future__ import annotations

import json
import re
from typing import List, Optional, Tuple

from .models import (
    AiStatus,
    ComplianceStatus,
    DeepSeekDecision,
    GateResult,
    OpenCVDiff,
    QwenResult,
)


HIGH_SAFETY_KEYWORDS = (
    "battery",
    "power",
    "voltage",
    "pressure",
)


def _contains_high_safety_terms(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in HIGH_SAFETY_KEYWORDS)


def fail_closed_reject(ai_status: AiStatus, reasons: List[str]) -> GateResult:
    return GateResult(
        status=ComplianceStatus.REJECTED,
        reasons=reasons,
        ai_status=ai_status,
        qwen=None,
        deepseek=None,
    )


def rule_gate(
    *,
    opencv: OpenCVDiff,
    ai_status: AiStatus,
    qwen: Optional[QwenResult],
    deepseek: Optional[DeepSeekDecision],
    image_verification_evidence_available: bool,
) -> GateResult:
    """
    Enforces non-negotiable fail-closed safety rules.
    This function must be deterministic and auditable.
    """

    reasons: List[str] = []

    # Required: OpenCV diffs must exist (validated by schema min_length=1).
    # Guard anyway for defense-in-depth.
    if not opencv.diffs:
        reasons.append("OpenCV diff is empty; cannot determine allowed edits.")
        return fail_closed_reject(ai_status, reasons)

    # Fail-closed if any AI service unavailable (per spec).
    if not ai_status.qwen_available or not ai_status.deepseek_available:
        reasons.append("AI service unavailable (qwen or deepseek); fail-closed.")
        return fail_closed_reject(ai_status, reasons)

    # Fail-closed on missing AI outputs or JSON parse failure upstream.
    if qwen is None:
        reasons.append("Qwen result missing/unparseable; fail-closed.")
        return fail_closed_reject(ai_status, reasons)
    if deepseek is None:
        reasons.append("DeepSeek decision missing/unparseable; fail-closed.")
        return fail_closed_reject(ai_status, reasons)

    # Ambiguous component classification -> reject.
    if qwen.classification not in ("Internal Component", "External Component"):
        reasons.append("Ambiguous component classification; fail-closed.")
        return fail_closed_reject(ai_status, reasons)

    # If external component, require image verification evidence + successful result.
    if qwen.classification == "External Component":
        if not image_verification_evidence_available:
            reasons.append("External component but image evidence missing/unclear; fail-closed.")
            return fail_closed_reject(ai_status, reasons)
        if qwen.image_verification_required and not qwen.image_verification_result:
            reasons.append("External component image verification failed; reject.")
            return fail_closed_reject(ai_status, reasons)

    # High-safety keywords require HIGH safety and explicit approval.
    joined = " ".join([opencv.spec_name] + [d.component_path for d in opencv.diffs])
    if _contains_high_safety_terms(joined):
        if deepseek.safety_level != "HIGH":
            reasons.append("High-safety domain change requires HIGH safety level; reject.")
            return fail_closed_reject(ai_status, reasons)

    # DeepSeek is policy gate: if not approved, reject.
    if not deepseek.approved or not deepseek.update_docs:
        reasons.append(f"DeepSeek blocked update: {deepseek.reason}")
        return fail_closed_reject(ai_status, reasons)

    return GateResult(
        status=ComplianceStatus.APPROVED,
        reasons=[],
        ai_status=ai_status,
        qwen=qwen,
        deepseek=deepseek,
    )

