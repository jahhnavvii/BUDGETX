"""
BudgetX - Authentication Module (Refactored for SQLAlchemy)
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
import database
from database import get_db, User

router = APIRouter(prefix="/api", tags=["auth"])
security = HTTPBearer()

SECRET_KEY = "budgetx-secret-key-change-in-production"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    token: str
    username: str

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        username = payload.get("username")
        if user_id is None or username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    print(f"Registering user: {req.username}")
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        print(f"Registration failed: User {req.username} already exists")
        raise HTTPException(status_code=409, detail="Username already exists")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(req.password.encode('utf-8'), salt).decode('utf-8')
    try:
        new_user = User(username=req.username, password_hash=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"User {req.username} created with ID {new_user.id}")
        user_id = new_user.id
    except Exception as e:
        db.rollback()
        print(f"Database error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

    token = create_token(user_id, req.username)
    return AuthResponse(token=token, username=req.username)

@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    print(f"Login attempt: {req.username}")
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        print(f"Login failed: User {req.username} not found")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not bcrypt.checkpw(req.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        print(f"Login failed: Incorrect password for {req.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    print(f"Login successful: {req.username}")
    token = create_token(user.id, user.username)
    return AuthResponse(token=token, username=req.username)
