#!/usr/bin/env python
"""
Application Runner with Beautiful Startup Banner
"""
import uvicorn
from app.config import settings


def print_banner():
    """Print startup banner with system info"""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🤖 Multi-Agent Code Explainer                              ║
║                                                              ║
║  Version: {settings.APP_VERSION:<48} ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🚀 Starting Application...

📍 Server Configuration:
   • Host: {settings.API_HOST}
   • Port: {settings.API_PORT}
   • Prefix: {settings.API_PREFIX}

🤖 Model Configuration:
   • Fast Model: {settings.FAST_MODEL}
   • Powerful Model: {settings.POWERFUL_MODEL}
   • Ollama URL: {settings.OLLAMA_BASE_URL}

📚 RAG Configuration:
   • Embedding Model: {settings.EMBEDDING_MODEL}
   • Documents Path: {settings.DOCUMENTS_PATH}
   • Vector DB Path: {settings.VECTOR_DB_PATH}
   • Chunk Size: {settings.CHUNK_SIZE}
   • Top-K Results: {settings.TOP_K_RESULTS}

🌐 Access URLs:
   • Local:        http://localhost:{settings.API_PORT}
   • Network:      http://{settings.API_HOST}:{settings.API_PORT}
   • API Base:     http://localhost:{settings.API_PORT}{settings.API_PREFIX}
   • Health Check: http://localhost:{settings.API_PORT}{settings.API_PREFIX}/health

📖 API Documentation:
   • Swagger UI:   http://localhost:{settings.API_PORT}/docs
   • ReDoc:        http://localhost:{settings.API_PORT}/redoc
   • OpenAPI JSON: http://localhost:{settings.API_PORT}/openapi.json

💡 Quick Test:
   curl -X POST "http://localhost:{settings.API_PORT}{settings.API_PREFIX}/ask" \\
     -H "Content-Type: application/json" \\
     -d '{{"query": "How to use WebSocket in FastAPI?"}}'

🎨 Frontend (run separately):
   streamlit run frontend/app.py

⚡ Press CTRL+C to stop the server

════════════════════════════════════════════════════════════════
"""
    print(banner)


def main():
    """Run the application with uvicorn"""
    print_banner()

    # Run uvicorn with live reload in debug mode
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()