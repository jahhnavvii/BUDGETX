"""
BudgetX - Finance Analysis Router
"""

from fastapi import APIRouter
from pydantic import BaseModel
from llm_local import generate_local_finance_advice
from llm_flash import polish_with_flash

router = APIRouter(prefix="/api/finance", tags=["finance"])

class FinanceSummary(BaseModel):
    income: float
    expense: float
    savings_rate: float

@router.post("/analyze")
async def analyze_finance(summary: FinanceSummary):
    # Step 1: Convert structured JSON into readable summary
    summary_text = f"Income: {summary.income}, Expense: {summary.expense}, Savings Rate: {summary.savings_rate}"

    # Step 2: Local domain reasoning (using Gemma)
    local_output = generate_local_finance_advice(summary_text)

    # Step 3: Polishing layer (using Gemini Flash)
    final_output = polish_with_flash(local_output)

    return {
        "local_model_output": local_output,
        "final_polished_output": final_output
    }
