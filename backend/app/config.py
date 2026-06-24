from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    """
    Conservative defaults:
    - AI calls are disabled unless explicitly enabled later.
    - Fail-closed is enforced by gate logic, not config flags.
    """

    qwen_enabled: bool = False
    deepseek_enabled: bool = False


settings = Settings()

