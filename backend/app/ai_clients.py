from __future__ import annotations

from typing import Optional, Tuple

from .config import settings
from .models import AiStatus, DeepSeekDecision, QwenResult


def get_ai_status() -> AiStatus:
    # Conservative default: if not enabled, treat as unavailable.
    return AiStatus(
        qwen_available=bool(settings.qwen_enabled),
        deepseek_available=bool(settings.deepseek_enabled),
    )


def call_qwen_for_component(*, component_name: str, context: str) -> Tuple[Optional[QwenResult], Optional[str]]:
    """
    Stub: cloud call intentionally not implemented in this scaffold.
    Return (result, error_reason). Any error must be treated as fail-closed upstream.
    """

    if not settings.qwen_enabled:
        return None, "qwen disabled"
    return None, "qwen client not implemented"


def call_deepseek_policy(*, context: str) -> Tuple[Optional[DeepSeekDecision], Optional[str]]:
    """
    Stub: cloud call intentionally not implemented in this scaffold.
    Return (result, error_reason). Any error must be treated as fail-closed upstream.
    """

    if not settings.deepseek_enabled:
        return None, "deepseek disabled"
    return None, "deepseek client not implemented"


def analyze_photo_view(image_bytes: bytes) -> VisionAnalysisResult:
    """
    Vision-AI stub: Analyzes the photo to determine if it's a side view.
    In a real implementation, this would call a Vision-LLM (like GPT-4o or Gemini Flash).
    """
    # Placeholder logic: 
    # If the user mentioned 'side' in the request, we'll simulate a side-view detection.
    # For now, we return a mock result.
    return VisionAnalysisResult(
        view_type="side",
        mismatches=["Internal battery bracket missing in side view"],
        update_actions=[
            UpdateAction(type="text", target="{{STATUS}}", new_value="Side View Verified"),
            UpdateAction(type="image", target="SIDE_VIEW_PLACEHOLDER", new_value="uploaded_photo.jpg")
        ],
        confidence=0.95
    )


def generate_update_instructions(spec_content: str, vision_result: VisionAnalysisResult) -> VisionAnalysisResult:
    """
    Combines specification text with vision results to finalize update actions.
    """
    # Logic to merge spec requirements with vision findings.
    if "bracket" in spec_content.lower():
        vision_result.update_actions.append(
            UpdateAction(type="text", target="{{BRACKET_CHECK}}", new_value="Verified per spec")
        )
    return vision_result

