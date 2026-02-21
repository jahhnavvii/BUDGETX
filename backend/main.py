"""
BudgetX - FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database  # triggers init_db() on import
import auth
import analytics
import chat

app = FastAPI(
    title="BudgetX API",
    description="AI-Assisted Financial Optimization Engine",
    version="1.0.0",
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"message": "BudgetX API is running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
