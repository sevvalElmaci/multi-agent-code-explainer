# app/tools/web_search.py
from __future__ import annotations

from typing import Any, Dict, List
import logging
import time

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class WebSearchTool:
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        # Hızlı koruma: boş query vs
        q = (query or "").strip()
        if not q:
            return []

        # Rate limit yiyorsan max_results'i de küçük tut (3-5 ideal)
        max_results = max(1, min(int(max_results), 5))

        for attempt in range(3):  # 3 deneme: 0,1,2
            try:
                results: List[Dict[str, Any]] = []
                with DDGS() as ddgs:
                    # ✅ backend="lite" çoğu ortamda daha stabil
                    for r in ddgs.text(q, max_results=max_results, backend="lite"):
                        results.append(
                            {
                                "title": r.get("title", "") or "",
                                "url": r.get("href", "") or "",
                                "snippet": r.get("body", "") or "",
                            }
                        )
                return results

            except Exception as e:
                msg = str(e).lower()
                is_rate = any(x in msg for x in ["ratelimit", "rate limit", "too many requests", "429"])
                if is_rate:
                    wait = 2 ** attempt  # 1,2,4 sn
                    logger.warning("DuckDuckGo rate limit (attempt %s). Waiting %ss...", attempt + 1, wait)
                    time.sleep(wait)
                    continue

                logger.error("Web search failed", exc_info=True)
                return []

        # 3 denemede de ratelimit → web’siz devam
        logger.warning("DuckDuckGo rate limit persists. Continuing without web results.")
        return []
