from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any

# 定义泛型数据类型
T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    code: int = 200
    msg: str = "success"
    data: Optional[T] = None
    sha: Optional[str] = None  # 专门给 GitHub 操作留的字段

def success(data: Any = None, msg: str = "操作成功", sha: str = None):
    """成功响应工具函数"""
    return {
        "code": 200,
        "msg": msg,
        "data": data,
        "sha": sha
    }

def fail(msg: str = "操作失败", code: int = 400):
    """失败响应工具函数"""
    return {
        "code": code,
        "msg": msg,
        "data": None
    }
