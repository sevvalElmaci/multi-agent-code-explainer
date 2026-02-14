from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.models.schemas import DocumentationResult, DocSnippet


class DocumentationReaderAgent(BaseAgent):
    reasoning_depth = "deep"

    def __init__(self, llm_service: Any, model_selector: Any, rag_service: Any):
        super().__init__(llm_service, model_selector)
        self.rag = rag_service

    async def execute(self, input_data: Any) -> Dict[str, Any]:
        """
        input_data: QueryAnalysis dict
        output: DocumentationResult dict
        """
        analysis = input_data if isinstance(input_data, dict) else {}
        keywords = analysis.get("keywords", [])
        topic = analysis.get("topic", "unknown")

        # RAG query: keywords + topic
        rag_query = " ".join(keywords) if keywords else str(topic)

        # rag_service.search(query) -> list of records/snippets
        # Senin rag_service'in dönüş formatı farklıysa burayı uyarlayacağız.
        hits = self.rag.search(rag_query)

        snippets = []
        for h in hits or []:
            # beklenen: {"source": "...", "text": "...", "score": ...} gibi
            source = h.get("source") or h.get("file") or "local_docs"
            text = h.get("text") or h.get("chunk") or ""
            # relevance normalize: eğer score zaten 0-1 değilse 0.0 ver
            rel = h.get("relevance")
            if rel is None:
                rel = h.get("score")
            try:
                rel = float(rel)
                if rel < 0 or rel > 1:
                    rel = 0.0
            except Exception:
                rel = 0.0

            if text.strip():
                snippets.append(DocSnippet(source=source, text=text, relevance=rel))

        result = DocumentationResult(
            snippets=snippets,
            meta={"query": rag_query, "top_k": len(snippets), "source": "faiss"},
        )
        return result.model_dump()
