from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple

from app.agents.base_agent import BaseAgent
from app.models.schemas import QueryAnalysis


_ALLOWED_LANG = {"python", "javascript", "java", "unknown"}
_ALLOWED_FW = {"fastapi", "django", "flask", "react", "unknown"}

_TOPIC_ALIASES = {
    "dependencies":          "dependency_injection",
    "dependency injection":  "dependency_injection",
    "depends":               "dependency_injection",
    "di":                    "dependency_injection",
    "auth":                  "authentication",
    "jwt":                   "authentication",
    "oauth":                 "authentication",
    "oauth2":                "authentication",
    "rest":                  "rest_api",
    "api":                   "rest_api",
    "http":                  "rest_api",
    "web socket":            "websocket",
    "ws":                    "websocket",
    "db":                    "database",
    "sql":                   "database",
    "orm":                   "database",
    "sqlalchemy":            "database",
    "background task":       "background_tasks",
    "background tasks":      "background_tasks",
    "background-tasks":      "background_tasks",
}


class QueryAnalyzerAgent(BaseAgent):
    reasoning_depth = "shallow"

    def _safe_extract_json(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()

        # 1) ```json ... ``` fenced
        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            return json.loads(fenced.group(1))

        # 2) first balanced { ... } object
        start = text.find("{")
        if start == -1:
            raise ValueError("No JSON start found")

        in_str = False
        escape = False
        depth = 0

        for i in range(start, len(text)):
            ch = text[i]

            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue

            if ch == '"':
                in_str = True
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    return json.loads(candidate)

        raise ValueError("No complete JSON object found")

    @staticmethod
    def _infer_framework_topic(query: str) -> Tuple[str, str]:
        q = (query or "").lower()
        framework = "unknown"
        topic = "unknown"

        # framework
        if "django" in q:
            framework = "django"
        elif "flask" in q:
            framework = "flask"
        elif "fastapi" in q:
            framework = "fastapi"
        elif "react" in q:
            framework = "react"

        # topic
        if "websocket" in q or "web socket" in q or re.search(r"\bws\b", q):
            topic = "websocket"
        elif "signal" in q:
            topic = "signals"
        elif any(x in q for x in ["auth", "jwt", "token", "oauth", "login"]):
            topic = "authentication"
        elif "middleware" in q:
            topic = "middleware"
        elif any(x in q for x in ["depends", "dependency", "injection", "inject"]):
            topic = "dependency_injection"
        elif any(x in q for x in ["database", "sql", "orm", "sqlalchemy"]):
            topic = "database"
        elif any(x in q for x in ["test", "pytest", "unittest"]):
            topic = "testing"
        elif any(x in q for x in ["deploy", "docker", "gunicorn", "k8s", "kubernetes"]):
            topic = "deployment"
        elif any(x in q for x in ["rest", "api", "endpoint", "http"]):
            topic = "rest_api"

        return framework, topic

    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        lang = str(data.get("language", "unknown")).strip().lower()
        fw = str(data.get("framework", "unknown")).strip().lower()
        topic = str(data.get("topic", "unknown")).strip().lower()

        # IMPORTANT: model bazen "fastapi|django|..." döndürüyor -> tek değere indir
        if "|" in fw:
            fw = fw.split("|")[0].strip()

        if lang not in _ALLOWED_LANG:
            lang = "unknown"
        if fw not in _ALLOWED_FW:
            fw = "unknown"

        if not topic or topic in {"none", "short_main_topic", "main_topic", "topic"}:
            topic = "unknown"

        topic = _TOPIC_ALIASES.get(topic, topic)

        subtopic = data.get("subtopic")
        if subtopic is not None:
            subtopic = str(subtopic).strip().lower()
            if subtopic in {"", "none", "null"}:
                subtopic = None

        keywords = data.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []
        keywords = [str(k).strip().lower() for k in keywords if str(k).strip()]
        keywords = keywords[:8]

        return {
            "language": lang,
            "framework": fw,
            "topic": topic,
            "subtopic": subtopic,
            "keywords": keywords,
        }

    async def execute(self, input_data: Any) -> Dict[str, Any]:
        query = input_data if isinstance(input_data, str) else str(input_data)
        query = query.strip()

        if not query:
            qa = QueryAnalysis(
                language="python",
                framework="unknown",
                topic="unknown",
                subtopic=None,
                keywords=[],
            )
            return qa.model_dump()

        model = self._get_model("classify", len(query))

        prompt = f"""
You are a query analyzer agent.

Return ONLY valid JSON that EXACTLY matches this schema:
{{
  "language": "python|javascript|java|unknown",
  "framework": "fastapi|django|flask|react|unknown",
  "topic": "websocket",
  "subtopic": null,
  "keywords": ["3-8 search keywords"]
}}

The "topic" field above shows an EXAMPLE value ("websocket").
You MUST replace it with the actual topic from the query below.
Good topic values: "websocket", "rest_api", "dependency_injection",
"authentication", "middleware", "database", "routing", "testing", "deployment".

STRICT RULES:
- Return ONLY JSON (no markdown, no extra text).
- All values MUST be lowercase.
- "framework" MUST be ONE value only (not a list, not 'a|b|c').
- "topic" MUST describe the actual subject — NEVER return "short_main_topic".
- If you are unsure about framework, use "unknown".

Query: {query}
""".strip()

        raw = self.llm.generate(prompt, model=model, temperature=0.0)

        try:
            data = self._safe_extract_json(raw)
            data = self._sanitize(data)

            # HARD GUARANTEE: LLM boş/unknown döndürse bile query’den tamamla
            fw2, tp2 = self._infer_framework_topic(query)
            if data.get("framework") in (None, "", "unknown") and fw2 != "unknown":
                data["framework"] = fw2
            if data.get("topic") in (None, "", "unknown") and tp2 != "unknown":
                data["topic"] = tp2

            validated = QueryAnalysis.model_validate(data)
            return validated.model_dump()

        except Exception:
            # fallback heuristics (stable & predictable)
            fw2, tp2 = self._infer_framework_topic(query)

            low = query.lower()
            _KEYWORD_POOL = [
                "fastapi", "django", "flask", "react",
                "websocket", "authentication", "jwt", "token",
                "dependency", "injection", "rest", "api",
                "middleware", "database", "sql", "orm",
                "endpoint", "route", "http", "async",
            ]
            keywords = [k for k in _KEYWORD_POOL if k in low]
            if not keywords:
                keywords = [fw2] if fw2 != "unknown" else ["python"]

            qa = QueryAnalysis(
                language="python",
                framework=fw2,
                topic=tp2,
                subtopic=None,
                keywords=keywords[:8],
            )
            return qa.model_dump()
