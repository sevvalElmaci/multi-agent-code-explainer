from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.models.schemas import ExampleFinderResult, WebResult

# Kod içerdiğine dair güvenilir sinyaller
_CODE_SIGNALS = [
    "def ", "class ", "import ", "from ", "async def ",
    "@app.", "=>", "const ", "return ", "await ",
    "function ", "export ", "module.", "require(",
]


class ExampleFinderAgent(BaseAgent):
    reasoning_depth = "shallow"

    def __init__(self, llm_service: Any, model_selector: Any, web_search_tool: Any):
        super().__init__(llm_service, model_selector)
        self.web = web_search_tool

    def _extract_best_code_snippet(self, results_raw: List[Dict]) -> str:
        """
        Web sonuçlarının snippet alanlarını tarar.
        Kod sinyali içeren ilk snippet'i döndürür.
        Hiçbirinde kod yoksa en uzun snippet'i döndürür (LLM için en iyi bağlam).
        """
        best_with_code: Optional[str] = None
        longest: str = ""

        for r in results_raw:
            snippet = (r.get("body") or r.get("snippet") or "").strip()
            if not snippet:
                continue

            # Kod sinyali var mı?
            if best_with_code is None and any(sig in snippet for sig in _CODE_SIGNALS):
                best_with_code = snippet

            # En uzun snippet'i de takip et (fallback için)
            if len(snippet) > len(longest):
                longest = snippet

        return best_with_code or longest

    async def execute(self, input_data: Any) -> Dict[str, Any]:
        analysis = input_data if isinstance(input_data, dict) else {}
        keywords = analysis.get("keywords", [])
        framework = analysis.get("framework", "unknown")
        topic = analysis.get("topic", "unknown")
        subtopic = analysis.get("subtopic")

        q = " ".join(keywords) if keywords else f"{framework} {topic}"
        if subtopic:
            q += f" {subtopic}"
        q += " github example"

        results_raw = self.web.search(q, max_results=5)  # list[dict]
        results: List[WebResult] = []

        for r in results_raw or []:
            results.append(
                WebResult(
                    title=r.get("title", ""),
                    url=r.get("href") or r.get("url") or "",
                    snippet=(r.get("body") or r.get("snippet") or "")
                )
            )

        # BUG 1 FIX: snippet'lardan en iyi kod adayını çıkar
        code_example = self._extract_best_code_snippet(results_raw or [])

        # Bonus: CodeExplainer'ın sources'a yazabilmesi için URL'leri meta'ya ekle
        source_urls = [r.url for r in results if r.url]

        out = ExampleFinderResult(
            results=results,
            code_example=code_example,
            meta={
                "query": q,
                "provider": "duckduckgo",
                "urls": source_urls,   # Bug 5 fix için hazır
            },
        )
        return out.model_dump()