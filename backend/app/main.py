from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pydantic import BaseModel
from .ai_clients import (
    call_deepseek_policy, 
    call_qwen_for_component, 
    get_ai_status,
    analyze_photo_view,
    generate_update_instructions
)
from .audit import write_audit_zip
from .gate import rule_gate
from .models import OpenCVDiff, DocumentUpdateResponse
from .document_service import process_document_update


class RunRequest(BaseModel):
    """
    This API is intentionally strict: OpenCV diff results must be provided.
    Documents/images are not handled in this scaffold.
    """

    opencv_diff: OpenCVDiff
    image_verification_evidence_available: bool = False


app = FastAPI(title="DOC_GUARD", version="7.0-scaffold")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Widened for local developer convenience
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Absolute paths for reliability on Windows
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_DIR = os.path.join(BASE_DIR, "audit_out")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# Serves audit_out for downloads
if not os.path.exists(AUDIT_DIR):
    os.makedirs(AUDIT_DIR)
app.mount("/audit_out", StaticFiles(directory=AUDIT_DIR), name="audit_out")

# Serves frontend files
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": "doc_guard", "version": app.version}


@app.post("/run")
def run(req: RunRequest) -> Dict[str, Any]:
    ai_status = get_ai_status()

    # In v7.0, OpenCV is authoritative; operate only on OpenCV-provided component.
    first_component = req.opencv_diff.diffs[0].component_path
    context = f"spec={req.opencv_diff.spec_name} component={first_component}"

    qwen, qwen_err = call_qwen_for_component(component_name=first_component, context=context)
    deepseek, deepseek_err = call_deepseek_policy(context=context)

    # Any AI error leads to reject (handled by gate).
    gate = rule_gate(
        opencv=req.opencv_diff,
        ai_status=ai_status,
        qwen=qwen,
        deepseek=deepseek,
        image_verification_evidence_available=req.image_verification_evidence_available,
    )

    audit_zip = write_audit_zip(
        out_dir="audit_out",
        opencv=req.opencv_diff,
        ai_status=ai_status,
        gate=gate,
        raw_inputs={"qwen_error": qwen_err, "deepseek_error": deepseek_err, **req.model_dump()},
    )

    return {
        "status": gate.status,
        "reasons": gate.reasons,
        "audit_zip_path": audit_zip,
        "author": "Antigravity",
    }


@app.post("/update-doc", response_model=DocumentUpdateResponse)
async def update_document(
    spec_file: UploadFile = File(...),
    photo_file: UploadFile = File(...),
    template_name: str = "template.docx"
):
    """
    Main orchestration endpoint for vision-based document updates.
    1. Read uploaded files.
    2. Analyze photo for 'side view'.
    3. Compare with spec.
    4. Generate update instructions.
    5. Apply updates to document template.
    """
    try:
        # 1. Read files
        spec_content = (await spec_file.read()).decode("utf-8")
        photo_bytes = await photo_file.read()

        # 2. Vision analysis (side-view detection)
        vision_result = analyze_photo_view(photo_bytes)

        if vision_result.view_type != "side":
            return DocumentUpdateResponse(
                success=False,
                message=f"Photo is not a side view ({vision_result.view_type}). No update performed."
            )

        # 3. & 4. Logic/Comparison
        final_instructions = generate_update_instructions(spec_content, vision_result)

        # 5. Document Update
        # For prototype, we assume template.docx exists in a 'templates' folder.
        template_path = os.path.join("templates", template_name)
        output_name = f"updated_{template_name}"
        output_path = os.path.join("audit_out", output_name)

        # Create dummy template if not exists for testing
        if not os.path.exists("templates"):
            os.makedirs("templates")
        
        # Ensure output dir exists
        if not os.path.exists("audit_out"):
            os.makedirs("audit_out")

        # Mock image save for doc inclusion
        temp_image_path = os.path.join("audit_out", "latest_photo.jpg")
        with open(temp_image_path, "wb") as f:
            f.write(photo_bytes)

        # Map actions to real file paths
        for action in final_instructions.update_actions:
            if action.type == "image":
                action.new_value = temp_image_path

        # Perform the actual update
        process_document_update(template_path, output_path, final_instructions.update_actions)

        return DocumentUpdateResponse(
            success=True,
            message="Document updated successfully based on side-view analysis.",
            output_path=output_path
        )

    except Exception as e:
        return DocumentUpdateResponse(success=False, message=str(e))


import os

