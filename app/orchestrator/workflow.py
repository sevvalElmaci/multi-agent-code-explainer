# app/orchestrator/workflow.py
import asyncio
from typing import Any, Dict

from app.models.schemas import (
    QueryAnalysis,
    DocumentationResult,
    ExampleFinderResult,
    CodeValidationResult,
    ComplexityResult,
    FinalAnswer,
)


class AgentOrchestrator:
    def __init__(self, agents: Dict[str, Any], tools: Dict[str, Any]):
        self.agents = agents
        self.tools = tools

    async def process_query(self, query: str) -> Dict[str, Any]:
        # 1) Agent 1 - analyze (validate contract)
        raw_analysis = await self.agents["query_analyzer"].execute(query)
        analysis = QueryAnalysis.model_validate(raw_analysis).model_dump()

        # 2) Agent 2 & 3 parallel (validate contracts)
        doc_task = self.agents["doc_reader"].execute(analysis)
        ex_task = self.agents["example_finder"].execute(analysis)
        raw_doc_res, raw_ex_res = await asyncio.gather(doc_task, ex_task)

        doc_res = DocumentationResult.model_validate(raw_doc_res).model_dump()
        ex_res = ExampleFinderResult.model_validate(raw_ex_res).model_dump()

        # 3) Tools - validate + complexity (validate contracts)

        # BUG 6 FIX: validator'a temiz Python kodu gönder
        # example_finder snippet'ı ```python ... ``` ile sarılı gelebilir — soy
        def _strip_fenced(code: str) -> str:
            code = (code or "").strip()
            if code.startswith("```"):
                lines = code.splitlines()
                inner = [l for l in lines if not l.strip().startswith("```")]
                return "\n".join(inner).strip()
            return code

        code_candidate = _strip_fenced(ex_res.get("code_example", "") or "")

        # Hala boşsa doc snippet'lardan kod içeren bir parça dene
        if not code_candidate:
            for snip in doc_res.get("snippets", []):
                text = snip.get("text", "") if isinstance(snip, dict) else getattr(snip, "text", "")
                if any(sig in text for sig in ("def ", "import ", "class ", "@app.")):
                    code_candidate = text.strip()
                    break

        raw_val = self.tools["code_validator"].validate(code_candidate)
        val = CodeValidationResult.model_validate(raw_val).model_dump()

        if val.get("valid"):
            raw_cx = self.tools["complexity_analyzer"].analyze(code_candidate)
        else:
            raw_cx = {}  # boş -> schema Optional alanlar ile sorunsuz geçer

        cx = ComplexityResult.model_validate(raw_cx).model_dump()

        # 4) Agent 4 - final (validate contract)
        raw_final = await self.agents["code_explainer"].execute(
            {
                "query": query,
                "analysis": analysis,
                "documentation": doc_res,
                "examples": ex_res,
                "validation": val,
                "complexity": cx,
            }
        )

        final = FinalAnswer.model_validate(raw_final)
        return final.model_dump()