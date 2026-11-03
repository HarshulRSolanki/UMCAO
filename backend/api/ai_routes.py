"""Gemini AI Explanation API Routes for UMCAO.

Endpoints:
- POST /api/ai/explain
- POST /api/ai/explain-line-by-line
- POST /api/ai/explain-algorithm
- POST /api/ai/explain-interview
- POST /api/ai/explain-optimization
- POST /api/ai/chat
"""

from fastapi import APIRouter, HTTPException, status
from models.schemas import (
    AIExplainRequest,
    AIExplainResponse,
    AIChatRequest,
    AIChatResponse,
)
from services.gemini_service import explain_code_with_gemini, chat_with_gemini

router = APIRouter(prefix="/api/ai", tags=["Gemini AI Explanation"])


@router.post("/explain", response_model=AIExplainResponse)
def explain_code(request: AIExplainRequest):
    """Explains complete code using Google Gemini AI in the selected mode and language."""
    res = explain_code_with_gemini(
        code=request.code,
        language=request.language,
        mode=request.mode or "detailed",
        explanation_language=request.explanation_language or "english",
    )
    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "No code" in (res.get("error") or "") else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("error", "AI explanation failed."),
        )
    return res


@router.post("/explain-line-by-line", response_model=AIExplainResponse)
def explain_line_by_line(request: AIExplainRequest):
    """Explains code line by line in sequential numbered order."""
    res = explain_code_with_gemini(
        code=request.code,
        language=request.language,
        mode="line_by_line",
        explanation_language=request.explanation_language or "english",
    )
    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("error", "Line-by-line explanation failed."),
        )
    return res


@router.post("/explain-algorithm", response_model=AIExplainResponse)
def explain_algorithm(request: AIExplainRequest):
    """Explains the underlying algorithm and step-by-step state execution flow."""
    res = explain_code_with_gemini(
        code=request.code,
        language=request.language,
        mode="algorithm",
        explanation_language=request.explanation_language or "english",
    )
    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("error", "Algorithm explanation failed."),
        )
    return res


@router.post("/explain-interview", response_model=AIExplainResponse)
def explain_interview(request: AIExplainRequest):
    """Generates a technical interview answer, concept highlights, and follow-up Q&A."""
    res = explain_code_with_gemini(
        code=request.code,
        language=request.language,
        mode="interview",
        explanation_language=request.explanation_language or "english",
    )
    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("error", "Interview explanation failed."),
        )
    return res


@router.post("/explain-optimization", response_model=AIExplainResponse)
def explain_optimization(request: AIExplainRequest):
    """Identifies code inefficiencies and suggests optimization opportunities with trade-offs."""
    res = explain_code_with_gemini(
        code=request.code,
        language=request.language,
        mode="optimization",
        explanation_language=request.explanation_language or "english",
    )
    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("error", "Optimization explanation failed."),
        )
    return res


@router.post("/chat", response_model=AIChatResponse)
def chat_follow_up(request: AIChatRequest):
    """Answers follow-up questions about submitted code with full context memory."""
    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
    res = chat_with_gemini(
        code=request.code,
        message=request.message,
        language=request.language,
        explanation_language=request.explanation_language or "english",
        history=history_dicts,
    )
    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("error", "Chat follow-up failed."),
        )
    return res

