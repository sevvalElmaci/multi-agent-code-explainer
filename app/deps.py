from app.services.llm_service import LLMService
from app.services.model_selector import ModelSelector
from app.services.rag_service import RAGService
from app.tools.web_search import WebSearchTool
from app.tools.code_validator import CodeValidatorTool
from app.tools.complexity_analyzer import ComplexityAnalyzerTool

from app.agents.query_analyzer import QueryAnalyzerAgent
from app.agents.documentation_reader import DocumentationReaderAgent
from app.agents.example_finder import ExampleFinderAgent
from app.agents.code_explainer import CodeExplainerAgent

from app.orchestrator.workflow import AgentOrchestrator
from sentence_transformers import SentenceTransformer
from app.config import settings

def build_orchestrator() -> AgentOrchestrator:
    llm = LLMService()
    selector = ModelSelector()

    embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    rag = RAGService(embedding_model=embedding_model)
    web = WebSearchTool()

    agents = {
        "query_analyzer": QueryAnalyzerAgent(llm, selector),
        "doc_reader": DocumentationReaderAgent(llm, selector, rag),
        "example_finder": ExampleFinderAgent(llm, selector, web),
        "code_explainer": CodeExplainerAgent(llm, selector),
    }

    tools = {
        "code_validator": CodeValidatorTool(),
        "complexity_analyzer": ComplexityAnalyzerTool(),
    }

    return AgentOrchestrator(agents, tools)
