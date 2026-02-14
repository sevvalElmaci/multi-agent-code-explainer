from typing import Dict, Any

try:
    from radon.complexity import cc_visit
except Exception:
    cc_visit = None


class ComplexityAnalyzerTool:
    def analyze(self, code: str) -> Dict[str, Any]:
        if not code or not code.strip():
            return {"available": True, "avg_cc": 0.0, "max_cc": 0, "blocks": []}

        if cc_visit is None:
            return {"available": False, "error": "radon not installed", "avg_cc": None, "max_cc": None, "blocks": []}

        blocks = cc_visit(code)
        if not blocks:
            return {"available": True, "avg_cc": 0.0, "max_cc": 0, "blocks": []}

        ccs = [b.complexity for b in blocks]
        return {
            "available": True,
            "avg_cc": sum(ccs) / len(ccs),
            "max_cc": max(ccs),
            "blocks": [{"name": b.name, "cc": b.complexity, "line": b.lineno} for b in blocks],
        }
