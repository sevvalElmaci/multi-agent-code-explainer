from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    reasoning_depth: str = "shallow"  # shallow | deep

    def __init__(self, llm_service: Any, model_selector: Any):
        self.llm = llm_service
        self.selector = model_selector

    def _get_model(self, task_type: str, input_length: int) -> str:
        return self.selector.select_model(
            task_type=task_type,
            input_length=input_length,
            reasoning_depth=self.reasoning_depth,
        )

    @abstractmethod
    async def execute(self, input_data: Any) -> Dict[str, Any]:
        raise NotImplementedError
