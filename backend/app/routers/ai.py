from fastapi import APIRouter

from ..models import Query
from ..ollama_client import ask
from ..storage import load_reports
from ..analytics import build_ai_context


router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/analyze")
def analyze(q: Query):
    reports = load_reports()
    context_block = build_ai_context(q.question, reports)
    # combine any user-provided context with grounded data snapshot
    combined_context = (
        (q.context + "\n\n") if q.context else ""
    ) + "DATA SNAPSHOT (from CSV):\n" + context_block
    system_guard = (
        "You are an assistant for soil boring & geotechnical logging."
        " Answer ONLY using the provided data snapshot."
        " If the answer cannot be found in the data, say 'Not found in data'."
        " Be concise and structure your answer with short bullets where appropriate."
        " Use the DATA SCHEMA types to interpret values (dates, times, numbers)."
        " When citing values, reference the exact column names."
    " Consider prior turns in the conversation to answer follow-ups."
    )
    answer = ask(q.question, combined_context + "\n\n" + system_guard, history=q.history)
    return {"answer": answer, "context": context_block}
