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
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

def init_auth_file():
    # 优先从 ADMIN_PASSWORD 获取
    env_password = os.getenv("ADMIN_PASSWORD")
    if not env_password:
        logger.info(f"请在.env中配置ADMIN_PASSWORD或SECRET_KEY")
    
    # 如果 auth.json 不存在，直接创建
    if not os.path.exists(AUTH_FILE):
        default_hash = get_password_hash(env_password)
        with open(AUTH_FILE, "w") as f:
            json.dump({"hashed_password": default_hash}, f)
        logger.info(f"Initialized auth.json with password from {'ADMIN_PASSWORD' if env_password else 'SECRET_KEY'}.")
    else:
        # 可选：如果环境变量存在，是否强制更新密码？
        # 为了方便用户重置，这里添加一个逻辑：如果设置了 FORCE_RESET_PASSWORD=true，则重置
        if os.getenv("FORCE_RESET_PASSWORD", "false").lower() == "true":
             default_hash = get_password_hash(env_password)
             with open(AUTH_FILE, "w") as f:
                json.dump({"hashed_password": default_hash}, f)
             logger.info("Forced reset password from env.")

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
