import os
import datetime
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from core.response import success, fail

# 导入自定义工具类
from core.github_client import GitHubClient
from core.image_uploader import TelegramUploader

# 1. 加载配置
load_dotenv()

# 2. 实例化 FastAPI
app = FastAPI()

# 3. 初始化工具类
client = GitHubClient()
uploader = TelegramUploader()

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

# --- API 接口 ---

@app.get("/api/articles")
def get_articles():
    try:
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
        
        # 返回标准成功结构，携带数据总量
        return success(data=final_list, total=len(final_list))
    except Exception as e:
        logger.error(f"获取文章列表失败: {str(e)}", exc_info=True)
        return fail(msg=f"获取文章列表失败: {str(e)}", code=Code.INTERNAL_ERROR)

@app.get("/api/article/detail")
def get_article_detail(path: str):
    try:
        content_file = client.repo.get_contents(path)
        raw_content = base64.b64decode(content_file.content).decode('utf-8')
        
        # 返回详情，并带上关键的 SHA
        return success(data={
            "path": path,
            "title": os.path.basename(path),
            "content": raw_content,
        }, sha=content_file.sha)
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
            res = client.repo.create_file(**params)
            action = "创建"
        else:
            logger.info(f"正在更新文件: {item.path} (SHA: {item.sha})")
            params["sha"] = item.sha
            res = client.repo.update_file(**params)
            action = "更新"
            
        # 核心：必须返回新的 SHA，否则前端无法连续保存
        new_sha = res['content'].sha
        logger.info(f"文件{action}成功: {item.path}, New SHA: {new_sha}")
        return success(msg=f"文件{action}成功", sha=new_sha)
    except Exception as e:
        logger.error(f"保存失败: {str(e)}", exc_info=True)
        # 处理常见错误：SHA 冲突
        if "does not match" in str(e):
            return fail(msg="保存失败：GitHub 版本冲突，请刷新页面重新编辑", code=Code.GITHUB_ERROR)
        return fail(msg=f"保存失败: {str(e)}", code=Code.INTERNAL_ERROR)

# 新增：图片上传接口
@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    try:
        # 1. 验证文件类型
        if not file.content_type.startswith("image/"):
            return fail(msg="仅支持上传图片文件", code=Code.PARAM_ERROR)
        
        # 2. 验证文件大小 (例如限制 5MB)
        # 注意：UploadFile 是流式读取，直接读取大小可能不准，这里简单跳过或在读取时判断
        # content = await file.read()
        # if len(content) > 5 * 1024 * 1024:
        #     return fail(msg="图片大小不能超过 5MB", code=Code.PARAM_ERROR)
        # await file.seek(0) # 重置指针

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
        return success(msg="文章已从 GitHub 彻底移除")
    except Exception as e:
        return fail(msg=f"删除操作失败: {str(e)}", code=Code.GITHUB_ERROR)

# 新增：重命名接口 (GitHub API 逻辑：新建+删除)
@app.post("/api/article/rename")
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
        
        # 返回新文件的 SHA，以便前端立即继续编辑新文件
        return success(msg="重命名成功", sha=create_res['content'].sha)
    except Exception as e:
        return fail(msg=f"重命名失败: {str(e)}", code=Code.INTERNAL_ERROR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
