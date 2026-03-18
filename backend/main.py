import os
import datetime
import base64
import logging
import json
import redis
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from core.response import success, fail, Code

# 导入自定义工具类
from core.github_client import GitHubClient
from core.image_uploader import TelegramUploader
from core.auth import (
    LoginRequest, PasswordChangeRequest, Token,
    verify_password, get_stored_hash, create_access_token,
    update_password, get_current_user, init_auth_file,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from fastapi import Depends, status
from datetime import timedelta

# 1. 加载配置
load_dotenv()

# 应用运行配置
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

# 初始化 Auth 文件
init_auth_file()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # 移除文件日志，避免 Docker 挂载目录冲突
        # logging.FileHandler("backend.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CMS-Backend")

# 2. 实例化 FastAPI
app = FastAPI()

# 3. 初始化工具类
client: Optional[GitHubClient] = None
github_init_error: Optional[str] = None

uploader = TelegramUploader()

# Redis 初始化
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    redis_client.ping()
    logger.info(f"Redis connected at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")
    redis_client = None

# 缓存配置
CACHE_TTL_ARTICLES = 3600  # 1 hour
CACHE_TTL_DETAIL = 86400   # 24 hours
CACHE_KEY_VERSION = "cms:version"
CACHE_KEY_ARTICLES = "cms:articles"

# 文章路径前缀
DRAFT_PREFIX = "src/drafts/"
POST_PREFIX = "src/posts/"

def _is_draft_path(path: str) -> bool:
    return isinstance(path, str) and path.startswith(DRAFT_PREFIX) and path.endswith(".md")

def _is_post_path(path: str) -> bool:
    return isinstance(path, str) and path.startswith(POST_PREFIX) and path.endswith(".md")

def _swap_prefix(path: str, from_prefix: str, to_prefix: str) -> Optional[str]:
    if not isinstance(path, str) or not path.startswith(from_prefix):
        return None
    return f"{to_prefix}{path[len(from_prefix):]}"

def _get_existing_file(path: str):
    try:
        return client.repo.get_contents(path)
    except Exception as e:
        if getattr(e, "status", None) == 404:
            return None
        raise

def _validate_publish_paths(old_path: str, new_path: str, from_prefix: str, to_prefix: str):
    if not old_path or not new_path:
        return fail(msg="路径不能为空", code=Code.PARAM_ERROR)
    if not _is_draft_path(old_path) and not _is_post_path(old_path):
        return fail(msg="旧路径必须在 src/drafts 或 src/posts 下", code=Code.PARAM_ERROR)
    if not _is_draft_path(new_path) and not _is_post_path(new_path):
        return fail(msg="新路径必须在 src/drafts 或 src/posts 下", code=Code.PARAM_ERROR)
    if not old_path.startswith(from_prefix):
        return fail(msg="旧路径前缀不正确", code=Code.PARAM_ERROR)
    if not new_path.startswith(to_prefix):
        return fail(msg="新路径前缀不正确", code=Code.PARAM_ERROR)

    expected_new = _swap_prefix(old_path, from_prefix, to_prefix)
    if expected_new != new_path:
        return fail(msg="路径不匹配，需保留子路径结构", code=Code.PARAM_ERROR)
    if old_path == new_path:
        return fail(msg="新旧路径不能相同", code=Code.PARAM_ERROR)
    return None

def get_cache(key: str):
    if not redis_client: return None
    try:
        return redis_client.get(key)
    except Exception as e:
        logger.error(f"Redis get failed: {e}")
        return None

def set_cache(key: str, value: str, ex: int = None): # type: ignore
    if not redis_client: return
    try:
        redis_client.set(key, value, ex=ex)
    except Exception as e:
        logger.error(f"Redis set failed: {e}")

def delete_cache(pattern: str):
    if not redis_client: return
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys) # type: ignore
    except Exception as e:
        logger.error(f"Redis delete failed: {e}")

# --- 请求模型定义 ---

class SaveArticleRequest(BaseModel):
    path: str
    content: str
    sha: Optional[str] = None  # 允许为 None 或空，代表新建
    message: Optional[str] = None

class DeleteArticleRequest(BaseModel):
    path: str
    sha: str
    message: Optional[str] = None

class RenameArticleRequest(BaseModel):
    old_path: str
    new_path: str
    sha: str
    content: Optional[str] = None # 如果重命名时内容有变化可以一起传
    overwrite: Optional[bool] = False # 允许覆盖目标文件

# GitHub 分支配置
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# 允许跨域的源（支持多个域名，用逗号分隔）
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 统一异常处理，避免错误无上下文
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(msg=str(exc.detail), code=exc.status_code)
        )

    logger.error(
        "unhandled.error path=%s method=%s err=%s",
        request.url.path,
        request.method,
        exc,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content=fail(msg="服务异常，请查看后端日志", code=Code.INTERNAL_ERROR)
    )

def _require_github_client():
    global client, github_init_error
    if client is None:
        try:
            client = GitHubClient()
            github_init_error = None
        except Exception as e:
            github_init_error = str(e)
            msg = f"GitHub 未初始化: {github_init_error or '未知错误'}"
            logger.error(msg, exc_info=True)
            return fail(msg=msg, code=Code.GITHUB_ERROR)
    return None

# 统一输出启动信息
@app.on_event("startup")
async def _log_startup_info():
    if PUBLIC_BASE_URL:
        base_url = PUBLIC_BASE_URL
    else:
        base_url = f"http://{APP_HOST}:{APP_PORT}"

    logger.info("startup.status=ok")
    logger.info("startup.base_url=%s", base_url)
    logger.info("startup.api_base=%s", f"{base_url}/api")
    logger.info("startup.docs=%s", f"{base_url}/docs")
    if APP_HOST == "0.0.0.0" and not PUBLIC_BASE_URL:
        logger.info("startup.note=use-server-ip Replace 0.0.0.0 with your public IP or domain")
    if github_init_error:
        logger.error("startup.github_init_error=%s", github_init_error)

# --- Auth 接口 ---

@app.post("/api/login")
async def login(request: LoginRequest):
    try:
        hashed_password = get_stored_hash()
        if not hashed_password:
             logger.error("Auth file not found or corrupted")
             return fail(msg="登录服务不可用", code=Code.INTERNAL_ERROR)

        if not verify_password(request.password, hashed_password):
            return fail(msg="密码错误", code=Code.UNAUTHORIZED)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": "admin"}, expires_delta=access_token_expires
        )
        return success(data={"access_token": access_token, "token_type": "bearer"}, msg="登录成功")
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        return fail(msg="登录服务异常", code=Code.INTERNAL_ERROR)

@app.post("/api/password/change", dependencies=[Depends(get_current_user)])
async def change_password(request: PasswordChangeRequest):
    hashed_password = get_stored_hash()
    if not verify_password(request.current_password, hashed_password):
        return fail(msg="当前密码错误", code=Code.PARAM_ERROR)
    
    update_password(request.new_password)
    return success(msg="密码修改成功")

# --- API 接口 ---

@app.get("/api/version", dependencies=[Depends(get_current_user)])
def get_version():
    """获取当前数据版本号 (Latest Commit SHA)"""
    try:
        err = _require_github_client()
        if err: return err
        version = get_cache(CACHE_KEY_VERSION)
        if not version:
            version = client.get_latest_commit_sha()
            if version:
                set_cache(CACHE_KEY_VERSION, version, ex=300) # 5 minutes TTL for version check
        
        return success(data={"version": version})
    except Exception as e:
        return fail(msg=f"获取版本失败: {str(e)}", code=Code.GITHUB_ERROR)

@app.get("/api/articles")
def get_articles(force_refresh: bool = False):
    try:
        err = _require_github_client()
        if err: return err
        # 缓存检查
        if not force_refresh:
            cached_data = get_cache(CACHE_KEY_ARTICLES)
            if cached_data:
                data = json.loads(cached_data) # type: ignore
                return success(data=data, total=len(data), extra={"cache": "HIT"})

        # 获取全量文件树
        tree = client.repo.get_git_tree(GITHUB_BRANCH, recursive=True)
        root = {"name": "Root", "children": []}
        folder_map = {"": root}

        for file in tree.tree:
            # 过滤目录
            if file.path.startswith(("src/posts/", "src/drafts/")) and file.path.endswith(".md"):
                path_parts = file.path.split('/')
                current_path = ""
                for i in range(len(path_parts) - 1):
                    part = path_parts[i]
                    parent_path = current_path
                    current_path = f"{current_path}/{part}" if current_path else part
                    if current_path not in folder_map:
                        new_folder = {"name": part, "type": "folder", "children": [], "path": current_path}
                        folder_map[parent_path]["children"].append(new_folder)
                        folder_map[current_path] = new_folder
                
                file_node = {
                    "name": path_parts[-1],
                    "path": file.path,
                    "type": "file",
                    "sha": file.sha,
                    "isDraft": "src/drafts/" in file.path
                }
                # 容错处理：确保 current_path 在 map 中
                if current_path in folder_map:
                    folder_map[current_path]["children"].append(file_node)

        # 整理返回列表（保留 posts/drafts 分组，避免同名目录冲突）
        final_list = []
        src_node = next((n for n in root["children"] if n["name"] == "src"), None)
        if src_node:
            for sub in src_node["children"]:
                if sub["name"] == "posts":
                    sub["group"] = "posts"
                    sub["name"] = "已发布"
                    final_list.append(sub)
                elif sub["name"] == "drafts":
                    sub["group"] = "drafts"
                    sub["name"] = "草稿"
                    final_list.append(sub)
        
        # 写入缓存
        set_cache(CACHE_KEY_ARTICLES, json.dumps(final_list), ex=CACHE_TTL_ARTICLES)
        
        # 返回标准成功结构，携带数据总量
        return success(data=final_list, total=len(final_list), extra={"cache": "MISS"})
    except Exception as e:
        logger.error(f"获取文章列表失败: {str(e)}", exc_info=True)
        return fail(msg=f"获取文章列表失败: {str(e)}", code=Code.INTERNAL_ERROR)

@app.get("/api/article/detail", dependencies=[Depends(get_current_user)])
def get_article_detail(path: str, force_refresh: bool = False):
    try:
        err = _require_github_client()
        if err: return err
        cache_key = f"cms:article:{path}"
        
        if not force_refresh:
            cached_data = get_cache(cache_key)
            if cached_data:
                return success(data=json.loads(cached_data), extra={"cache": "HIT"}) # type: ignore

        content_file = client.repo.get_contents(path)
        raw_content = base64.b64decode(content_file.content).decode('utf-8') # type: ignore
        
        result = {
            "path": path,
            "title": os.path.basename(path),
            "content": raw_content,
        }
        
        # 写入缓存
        set_cache(cache_key, json.dumps(result), ex=CACHE_TTL_DETAIL)

        # 返回详情，并带上关键的 SHA
        return success(data=result, sha=content_file.sha, extra={"cache": "MISS"}) # type: ignore
    except Exception as e:
        logger.error(f"读取文件内容失败: {path} - {str(e)}", exc_info=True)
        return fail(msg=f"读取文件内容失败: {path}", code=Code.NOT_FOUND)

@app.post("/api/article/save", dependencies=[Depends(get_current_user)])
def save_to_github(item: SaveArticleRequest):
    try:
        err = _require_github_client()
        if err: return err
        # 1. 基础验证
        if not item.path:
            return fail(msg="文件路径不能为空", code=Code.PARAM_ERROR)
        if not item.content:
            return fail(msg="文件内容不能为空", code=Code.PARAM_ERROR)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        default_msg = f"CMS Update: {os.path.basename(item.path)} ({now})"
        final_msg = item.message.strip() if item.message and item.message.strip() else default_msg

        params = {
            "path": item.path,
            "message": final_msg,
            "content": item.content,
            "branch": GITHUB_BRANCH
        }

        # 判断新建还是更新
        if not item.sha or item.sha in ["", "new"]:
            logger.info(f"正在新建文件: {item.path}")
            try:
                res = client.repo.create_file(**params) # type: ignore
                action = "创建"
            except Exception as create_e:
                # 容错处理：如果报错 "sha wasn't supplied" (422)，说明文件已存在，尝试获取 SHA 并转为更新
                if "sha" in str(create_e) and "supplied" in str(create_e) and "422" in str(create_e):
                    logger.warning(f"文件已存在但未提供 SHA，尝试自动修复: {item.path}")
                    try:
                        existing_file = client.repo.get_contents(item.path)
                        params["sha"] = existing_file.sha # type: ignore
                        res = client.repo.update_file(**params) # type: ignore
                        action = "更新 (自动修复)"
                    except Exception as inner_e:
                        # 如果修复过程中再次失败（如获取失败），抛出原始错误
                        logger.error(f"自动修复失败: {str(inner_e)}")
                        raise create_e
                else:
                    raise create_e
        else:
            logger.info(f"正在更新文件: {item.path} (SHA: {item.sha})")
            params["sha"] = item.sha
            res = client.repo.update_file(**params) # type: ignore
            action = "更新"
            
        # 核心：必须返回新的 SHA，否则前端无法连续保存
        new_sha = res['content'].sha
        logger.info(f"文件{action}成功: {item.path}, New SHA: {new_sha}")
        
        # 缓存清理
        delete_cache(CACHE_KEY_ARTICLES)
        delete_cache(f"cms:article:{item.path}")
        delete_cache(CACHE_KEY_VERSION)
        
        return success(msg=f"文件{action}成功", sha=new_sha)
    except Exception as e:
        logger.error(f"保存失败: {str(e)}", exc_info=True)
        # 处理常见错误：SHA 冲突
        if "does not match" in str(e):
            return fail(msg="保存失败：GitHub 版本冲突，请刷新页面重新编辑", code=Code.GITHUB_ERROR)
        return fail(msg=f"保存失败: {str(e)}", code=Code.INTERNAL_ERROR)

# ... (image upload unchanged) ...
@app.post("/api/upload/image", dependencies=[Depends(get_current_user)])
async def upload_image(file: UploadFile = File(...)):
    try:
        # 1. 验证文件类型
        if not file.content_type.startswith("image/"): # type: ignore
            return fail(msg="仅支持上传图片文件", code=Code.PARAM_ERROR)
        
        logger.info(f"开始上传图片: {file.filename}")
        url = await uploader.upload_image(file)
        
        if url:
            logger.info(f"图片上传成功: {url}")
            return success(data={"url": url})
        else:
            logger.error("图片上传失败: 图床服务返回空 URL")
            return fail(msg="图片上传失败，请检查图床配置", code=Code.INTERNAL_ERROR)
    except Exception as e:
        logger.error(f"图片上传异常: {str(e)}", exc_info=True)
        return fail(msg=f"图片上传异常: {str(e)}", code=Code.INTERNAL_ERROR)


# 新增：删除接口
@app.post("/api/article/delete", dependencies=[Depends(get_current_user)])
def delete_article(item: DeleteArticleRequest):
    try:
        err = _require_github_client()
        if err: return err
        default_msg = f"CMS Delete: {os.path.basename(item.path)}"
        commit_msg = item.message.strip() if item.message and item.message.strip() else default_msg
        client.repo.delete_file(
            path=item.path,
            message=commit_msg,
            sha=item.sha,
            branch=GITHUB_BRANCH
        )
        # 缓存清理
        delete_cache(CACHE_KEY_ARTICLES)
        delete_cache(f"cms:article:{item.path}")
        delete_cache(CACHE_KEY_VERSION)
        
        return success(msg="文章已从 GitHub 彻底移除")
    except Exception as e:
        return fail(msg=f"删除操作失败: {str(e)}", code=Code.GITHUB_ERROR)

# 通用重命名/发布/撤回逻辑
def _handle_rename_action(item: RenameArticleRequest, action_label: str):
    # 1. 基础校验
    if not item.old_path or not item.new_path:
        return fail(msg="路径不能为空", code=Code.PARAM_ERROR)
    if item.old_path == item.new_path:
        return fail(msg="新旧路径不能相同", code=Code.PARAM_ERROR)

    # 2. 获取内容
    content = item.content
    if not content:
        try:
            old_file = client.repo.get_contents(item.old_path)
            # 旧路径如果是目录则视为无效
            if isinstance(old_file, list):
                return fail(msg="旧路径为目录，无法重命名", code=Code.PARAM_ERROR)
            content = base64.b64decode(old_file.content).decode('utf-8') # type: ignore
        except Exception as e:
            if getattr(e, "status", None) == 404:
                return fail(msg="旧路径不存在", code=Code.NOT_FOUND)
            raise

    # 3. 创建或覆盖目标文件
    try:
        existing_target = _get_existing_file(item.new_path)
        if existing_target:
            if isinstance(existing_target, list):
                return fail(msg="目标路径为目录，无法覆盖", code=Code.CONFLICT)
            if not item.overwrite:
                return fail(msg="目标路径已存在", code=Code.CONFLICT)

            logger.info(f"{action_label}.overwrite: {item.old_path} -> {item.new_path}")
            create_res = client.repo.update_file(
                path=item.new_path,
                message=f"CMS {action_label} (Overwrite): {item.old_path} -> {item.new_path}",
                content=content,
                sha=existing_target.sha, # type: ignore
                branch=GITHUB_BRANCH
            )
        else:
            logger.info(f"{action_label}.create: {item.old_path} -> {item.new_path}")
            create_res = client.repo.create_file(
                path=item.new_path,
                message=f"CMS {action_label} (Create): {item.old_path} -> {item.new_path}",
                content=content,
                branch=GITHUB_BRANCH
            )
    except Exception as e:
        return fail(msg=f"{action_label}失败: {str(e)}", code=Code.GITHUB_ERROR)

    # 4. 删除旧路径文件
    try:
        client.repo.delete_file(
            path=item.old_path,
            message=f"CMS {action_label} (Delete): {item.old_path}",
            sha=item.sha,
            branch=GITHUB_BRANCH
        )
    except Exception as e:
        return fail(msg=f"{action_label}失败(删除旧文件): {str(e)}", code=Code.GITHUB_ERROR)
    
    # 缓存清理
    delete_cache(CACHE_KEY_ARTICLES)
    delete_cache(f"cms:article:{item.old_path}")
    delete_cache(f"cms:article:{item.new_path}")
    delete_cache(CACHE_KEY_VERSION)
    
    # 返回新文件的 SHA，以便前端立即继续编辑新文件
    return success(msg=f"{action_label}成功", sha=create_res['content'].sha)

# 新增：重命名接口 (GitHub API 逻辑：新建+删除)
@app.post("/api/article/rename", dependencies=[Depends(get_current_user)])
def rename_article(item: RenameArticleRequest):
    try:
        err = _require_github_client()
        if err: return err
        return _handle_rename_action(item, "Rename")
    except Exception as e:
        return fail(msg=f"重命名失败: {str(e)}", code=Code.INTERNAL_ERROR)

# 新增：发布草稿
@app.post("/api/article/publish", dependencies=[Depends(get_current_user)])
def publish_article(item: RenameArticleRequest):
    try:
        err = _require_github_client()
        if err: return err
        validation_error = _validate_publish_paths(item.old_path, item.new_path, DRAFT_PREFIX, POST_PREFIX)
        if validation_error:
            return validation_error

        # 冲突检测
        if _get_existing_file(item.new_path):
            return fail(msg="目标路径已存在，请确认是否覆盖", code=Code.CONFLICT)

        logger.info(f"publish: {item.old_path} -> {item.new_path}")
        return _handle_rename_action(item, "Publish")
    except Exception as e:
        return fail(msg=f"发布失败: {str(e)}", code=Code.INTERNAL_ERROR)

# 新增：撤回为草稿
@app.post("/api/article/unpublish", dependencies=[Depends(get_current_user)])
def unpublish_article(item: RenameArticleRequest):
    try:
        err = _require_github_client()
        if err: return err
        validation_error = _validate_publish_paths(item.old_path, item.new_path, POST_PREFIX, DRAFT_PREFIX)
        if validation_error:
            return validation_error

        # 冲突检测
        if _get_existing_file(item.new_path):
            return fail(msg="目标路径已存在，请确认是否覆盖", code=Code.CONFLICT)

        logger.info(f"unpublish: {item.old_path} -> {item.new_path}")
        return _handle_rename_action(item, "Unpublish")
    except Exception as e:
        return fail(msg=f"撤回失败: {str(e)}", code=Code.INTERNAL_ERROR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
