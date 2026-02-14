from __future__ import annotations

import codecs
import json
import re
from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.models.schemas import FinalAnswer


class CodeExplainerAgent(BaseAgent):
    reasoning_depth = "deep"

    # -------------------------
    # JSON extraction utilities
    # -------------------------
    def _safe_extract_json(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()

        # 1) ```json ... ``` fenced block varsa
        fenced = re.search(
            r"```json\s*(\{.*?\})\s*```",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if fenced:
            return json.loads(fenced.group(1))

        # 2) Metin içinde ilk "dengeli" { ... } JSON objesini bul
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

    # -------------------------
    # Context formatting
    # -------------------------
    def _format_doc_snippets(self, snippets: list) -> str:
        lines = []
        for s in (snippets or [])[:3]:
            if isinstance(s, dict):
                source = s.get("source", "docs")
                text = s.get("text", "")
            else:
                source = getattr(s, "source", "docs")
                text = getattr(s, "text", "")
            if text and str(text).strip():
                lines.append(f"[Source: {source}]\n{str(text).strip()}")
        return "\n\n---\n\n".join(lines) if lines else "No documentation found."

    def _format_web_results(self, results: list) -> str:
        lines = []
        for i, r in enumerate((results or [])[:3], 1):
            if isinstance(r, dict):
                title = r.get("title", "No title")
                url = r.get("url", "")
                snippet = r.get("snippet", "")
            else:
                title = getattr(r, "title", "No title")
                url = getattr(r, "url", "")
                snippet = getattr(r, "snippet", "") or ""
            lines.append(f"[{i}] {title}\nURL: {url}\n{str(snippet).strip()}")
        return "\n\n".join(lines) if lines else "No web results found."

    # -------------------------
    # Escape decoding (fixes \\u003c etc)
    # -------------------------
    def _decode_double_escapes(self, s: str) -> str:
        """
        Model bazen stringleri double-escape döndürüyor:
        "\\u003c" gibi. UI'da bunlar görünüyor.
        Burada unicode_escape ile çözmeye çalışıyoruz.
        """
        if not isinstance(s, str) or not s:
            return s

        # Eğer literal backslash-u görüyorsak decode et
        if "\\u" in s or "\\n" in s or "\\t" in s or "\\r" in s:
            try:
                s = codecs.decode(s, "unicode_escape")
            except Exception:
                pass

        # Son bir normalize
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        return s

    async def execute(self, input_data: Any) -> Dict[str, Any]:
        payload = input_data if isinstance(input_data, dict) else {}

        query = payload.get("query", "")
        analysis = payload.get("analysis", {}) or {}
        documentation = payload.get("documentation", {}) or {}
        examples = payload.get("examples", {}) or {}
        validation = payload.get("validation", {}) or {}
        complexity = payload.get("complexity", {}) or {}

        topic = (analysis.get("topic") or "unknown").strip()
        framework = (analysis.get("framework") or "unknown").strip()

        model = self._get_model("explain", len(query) + 500)

        doc_context = self._format_doc_snippets(documentation.get("snippets", []) or [])
        web_context = self._format_web_results(examples.get("results", []) or [])

        _CODE_RULES = {
            "websocket": (
                "code_example MUST include: WebSocket route (@app.websocket), "
                "websocket.accept(), receive_text(), send_text(), WebSocketDisconnect handler."
            ),
            "dependency_injection": (
                "code_example MUST include: a dependency function, Depends() in a route parameter, "
                "and at least one route that uses the dependency."
            ),
            "authentication": (
                "code_example MUST include: token/JWT validation, a protected route, "
                "HTTPException with 401 status for unauthorized access."
            ),
            "rest_api": (
                "code_example MUST include: FastAPI(), at least one HTTP route "
                "(@app.get or @app.post), proper return value or Pydantic model."
            ),
            "middleware": (
                "code_example MUST include: @app.middleware decorator or "
                "app.add_middleware(), request/response handling."
            ),
            "database": (
                "code_example MUST include: database session setup, "
                "a model definition, and a route that queries the database."
            ),
        }
        code_rule = _CODE_RULES.get(
            topic,
            f"code_example MUST be a complete, self-contained {framework} example that directly answers the user question."
        )

        prompt = f"""
You are a senior software engineer and teacher.

User question:
{query}

Context (official documentation snippets):
{doc_context}

Context (web results):
{web_context}

Code validation result:
{validation}

Complexity info:
{complexity}

Return ONLY valid JSON in this schema:
{{
  "explanation": "2-3 sentence explanation of the concept",
  "code_example": "complete runnable python code here",
  "line_by_line": [
    "Line 1 does X because Y",
    "Line 2 does X because Y"
  ],
  "best_practices": [
    "Always do X to avoid Y",
    "Use Z when W"
  ],
  "sources": ["https://actual-url.com"],
  "meta": {{"framework": "{framework}", "topic": "{topic}"}}
}}

Rules:
- No extra text, only JSON.
- NEVER copy the example values above — replace them with real content.
- code_example MUST be a complete, runnable {framework} example relevant to: {topic}.
- {code_rule}
- line_by_line MUST have at least 6 items.
- best_practices MUST have at least 4 items.
- sources MUST contain real URLs from the web results context above.
""".strip()

        raw = self.llm.generate(prompt, model=model, temperature=0.1)
        print("RAW MODEL OUTPUT:\n", raw)

        # ---------- PARSE + REPAIR (never crash) ----------
        try:
            data = self._safe_extract_json(raw)
        except Exception:
            repair_prompt = f"""Convert the content below into VALID JSON that EXACTLY matches this schema.
Return ONLY JSON. No markdown. No extra keys.
IMPORTANT:
- Use ONLY double quotes for JSON strings.
- Escape inner quotes as \\"
- Do NOT put raw newlines inside JSON strings; use \\n instead.

Schema:
{{
  "explanation": "2-3 sentence explanation",
  "code_example": "python code as a string",
  "line_by_line": ["bullets"],
  "best_practices": ["bullets"],
  "sources": ["urls"],
  "meta": {{"framework": "{framework}", "topic": "{topic}"}}
}}

Content:
{raw}
"""
            raw2 = self.llm.generate(repair_prompt, model=model, temperature=0.0)
            print("REPAIRED MODEL OUTPUT:\n", raw2)

            try:
                data = self._safe_extract_json(raw2)
            except Exception:
                hard_repair = f"""Return STRICT VALID MINIFIED JSON ONLY (one JSON object).
Rules:
- Use ONLY double quotes.
- Escape all inner quotes as \\"
- Replace all newlines in strings with \\n
- No trailing commas.
- Keys MUST be exactly:
  explanation, code_example, line_by_line, best_practices, sources, meta

framework="{framework}"
topic="{topic}"

Content:
{raw2}
"""
                raw3 = self.llm.generate(hard_repair, model=model, temperature=0.0)
                print("HARD REPAIRED OUTPUT:\n", raw3)

                try:
                    data = self._safe_extract_json(raw3)
                except Exception:
                    data = {
                        "explanation": "Could not parse model output into valid JSON. Please retry.",
                        "code_example": "",
                        "line_by_line": [],
                        "best_practices": [],
                        "sources": [],
                        "meta": {"framework": framework, "topic": topic},
                    }

        # ---------- NORMALIZE ----------
        if not isinstance(data, dict):
            data = {}

        _PLACEHOLDERS = {
            "bullets",
            "line-by-line explanation bullets",
            "best practice bullets",
            "line by line explanation",
            "explanation bullets",
            "best practices",
            "list of urls or source names",
            "urls or names",
        }

        def _is_placeholder(s: str) -> bool:
            return (not isinstance(s, str)) or (not s.strip()) or (s.strip().lower() in _PLACEHOLDERS)

        # ---- explanation (robust fallback) ----
        expl = data.get("explanation")
        if _is_placeholder(expl) or ("could not parse model output" in str(expl).lower()):
            _FALLBACK_EXPLANATION = {
                "websocket": "WebSocket, istemci ve sunucu arasında çift yönlü ve sürekli bir bağlantı kurar. FastAPI’de @app.websocket ile endpoint açıp accept/receive/send akışını yönetirsin.",
                "authentication": "Authentication, API’ye erişen kullanıcının kimliğini doğrulama sürecidir. Genelde Bearer token/JWT ile isteklerde doğrulama yapılır ve yetkisizse 401 döndürülür.",
                "rest_api": "REST API, HTTP metodları (GET/POST/PUT/DELETE) ile kaynaklara erişim yaklaşımıdır. Framework’te route tanımlayıp JSON response döndürerek kurarsın.",
                "dependency_injection": "Dependency Injection, ortak ihtiyaçları (DB session, auth, config) route’lara Depends() gibi mekanizmalarla enjekte etmektir. Kod tekrarını azaltır ve test etmeyi kolaylaştırır.",
            }
            data["explanation"] = _FALLBACK_EXPLANATION.get(
                topic,
                f"{framework} için bu konuda açıklama üretilemedi; örnek kod ve maddeler sağlandı."
            )
        else:
            data["explanation"] = str(expl).strip()

        # ---- best_practices ----
        bp = data.get("best_practices")
        if isinstance(bp, dict):
            bp = [str(v) for v in bp.values()]
        if not isinstance(bp, list):
            bp = []
        bp = [s for s in bp if isinstance(s, str) and not _is_placeholder(s)]
        if len(bp) < 4:
            bp.extend(
                [
                    "Handle disconnects and exceptions gracefully.",
                    "Avoid blocking calls; keep handlers async-friendly.",
                    "Add rate limiting / connection limits for safety.",
                    "Use clear message formats (e.g., JSON messages) for clients.",
                ][: max(0, 4 - len(bp))]
            )
        data["best_practices"] = bp

        # ---- line_by_line ----
        lbl = data.get("line_by_line")
        if not isinstance(lbl, list):
            lbl = []
        lbl = [s for s in lbl if isinstance(s, str) and not _is_placeholder(s)]

        _FALLBACK_LINE_BY_LINE = {
            "websocket": [
                "Create the app instance with app = FastAPI().",
                "Define a WebSocket route with @app.websocket('/ws').",
                "Accept the incoming connection with await websocket.accept().",
                "Receive messages using await websocket.receive_text().",
                "Send responses using await websocket.send_text(...).",
                "Handle disconnects with WebSocketDisconnect exception.",
            ],
            "dependency_injection": [
                "Define a dependency function that returns what you need.",
                "Use Depends(your_dependency) to inject it into a route.",
                "FastAPI runs the dependency before the route handler.",
                "Dependencies can be nested (dependency depends on another).",
                "Use yield for setup/teardown (e.g., DB session close).",
                "Use async dependencies for I/O operations.",
            ],
            "rest_api": [
                "Create the app instance.",
                "Define routes with method decorators.",
                "Use path params for resource IDs.",
                "Use query params for optional filters.",
                "Return dict/Pydantic model so it serializes to JSON.",
                "Raise HTTPException for proper HTTP error codes.",
            ],
            "authentication": [
                "Define a security scheme (Bearer/API key/OAuth2).",
                "Create a function to read and validate the token.",
                "Protect routes by injecting the dependency.",
                "Return 401 when invalid/missing credentials.",
                "Never store plaintext passwords; hash them.",
                "Use short-lived tokens + refresh tokens.",
            ],
        }

        if len(lbl) < 6:
            topic_key = "dependency_injection" if topic == "dependencies" else topic
            fallback_lbl = _FALLBACK_LINE_BY_LINE.get(topic_key, [
                f"Import the necessary {framework} modules.",
                "Initialize the application instance.",
                "Define the core handler logic.",
                "Handle inputs and validation.",
                "Return the appropriate response.",
                "Add error handling.",
            ])
            lbl.extend(fallback_lbl[: max(0, 6 - len(lbl))])

        data["line_by_line"] = lbl

        # ---- code_example (dict normalize + double-escape decode + fallback) ----
        _FALLBACK_CODE = {
            "websocket": """from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"echo: {msg}")
    except WebSocketDisconnect:
        pass

# Run: uvicorn main:app --reload
""",
            "rest_api": """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

items: dict[int, dict] = {}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]

@app.post("/items/{item_id}")
def create_item(item_id: int, item: Item):
    items[item_id] = item.model_dump()
    return items[item_id]

# Run: uvicorn main:app --reload
""",
            "authentication": """from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str) -> str:
    if token != "secret-token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return "user@example.com"

@app.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    return {"user": user, "message": "Access granted"}

# Run: uvicorn main:app --reload
""",
        }

        ce = data.get("code_example")
        if isinstance(ce, dict):
            ce = ce.get("code") or ce.get("content") or ""

        if not isinstance(ce, str) or not ce.strip():
            ce = _FALLBACK_CODE.get(
                topic,
                f"# No fallback example available for topic: {topic}\n# Please refer to the {framework} documentation."
            )

        ce = self._decode_double_escapes(ce)
        ce = ce.replace("\r\n", "\n").strip()
        data["code_example"] = ce

        # ---- sources: guarantee urls ----
        _FALLBACK_DOCS = {
            "fastapi": "https://fastapi.tiangolo.com",
            "django": "https://docs.djangoproject.com",
            "flask": "https://flask.palletsprojects.com",
            "react": "https://react.dev",
        }

        guaranteed_urls = []
        for r in (examples.get("results") or [])[:3]:
            url = r.get("url", "") if isinstance(r, dict) else getattr(r, "url", "")
            if isinstance(url, str) and url.startswith("http"):
                guaranteed_urls.append(url)

        for url in (examples.get("meta") or {}).get("urls", []):
            if isinstance(url, str) and url.startswith("http") and url not in guaranteed_urls:
                guaranteed_urls.append(url)

        if not guaranteed_urls:
            guaranteed_urls.append(_FALLBACK_DOCS.get(framework, "https://docs.python.org"))

        src = data.get("sources")
        if not isinstance(src, list):
            src = []
        clean_llm_sources = [s for s in src if isinstance(s, str) and s.startswith("http") and not _is_placeholder(s)]

        seen = set()
        merged = []
        for url in clean_llm_sources + guaranteed_urls:
            if url not in seen:
                seen.add(url)
                merged.append(url)
        data["sources"] = merged

        # ---- meta ----
        data.setdefault("meta", {})
        if not isinstance(data["meta"], dict):
            data["meta"] = {}
        data["meta"].setdefault("framework", framework)
        data["meta"].setdefault("topic", topic)

        final = FinalAnswer.model_validate(data)
        print("FINAL JSON:", final.model_dump())
        return final.model_dump()
