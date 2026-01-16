import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

# 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-it")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 12 * 60  # 12 hours
AUTH_FILE = "auth.json"

# 初始化
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
logger = logging.getLogger("CMS-Auth")

# 模型
class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    password: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

# 密码管理
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def init_auth_file():
    if not os.path.exists(AUTH_FILE):
        default_hash = get_password_hash("admin123")
        with open(AUTH_FILE, "w") as f:
            json.dump({"hashed_password": default_hash}, f)
        logger.info("Initialized auth.json with default password.")

def get_stored_hash():
    if not os.path.exists(AUTH_FILE):
        init_auth_file()
    try:
        with open(AUTH_FILE, "r") as f:
            data = json.load(f)
            return data.get("hashed_password")
    except Exception as e:
        logger.error(f"Failed to read auth file: {e}")
        return None

def update_password(new_password):
    new_hash = get_password_hash(new_password)
    with open(AUTH_FILE, "w") as f:
        json.dump({"hashed_password": new_hash}, f)

# Token 管理
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 依赖注入
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 这里我们就简单验证 token 有效性，因为是单用户系统
        return True
    except JWTError:
        raise credentials_exception
