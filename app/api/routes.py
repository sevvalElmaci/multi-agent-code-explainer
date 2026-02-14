from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import QueryRequest, QueryResponse

router = APIRouter()

@router.post("/ask", response_model=QueryResponse)
async def ask(request: Request, payload: QueryRequest):
    try:
        orchestrator = request.app.state.orchestrator
        result = await orchestrator.process_query(payload.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    return {"status": "ok"}
