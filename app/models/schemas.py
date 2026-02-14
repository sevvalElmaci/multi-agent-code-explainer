from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


# -----------------------
# API Boundary Models
# -----------------------
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User technical question")


class QueryResponse(BaseModel):
    explanation: str
    code_example: str = ""
    line_by_line: List[str] = []
    best_practices: List[str] = []
    sources: List[str] = []
    meta: Optional[Dict[str, Any]] = None


# -----------------------
# Agent Contracts
# -----------------------
class QueryAnalysis(BaseModel):
    language: str = Field(..., description="Programming language, e.g. python")
    framework: str = Field(..., description="Framework/library, e.g. fastapi")
    topic: str = Field(..., description="Main topic, e.g. websocket")
    subtopic: Optional[str] = Field(None, description="Subtopic, e.g. authentication")
    keywords: List[str] = Field(default_factory=list, description="Search keywords 3-8 items")


class DocSnippet(BaseModel):
    source: str
    text: str
    relevance: float = Field(..., ge=0.0, le=1.0)


class DocumentationResult(BaseModel):
    snippets: List[DocSnippet] = Field(default_factory=list)
    meta: Optional[Dict[str, Any]] = None  # e.g., {"index":"local_docs", "top_k":3}


class WebResult(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class ExampleFinderResult(BaseModel):
    results: List[WebResult] = Field(default_factory=list)
    code_example: str = ""  # best candidate extracted (if any)
    meta: Optional[Dict[str, Any]] = None  # e.g., {"query":"...", "provider":"ddg"}


# -----------------------
# Tool Contracts
# -----------------------
class CodeValidationResult(BaseModel):
    valid: bool
    error: Optional[str] = None


class ComplexityResult(BaseModel):
    cyclomatic_complexity: Optional[int] = None
    rank: Optional[str] = None
    loc: Optional[int] = None


# -----------------------
# Final Aggregation Contract
# -----------------------
class FinalAnswer(BaseModel):
    explanation: str
    code_example: str = ""
    line_by_line: List[str] = Field(default_factory=list)
    best_practices: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    meta: Optional[Dict[str, Any]] = None
