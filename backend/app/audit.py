from __future__ import annotations

import hashlib
import json
import os
import time
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .models import AiStatus, GateResult, OpenCVDiff


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def sha256_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(payload)


def write_audit_zip(
    *,
    out_dir: str,
    opencv: OpenCVDiff,
    ai_status: AiStatus,
    gate: GateResult,
    raw_inputs: Dict[str, Any],
) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    zip_path = os.path.join(out_dir, f"audit-{ts}.zip")

    opencv_payload = opencv.model_dump()
    gate_payload = gate.model_dump()
    ai_status_payload = ai_status.model_dump()

    manifest = {
        "ts": ts,
        "spec_name": opencv.spec_name,
        "spec_diff_hash": opencv.spec_diff_hash,
        "computed_opencv_hash": sha256_json(opencv_payload),
        "ai_status": ai_status_payload,
        "final_status": gate.status,
        "reasons": gate.reasons,
        "hashes": {},
    }

    def _writestr(z: zipfile.ZipFile, arcname: str, data: bytes) -> None:
        z.writestr(arcname, data)
        manifest["hashes"][arcname] = sha256_bytes(data)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        _writestr(z, "inputs/opencv_diff.json", json.dumps(opencv_payload, indent=2, ensure_ascii=False).encode("utf-8"))
        _writestr(z, "inputs/raw_request.json", json.dumps(raw_inputs, indent=2, ensure_ascii=False).encode("utf-8"))
        _writestr(z, "ai/ai_status.json", json.dumps(ai_status_payload, indent=2, ensure_ascii=False).encode("utf-8"))
        _writestr(z, "decisions/gate_result.json", json.dumps(gate_payload, indent=2, ensure_ascii=False).encode("utf-8"))
        _writestr(z, "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"))

    return zip_path

