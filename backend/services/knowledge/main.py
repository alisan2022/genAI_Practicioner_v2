from __future__ import annotations

from fastapi import FastAPI

from backend.services.shared.knowledge_base import DOCUMENTS, retrieve_documents
from backend.services.shared.schemas import KnowledgeRetrieveRequest, KnowledgeRetrieveResponse

app = FastAPI(title="Knowledge Service")


@app.get("/health")
def health() -> dict[str, int | str]:
    return {"status": "ok", "service": "knowledge", "documents": len(DOCUMENTS)}


@app.post("/retrieve", response_model=KnowledgeRetrieveResponse)
def retrieve(request: KnowledgeRetrieveRequest) -> KnowledgeRetrieveResponse:
    return KnowledgeRetrieveResponse(
        cards=retrieve_documents(
            request.query,
            urgency=request.urgency,
            top_k=request.top_k,
        )
    )
