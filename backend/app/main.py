"""
AI Why? Engine — FastAPI Application Entrypoint
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.explain import router as explain_router

app = FastAPI(
    title="AI Why? Engine API",
    description="Interactive AI explainability and causal diagnostic reasoning platform with Hybrid RAG.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(explain_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-why-engine",
        "version": "1.0.0",
        "rag_status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
