import os
import datetime
import base64
import logging
import json
import redis
from fastapi import FastAPI, HTTPException, UploadFile, File
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
client = GitHubClient()
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

def get_cache(key: str):
    if not redis_client: return None
    try:
        return redis_client.get(key)
    except Exception as e:
        logger.error(f"Redis get failed: {e}")
        return None

def set_cache(key: str, value: str, ex: int = None):
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
            redis_client.delete(*keys)
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

class RenameArticleRequest(BaseModel):
    old_path: str
    new_path: str
    sha: str
    content: Optional[str] = None # 如果重命名时内容有变化可以一起传

# 允许跨域的源
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth 接口 ---

@app.post("/api/login", response_model=Token)
async def login(request: LoginRequest):
    try:
        hashed_password = get_stored_hash()
        if not hashed_password:
             logger.error("Auth file not found or corrupted")
             return fail(msg="Login service unavailable", code=Code.INTERNAL_ERROR)

        if not verify_password(request.password, hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": "admin"}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        # 如果是 HTTPException 直接抛出，否则转为 500
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login service error"
        )

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
        # 缓存检查
        if not force_refresh:
            cached_data = get_cache(CACHE_KEY_ARTICLES)
            if cached_data:
                data = json.loads(cached_data)
                return success(data=data, total=len(data), extra={"cache": "HIT"})

        # 获取全量文件树
        tree = client.repo.get_git_tree("main", recursive=True)
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

        # 整理返回列表
        final_list = []
        src_node = next((n for n in root["children"] if n["name"] == "src"), None)
        if src_node:
            for sub in src_node["children"]:
                if sub["name"] in ["posts", "drafts"]:
                    final_list.extend(sub["children"])
        
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
        cache_key = f"cms:article:{path}"
        
        if not force_refresh:
            cached_data = get_cache(cache_key)
            if cached_data:
                return success(data=json.loads(cached_data), extra={"cache": "HIT"})

        content_file = client.repo.get_contents(path)
        raw_content = base64.b64decode(content_file.content).decode('utf-8')
        
        result = {
            "path": path,
            "title": os.path.basename(path),
            "content": raw_content,
        }
        
        # 写入缓存
        set_cache(cache_key, json.dumps(result), ex=CACHE_TTL_DETAIL)

        # 返回详情，并带上关键的 SHA
        return success(data=result, sha=content_file.sha, extra={"cache": "MISS"})
    except Exception as e:
        logger.error(f"读取文件内容失败: {path} - {str(e)}", exc_info=True)
        return fail(msg=f"读取文件内容失败: {path}", code=Code.NOT_FOUND)

@app.post("/api/article/save")
def save_to_github(item: SaveArticleRequest):
    try:
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
            "branch": "main"
        }

        # 判断新建还是更新
        if not item.sha or item.sha in ["", "new"]:
            logger.info(f"正在新建文件: {item.path}")
            try:
                res = client.repo.create_file(**params)
                action = "创建"
            except Exception as create_e:
                # 容错处理：如果报错 "sha wasn't supplied" (422)，说明文件已存在，尝试获取 SHA 并转为更新
                if "sha" in str(create_e) and "supplied" in str(create_e) and "422" in str(create_e):
                    logger.warning(f"文件已存在但未提供 SHA，尝试自动修复: {item.path}")
                    try:
                        existing_file = client.repo.get_contents(item.path)
                        params["sha"] = existing_file.sha
                        res = client.repo.update_file(**params)
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
            res = client.repo.update_file(**params)
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
        if not file.content_type.startswith("image/"):
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
@app.post("/api/article/delete")
def delete_article(item: DeleteArticleRequest):
    try:
        client.repo.delete_file(
            path=item.path,
            message=f"CMS Delete: {os.path.basename(item.path)}",
            sha=item.sha,
            branch="main"
        )
        # 缓存清理
        delete_cache(CACHE_KEY_ARTICLES)
        delete_cache(f"cms:article:{item.path}")
        delete_cache(CACHE_KEY_VERSION)
        
        return success(msg="文章已从 GitHub 彻底移除")
    except Exception as e:
        return fail(msg=f"删除操作失败: {str(e)}", code=Code.GITHUB_ERROR)

# 新增：重命名接口 (GitHub API 逻辑：新建+删除)
@app.post("/api/article/rename", dependencies=[Depends(get_current_user)])
def rename_article(item: RenameArticleRequest):
    try:
        # 1. 获取内容
        content = item.content
        if not content:
            old_file = client.repo.get_contents(item.old_path)
            content = base64.b64decode(old_file.content).decode('utf-8')

        # 2. 在新路径创建文件
        create_res = client.repo.create_file(
            path=item.new_path,
            message=f"CMS Rename (Create): {item.old_path} -> {item.new_path}",
            content=content,
            branch="main"
        )

        # 3. 删除旧路径文件
        client.repo.delete_file(
            path=item.old_path,
            message=f"CMS Rename (Delete): {item.old_path}",
            sha=item.sha,
            branch="main"
        )
        
        # 缓存清理
        delete_cache(CACHE_KEY_ARTICLES)
        delete_cache(f"cms:article:{item.old_path}")
        delete_cache(f"cms:article:{item.new_path}")
        delete_cache(CACHE_KEY_VERSION)
        
        # 返回新文件的 SHA，以便前端立即继续编辑新文件
        return success(msg="重命名成功", sha=create_res['content'].sha)
    except Exception as e:
        return fail(msg=f"重命名失败: {str(e)}", code=Code.INTERNAL_ERROR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
