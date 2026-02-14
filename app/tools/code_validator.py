import ast
from typing import Dict, Any


class CodeValidatorTool:
    def validate(self, code: str) -> Dict[str, Any]:
        if not code or not code.strip():
            return {"valid": False, "error": "Empty code", "line": None, "offset": None}

        try:
            ast.parse(code)
            return {"valid": True, "error": None, "line": None, "offset": None}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": getattr(e, "lineno", None),
                "offset": getattr(e, "offset", None),
            }
