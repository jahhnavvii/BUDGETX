"""
BudgetX - Financial Analytics Module
Deterministic calculations on CSV financial data using Pandas.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import json
import io
import os
import uuid
from datetime import datetime
from auth import verify_token
import database

router = APIRouter(prefix="/api", tags=["analytics"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Analytics engine (deterministic — no LLM)
# ---------------------------------------------------------------------------

def parse_csv(file_content: bytes, filename: str) -> pd.DataFrame:
    """Parse CSV bytes into a DataFrame with validation."""
    try:
        df = pd.read_csv(io.BytesIO(file_content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    # Normalize column names to lowercase
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"date", "category", "amount", "type"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(missing)}. "
                   f"Expected columns: date, category, amount, type (income/expense). "
                   f"Found columns: {', '.join(df.columns)}"
        )

    # Clean data
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["type"] = df["type"].str.strip().str.lower()
    df["category"] = df["category"].str.strip()

    return df


def compute_analytics(df: pd.DataFrame) -> dict:
    """Run deterministic financial calculations and return structured JSON."""

    income_df = df[df["type"] == "income"]
    expense_df = df[df["type"] == "expense"]

    total_income = round(float(income_df["amount"].sum()), 2)
    total_expenses = round(float(expense_df["amount"].sum()), 2)
    net_surplus = round(total_income - total_expenses, 2)

    savings_rate = round((net_surplus / total_income) * 100, 2) if total_income > 0 else 0.0

    # Expense breakdown by category
    expense_by_category = (
        expense_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .round(2)
        .to_dict()
    )

    # Expense ratios (percentage of total expenses per category)
    expense_ratios = {}
    if total_expenses > 0:
        for cat, amt in expense_by_category.items():
            expense_ratios[cat] = round((amt / total_expenses) * 100, 2)

    # Overspending detection — categories that consume > 30 % of total expenses
    overspending = [
        {"category": cat, "percentage": pct, "amount": expense_by_category[cat]}
        for cat, pct in expense_ratios.items()
        if pct > 30
    ]

    # Income breakdown by category
    income_by_category = (
        income_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
        .round(2)
        .to_dict()
    )

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_surplus": net_surplus,
        "savings_rate": savings_rate,
        "expense_by_category": expense_by_category,
        "expense_ratios": expense_ratios,
        "income_by_category": income_by_category,
        "overspending_flags": overspending,
        "total_transactions": len(df),
        "date_range": {
            "start": str(df["date"].min()),
            "end": str(df["date"].max()),
        },
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token),
):
    """Upload a CSV file, parse it, run analytics, and store results."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Parse and analyze
    df = parse_csv(content, file.filename)
    analytics = compute_analytics(df)

    # Save file to disk
    stored_name = f"{uuid.uuid4().hex}_{file.filename}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(content)

    # Save record to database
    file_id = database.save_file_record(
        user_id=current_user["user_id"],
        original_filename=file.filename,
        stored_filename=stored_name,
        file_size=len(content),
        analytics_json=json.dumps(analytics),
    )

    return {
        "file_id": file_id,
        "filename": file.filename,
        "analytics": analytics,
    }


@router.get("/files")
def list_files(current_user: dict = Depends(verify_token)):
    """List all files uploaded by the current user."""
    files = database.get_user_files(current_user["user_id"])
    result = []
    for f in files:
        item = {
            "id": f["id"],
            "filename": f["original_filename"],
            "size": f["file_size"],
            "uploaded": f["upload_date"],
        }
        if f["analytics_json"]:
            item["analytics"] = json.loads(f["analytics_json"])
        result.append(item)
    return result


@router.get("/files/{file_id}")
def get_file(file_id: int, current_user: dict = Depends(verify_token)):
    """Get details for a specific uploaded file."""
    f = database.get_file_by_id(file_id, current_user["user_id"])
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    result = dict(f)
    if result.get("analytics_json"):
        result["analytics"] = json.loads(result["analytics_json"])
    return result
