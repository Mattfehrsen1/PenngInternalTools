from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User as DBUser

router = APIRouter()

# Security configurations
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# JWT settings from environment
SECRET_KEY = os.getenv("JWT_SECRET", "changeme-dev-only")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None

class User(BaseModel):
    username: str
    email: str
    id: str

class UserInDB(User):
    hashed_password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def authenticate_user(db: AsyncSession, username: str, password: str):
    # TEMPORARY FALLBACK: Hardcoded demo user for production access
    if username == "demo" and password == "demo123":
        return UserInDB(
            username="demo",
            email="demo@example.com",
            id="demo-user-id",
            hashed_password=get_password_hash("demo123")
        )
    
    # Check database for user
    try:
        result = await db.execute(select(DBUser).where(DBUser.username == username))
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        
        return UserInDB(
            username=user.username,
            email=user.email or "",
            id=user.id,
            hashed_password=user.hashed_password
        )
    except Exception as e:
        print(f"Database connection failed: {e}")
        # If database fails and credentials don't match fallback, return False
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # TEMPORARY FALLBACK: Support hardcoded demo user
    if token_data.username == "demo" and user_id == "demo-user-id":
        return User(
            username="demo",
            email="demo@example.com",
            id="demo-user-id"
        )
    
    # Check database for user
    try:
        result = await db.execute(select(DBUser).where(DBUser.username == token_data.username))
        user = result.scalar_one_or_none()
        
        if not user:
            raise credentials_exception
        
        return User(
            username=user.username,
            email=user.email or "",
            id=user.id
        )
    except Exception as e:
        print(f"Database error during user lookup: {e}")
        # If database lookup fails and user is not demo, raise credentials error
        raise credentials_exception

@router.post("/login", response_model=Token)
async def login(db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login endpoint.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
