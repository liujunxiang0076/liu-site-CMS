import os
import datetime
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

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
                folder_map[current_path]["children"].append(file_node)

        # 整理返回列表
        final_list = []
        src_node = next((n for n in root["children"] if n["name"] == "src"), None)
        if src_node:
            for sub in src_node["children"]:
                if sub["name"] in ["posts", "drafts"]:
                    final_list.extend(sub["children"])
        return final_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/article/detail")
def get_article_detail(path: str):
    try:
        content_file = client.repo.get_contents(path)
        raw_content = base64.b64decode(content_file.content).decode('utf-8')
        return {
            "path": path,
            "title": os.path.basename(path),
            "content": raw_content,
            "sha": content_file.sha
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="无法获取内容")

@app.post("/api/article/save")
def save_to_github(item: SaveArticleRequest):
    try:
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
        if not item.sha or item.sha == "" or item.sha == "new":
            client.repo.create_file(**params)
        else:
            params["sha"] = item.sha
            client.repo.update_file(**params)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# 新增：重命名接口 (GitHub API 逻辑：新建+删除)
@app.post("/api/article/rename")
def rename_article(item: RenameArticleRequest):
    try:
        # 1. 如果没传内容，先获取原文件内容
        content = item.content
        if not content:
            old_file = client.repo.get_contents(item.old_path)
            content = base64.b64decode(old_file.content).decode('utf-8')

        # 2. 在新路径创建文件
        client.repo.create_file(
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
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重命名失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
