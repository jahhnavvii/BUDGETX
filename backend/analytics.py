"""
BudgetX - Financial Analytics Module (Refactored for SQLAlchemy)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import json
import io
import os
import uuid
from auth import verify_token
from database import get_db, UploadedFile

router = APIRouter(prefix="/api", tags=["analytics"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Analytics engine
# ---------------------------------------------------------------------------

def parse_csv(file_content: bytes, filename: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(file_content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    # Normalize column names to lowercase and strip whitespace
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Optional: try to handle typical column names if they're formatted differently
    # but for now we'll just keep the normalized names.
    
    return df

def compute_analytics(df: pd.DataFrame) -> dict:
    """Best-effort analytics: runs financial calculations if columns exist, else generic summary."""
    cols = set(df.columns)
    has_finance_cols = {"type", "amount"}.issubset(cols)
    
    # Generic metadata
    analysis = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "is_financial_data": has_finance_cols
    }

    if has_finance_cols:
        # Pre-process amount column if it exists
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["type"] = df["type"].astype(str).str.strip().str.lower()
        
        income_df = df[df["type"] == "income"]
        expense_df = df[df["type"] == "expense"]
        
        total_income = round(float(income_df["amount"].sum()), 2)
        total_expenses = round(float(expense_df["amount"].sum()), 2)
        net_surplus = round(total_income - total_expenses, 2)
        savings_rate = round((net_surplus / total_income) * 100, 2) if total_income > 0 else 0.0
        
        analysis.update({
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_surplus": net_surplus,
            "savings_rate": savings_rate
        })

        if "category" in cols:
            df["category"] = df["category"].astype(str).str.strip()
            expense_by_category = expense_df.groupby("category")["amount"].sum().sort_values(ascending=False).round(2).to_dict()
            analysis["expense_by_category"] = expense_by_category
            if total_expenses > 0:
                analysis["expense_ratios"] = {cat: round((amt / total_expenses) * 100, 2) for cat, amt in expense_by_category.items()}
                analysis["overspending_flags"] = [{"category": cat, "percentage": pct, "amount": expense_by_category[cat]} for cat, pct in analysis["expense_ratios"].items() if pct > 30]

    # For any columns, provide small sample / basic summary
    numeric_cols = df.select_dtypes(include=['number']).columns
    if not numeric_cols.empty:
        analysis["numeric_summary"] = df[numeric_cols].describe().round(2).to_dict()

    if "date" in cols:
        try:
            dates = pd.to_datetime(df["date"], errors='coerce')
            analysis["date_range"] = {"start": str(dates.min()), "end": str(dates.max())}
        except:
            pass

    return analysis

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    content = await file.read()
    df = parse_csv(content, file.filename)
    analytics = compute_analytics(df)
    stored_name = f"{uuid.uuid4().hex}_{file.filename}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(content)

    new_file = UploadedFile(
        user_id=current_user["user_id"],
        original_filename=file.filename,
        stored_filename=stored_name,
        file_size=len(content),
        analytics_json=json.dumps(analytics)
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return {"file_id": new_file.id, "filename": file.filename, "analytics": analytics}

@router.get("/files")
def list_files(current_user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    files = db.query(UploadedFile).filter(UploadedFile.user_id == current_user["user_id"]).order_by(UploadedFile.upload_date.desc()).all()
    return [{"id": f.id, "filename": f.original_filename, "size": f.file_size, "uploaded": f.upload_date, "analytics": json.loads(f.analytics_json) if f.analytics_json else None} for f in files]
