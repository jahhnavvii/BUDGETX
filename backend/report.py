"""
BudgetX - AI Report Generation Module
Generates detailed financial reports based on analytics data using Gemini.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from auth import verify_token
from database import get_db, UploadedFile
from ai_utils import get_gemini_model
import json

router = APIRouter(prefix="/api", tags=["reports"])

REPORT_PROMPTS = {
    "risk_assessment": """You are an expert financial risk analyst. Based on the following financial analytics data, generate a comprehensive Risk Assessment Report.

Include these sections:
1. **Financial Health Score** (0-100) with justification
2. **Liquidity Risk Analysis** - assess current ratio and cash flow stability
3. **Volatility Metrics** - income/expense variability assessment
4. **Emergency Fund Adequacy** - months of coverage estimate
5. **Debt Burden Analysis** - debt-to-income ratio assessment
6. **Concentration Risk** - revenue/expense concentration by category
7. **Early Warning Indicators** - list 5-10 predictive risk flags
8. **Scenario Simulation** - describe 2-3 stress test scenarios

At the VERY END of your response, you MUST include a [DASHBOARD_DATA] section with relevant JSON data for visualization.
Focus on: Liquidity Score vs Debt Score vs Savings Score.
Format:
[DASHBOARD_DATA]
{
  "is_financial_data": true,
  "net_surplus": 5000,
  "savings_rate": 25,
  "generic_chart_label": "Risk Factor Distribution",
  "expense_by_category": { "Liquidity": 80, "Debt": 30, "Savings": 60, "Volatility": 40 }
}
[/DASHBOARD_DATA]

Format with clear headers, bullet points, and specific numbers from the data. Be concise but thorough.""",

    "cost_optimization": """You are a financial efficiency expert. Based on the following financial analytics data, generate a comprehensive Cost Optimization Report.

Include these sections:
1. **Expense Category Breakdown** - hierarchical cost analysis
2. **Inefficiency Detection** - identify anomalies or unusual spending patterns
3. **Benchmark Comparison** - compare against typical spending profiles
4. **Zero-Based Budgeting Recommendations** - category-by-category review
5. **Vendor/Category Concentration** - identify over-reliance on single sources
6. **Subscription & Recurring Costs** - flag potentially reducible costs
7. **Tax Efficiency Opportunities** - potential deductions or optimizations
8. **Unit Economics** - cost per unit/transaction where applicable

At the VERY END of your response, you MUST include a [DASHBOARD_DATA] section with relevant JSON data for visualization.
Focus on: Potential Savings per Category.
Format:
[DASHBOARD_DATA]
{
  "is_financial_data": true,
  "total_rows": 100,
  "generic_chart_label": "Potential Annual Savings",
  "expense_by_category": { "Housing": 200, "Food": 150, "Transport": 100, "Sub": 300 }
}
[/DASHBOARD_DATA]

Format with clear headers, bullet points, and specific actionable dollar amounts from the data.""",

    "strategic_recommendations": """You are a strategic financial advisor. Based on the following financial analytics data, generate a comprehensive Strategic Recommendations Report.

Include these sections:
1. **Short-term Actions (0-3 months)** - 5 quick financial wins
2. **Medium-term Initiatives (3-12 months)** - 5 growth opportunities
3. **Long-term Strategy (1-5 years)** - 3 transformational changes
4. **Priority Matrix** - rank recommendations by Impact vs. Effort
5. **Resource Allocation Suggestions** - where to invest freed capital
6. **SMART Goal Framework** - 3 specific, measurable financial objectives
7. **Implementation Roadmap** - step-by-step 90-day execution plan

At the VERY END of your response, you MUST include a [DASHBOARD_DATA] section with relevant JSON data for visualization.
Focus on: Allocation of Strategic Efforts.
Format:
[DASHBOARD_DATA]
{
  "is_financial_data": true,
  "total_rows": 100,
  "generic_chart_label": "Strategic Priority Focus",
  "expense_by_category": { "Savings": 40, "Debt Payoff": 30, "Investing": 20, "Lifestyle": 10 }
}
[/DASHBOARD_DATA]

Format with clear headers, numbered lists, and specific timelines and metrics from the data.""",

    "performance_analytics": """You are a financial performance analyst. Based on the following financial analytics data, generate a comprehensive Performance Analytics Report.

Include these sections:
1. **Trend Analysis** - identify performance trends in the data
2. **Variance Analysis** - highlight significant deviations and their causes
3. **Growth Metrics** - calculate growth rates, CAGR where applicable
4. **Efficiency Ratios** - operating expense ratios, overhead percentages
5. **Profitability Analysis** - net/gross margin estimates
6. **Seasonality Patterns** - identify cyclical patterns if visible in data
7. **KPI Dashboard** - list 10-15 key financial indicators with values
8. **Performance Summary** - overall assessment and trajectory

At the VERY END of your response, you MUST include a [DASHBOARD_DATA] section with relevant JSON data for visualization.
Focus on: KPI Performance Metrics.
Format:
[DASHBOARD_DATA]
{
  "is_financial_data": true,
  "total_income": 10000,
  "total_expenses": 7000,
  "net_surplus": 3000,
  "generic_chart_label": "Core KPI Overview",
  "expense_by_category": { "Efficiency": 85, "Growth": 12, "Stability": 75 }
}
[/DASHBOARD_DATA]

Format with clear headers, tables where appropriate, and specific numbers from the data.""",

    "investment_portfolio": """You are an investment advisor and portfolio analyst. Based on the following financial analytics data, generate a comprehensive Investment & Portfolio Strategy Report.

Include these sections:
1. **Asset Allocation Analysis** - assess current allocation and gaps
2. **Risk-Return Profile** - estimate risk level and expected returns
3. **Diversification Assessment** - identify concentration risks
4. **Investment Opportunities** - suggest specific investment vehicles
5. **Rebalancing Recommendations** - suggest allocation adjustments
6. **Tax-Loss Harvesting** - identify potential optimization strategies
7. **Goal-Based Investing** - map investments to financial objectives
8. **Recommended Next Steps** - prioritized action items

At the VERY END of your response, you MUST include a [DASHBOARD_DATA] section with relevant JSON data for visualization.
Focus on: Target Asset Allocation.
Format:
[DASHBOARD_DATA]
{
  "is_financial_data": true,
  "generic_chart_label": "Recommended Asset Class Mix",
  "expense_by_category": { "Stocks": 60, "Bonds": 20, "Cash": 10, "Crypto/Alt": 10 }
}
[/DASHBOARD_DATA]

Format with clear headers, bullet points, and specific recommendations based on the available data."""
}

class ReportRequest(BaseModel):
    file_id: int
    report_type: str  # One of the REPORT_PROMPTS keys

@router.post("/report")
async def generate_report(
    req: ReportRequest,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    if req.report_type not in REPORT_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {req.report_type}")

    # Load the file's analytics
    file_record = db.query(UploadedFile).filter(
        UploadedFile.id == req.file_id,
        UploadedFile.user_id == current_user["user_id"]
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    analytics = {}
    if file_record.analytics_json:
        try:
            analytics = json.loads(file_record.analytics_json)
        except Exception:
            pass

    ai_model = get_gemini_model()
    if ai_model is None:
        raise HTTPException(status_code=503, detail="AI service unavailable. Please check your API key.")

    base_prompt = REPORT_PROMPTS[req.report_type]
    full_prompt = f"{base_prompt}\n\n**Analytics Data:**\n```json\n{json.dumps(analytics, indent=2)}\n```\n\nFilename: {file_record.original_filename}\nTotal rows: {analytics.get('total_rows', 'N/A')}"

    try:
        response = ai_model.generate_content(full_prompt)
        report_text = response.text.strip()
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            raise HTTPException(
                status_code=429, 
                detail="Gemini API quota exceeded for the Free Tier (Limit: 20 requests/day). Please wait a few minutes or try again later."
            )
        raise HTTPException(status_code=500, detail=f"Report generation failed: {error_msg}")

    return {
        "report_type": req.report_type,
        "filename": file_record.original_filename,
        "content": report_text
    }
