# app/services/model_selector.py
from __future__ import annotations

from app.config import settings


class ModelSelector:
    """
    Basit ama iş gören routing:
    - classify / kısa işler -> FAST
    - explain / deep / uzun input -> POWERFUL
    """

    @staticmethod
    def select_model(task_type: str, input_length: int, reasoning_depth: str) -> str:
        task_type = (task_type or "").lower()
        reasoning_depth = (reasoning_depth or "shallow").lower()

        # Agent bazlı net kural (en garantisi)
        if reasoning_depth == "deep":
            return settings.POWERFUL_MODEL

        if task_type in {"explain", "synthesize", "write"}:
            return settings.POWERFUL_MODEL

        # input çok uzunsa güçlü modele çık
        if input_length >= 1200:
            return settings.POWERFUL_MODEL

        return settings.FAST_MODEL
