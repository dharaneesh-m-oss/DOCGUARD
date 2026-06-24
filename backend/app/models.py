from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AiStatus(BaseModel):
    qwen_available: bool
    deepseek_available: bool


class OpenCVDiffItem(BaseModel):
    """
    Minimal schema for deterministic diff results (source of truth).
    This intentionally stays strict and small; extend only when OpenCV output is known.
    """

    component_path: str = Field(min_length=1)
    old_value: Any
    new_value: Any
    allowed_edit_region: Optional[Dict[str, Any]] = None  # image bounding boxes etc.


class OpenCVDiff(BaseModel):
    spec_name: str = Field(min_length=1)
    spec_diff_hash: str = Field(min_length=8)
    diffs: List[OpenCVDiffItem] = Field(min_length=1)


class QwenClassification(str, Enum):
    INTERNAL = "Internal Component"
    EXTERNAL = "External Component"


class QwenResult(BaseModel):
    component_name: str
    classification: QwenClassification
    image_verification_required: bool
    image_verification_result: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class SafetyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DeepSeekDecision(BaseModel):
    approved: bool
    safety_level: SafetyLevel
    reason: str
    update_docs: bool


class ComplianceStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GateResult(BaseModel):
    status: ComplianceStatus
    reasons: List[str] = Field(default_factory=list)
    ai_status: AiStatus
    qwen: Optional[QwenResult] = None
    deepseek: Optional[DeepSeekDecision] = None


class RunResponse(BaseModel):
    status: ComplianceStatus
    reasons: List[str]
    audit_zip_path: str


class ViewType(str, Enum):
    FRONT = "front"
    SIDE = "side"
    UNKNOWN = "unknown"


class UpdateAction(BaseModel):
    type: Literal["text", "image"]
    target: str  # Placeholder text or image description
    new_value: str  # New text value or path to new image


class VisionAnalysisResult(BaseModel):
    view_type: ViewType
    mismatches: List[str]
    update_actions: List[UpdateAction]
    confidence: float


class DocumentUpdateResponse(BaseModel):
    success: bool
    message: str
    output_path: Optional[str] = None

