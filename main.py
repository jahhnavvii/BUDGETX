"""
BudgetX - FastAPI Application (ORM Version)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import init_db
import auth
import analytics
import chat

load_dotenv() # Load environment variables from .env
init_db() # Create tables if not exist

app = FastAPI(title="BudgetX API (SQLAlchemy)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Simplified for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(chat.router)

@app.get("/")
def root(): return {"message": "BudgetX API is running (ORM)"}
