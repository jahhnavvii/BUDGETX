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
from database import get_db, UploadedFile, ChatMessage


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
    """Best-effort analytics: runs financial calculations if possible, else generic summary."""
    cols = list(df.columns)
    cols_set = set(cols)
    
    # Financial normalization (mapping common names)
    rename_map = {}
    if "type" not in cols_set:
        for c in ["transaction_type", "status", "payment_type"]:
            if c in cols_set:
                rename_map[c] = "type"
                break
    
    if "amount" not in cols_set:
        for c in ["total", "value", "revenue", "price", "cost", "total_price"]:
            if c in cols_set:
                rename_map[c] = "amount"
                break

    if "category" not in cols_set:
        for c in ["product", "item", "department", "expense_category"]:
            if c in cols_set:
                rename_map[c] = "category"
                break
                
    if rename_map:
        df = df.rename(columns=rename_map)
        cols_set = set(df.columns)

    has_finance_cols = {"type", "amount"}.issubset(cols_set)
    
    # Generic metadata
    analysis = {
        "total_rows": len(df),
        "columns": cols,
        "is_financial_data": has_finance_cols,
        "expense_by_category": {},
        "overspending_flags": []
    }

    # Pre-process numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if "amount" in cols_set and "amount" not in numeric_cols:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        numeric_cols.append("amount")

    if has_finance_cols:
        df["type"] = df["type"].astype(str).str.strip().str.lower()
        
        income_df = df[df["type"].isin(["income", "credit", "deposit", "earn"])]
        expense_df = df[df["type"].isin(["expense", "debit", "withdrawal", "payment", "buy"])]
        
        # If no explicit income/expense types found, treat all as expenses (common for simple sales data)
        if income_df.empty and expense_df.empty and "amount" in cols_set:
            expense_df = df
            
        total_income = round(float(income_df["amount"].sum()), 2)
        total_expenses = round(float(expense_df["amount"].sum()), 2)
        net_surplus = round(total_income - total_expenses, 2)
        savings_rate = round((net_surplus / total_income) * 100, 2) if total_income > 0 else 0.0
        
        analysis.update({
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_surplus": net_surplus,
            "savings_rate": savings_rate,
            "is_financial_data": True # Force true if we found something to chart
        })

        if "category" in cols_set:
            df["category"] = df["category"].astype(str).str.strip()
            cat_totals = expense_df.groupby("category")["amount"].sum().sort_values(ascending=False).round(2).to_dict()
            analysis["expense_by_category"] = cat_totals
            if total_expenses > 0:
                ratios = {cat: round((amt / total_expenses) * 100, 2) for cat, amt in cat_totals.items()}
                analysis["overspending_flags"] = [{"category": cat, "percentage": pct, "amount": cat_totals[cat]} for cat, pct in ratios.items() if pct > 30]

    # For generic numeric data (Fallback charts)
    if not analysis.get("is_financial_data") and numeric_cols:
        # Re-fetch current numeric columns and all columns after renaming
        current_cols = df.columns.tolist()
        # Pick the most "interesting" numeric column (usually 'amount' or the first numeric)
        target_col = "amount" if "amount" in current_cols else numeric_cols[0]
        
        # Pick a categorical column for grouping
        cat_candidates = [c for c in current_cols if c != target_col and df[c].nunique() < 20]
        if cat_candidates:
            group_col = cat_candidates[0]
            grouped = df.groupby(group_col)[target_col].sum().sort_values(ascending=False).round(2).to_dict()
            analysis["expense_by_category"] = grouped
            analysis["total_expenses"] = round(float(df[target_col].sum()), 2)
            analysis["is_financial_data"] = True # Enable charts in frontend
            analysis["generic_chart_label"] = f"{target_col} by {group_col}"


    if "date" in cols_set:
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

    # Add a signal for the frontend to render the dashboard
    analytics["_render_dashboard"] = True

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

    # 1. Add a placeholder message from the user about the upload
    upload_msg = ChatMessage(
        user_id=current_user["user_id"], 
        role="user", 
        content=f"Uploaded file: {file.filename}"
    )
    db.add(upload_msg)
    
    # 2. Trigger Auto-Analysis
    ai_insight = "AI analysis skipped due to error."
    try:
        from chat import get_auto_analysis
        ai_insight = await get_auto_analysis(json.dumps(analytics))
    except Exception as e:
        print(f"Auto-analysis Error: {str(e)}")
    
    # 3. Add the AI Insight as a chat message
    dashboard_data_marker = f"\n\n[DASHBOARD_DATA]{json.dumps(analytics)}[/DASHBOARD_DATA]"
    ai_msg = ChatMessage(
        user_id=current_user["user_id"],
        role="assistant",
        content=f"**Analysis for {file.filename}:**\n\n{ai_insight}{dashboard_data_marker}"
    )
    db.add(ai_msg)
    db.commit()

    return {"file_id": new_file.id, "filename": file.filename, "analytics": analytics, "ai_insight": ai_insight}



@router.get("/files")
def list_files(current_user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    files = db.query(UploadedFile).filter(UploadedFile.user_id == current_user["user_id"]).order_by(UploadedFile.upload_date.desc()).all()
    return [{"id": f.id, "filename": f.original_filename, "size": f.file_size, "uploaded": f.upload_date, "analytics": json.loads(f.analytics_json) if f.analytics_json else None} for f in files]
