from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any
from enum import IntEnum
import time

# 1. 定义业务状态码枚举
class Code(IntEnum):
    SUCCESS = 200            # 成功
    BAD_REQUEST = 400        # 请求参数错误
    UNAUTHORIZED = 401       # 未授权/Token失效
    FORBIDDEN = 403          # 权限不足
    NOT_FOUND = 404          # 资源不存在
    GITHUB_ERROR = 502       # GitHub API 调用失败
    INTERNAL_ERROR = 500     # 服务器内部错误

T = TypeVar("T")

# 2. 增强的标准响应模型
class StandardResponse(BaseModel, Generic[T]):
    code: int = Code.SUCCESS
    msg: str = "success"
    data: Optional[T] = None
    sha: Optional[str] = None
    timestamp: float = time.time()  # 响应时间戳
    # 用于分页的情况（可选）
    total: Optional[int] = None

# 3. 详细的响应工具函数
def success(
    data: Any = None, 
    msg: str = "操作成功", 
    sha: str = None, 
    total: int = None
):
    """成功响应：支持返回数据、GitHub SHA 和分页总数"""
    return {
        "code": Code.SUCCESS,
        "msg": msg,
        "data": data,
        "sha": sha,
        "total": total,
        "timestamp": time.time()
    }

def fail(
    msg: str = "操作失败", 
    code: Code = Code.BAD_REQUEST, 
    data: Any = None
):
    """失败响应：支持自定义状态码和错误详情"""
    return {
        "code": code,
        "msg": msg,
        "data": data,
        "timestamp": time.time()
    }
