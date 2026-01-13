import os
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from github import Github
import base64

# 如果你使用了之前建议的工具类
from core.github_client import GitHubClient
from core.image_uploader import TelegramUploader

# 1. 加载配置
load_dotenv()

# 2. 实例化 FastAPI (这是解决你报错的关键)
app = FastAPI()

# 3. 初始化工具类
# 这里的配置要对应你 .env 里的变量名
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")

# 如果你用了我们之前写的 GitHubClient 类
client = GitHubClient()
uploader = TelegramUploader()

# 定义保存请求的模型
class SaveRequest(BaseModel):
    path: str
    content: str
    sha: str
    message: Optional[str] = "docs: update article via CMS"


@app.get("/api/articles")
def get_articles():
    try:
        # 1. 获取全量文件树
        tree = client.repo.get_git_tree("main", recursive=True)
        
        root = {"name": "Root", "children": []}
        folder_map = {"": root}

        # 2. 构建树形结构
        for file in tree.tree:
            # 过滤目标路径
            if file.path.startswith(("src/posts/", "src/drafts/")) and file.path.endswith(".md"):
                path_parts = file.path.split('/')
                
                current_path = ""
                for i in range(len(path_parts) - 1):
                    part = path_parts[i]
                    parent_path = current_path
                    current_path = f"{current_path}/{part}" if current_path else part
                    
                    if current_path not in folder_map:
                        new_folder = {"name": part, "type": "folder", "children": []}
                        folder_map[parent_path]["children"].append(new_folder)
                        folder_map[current_path] = new_folder
                
                # 添加文件节点
                file_node = {
                    "name": path_parts[-1],
                    "path": file.path,
                    "type": "file",
                    "sha": file.sha,
                    "isDraft": "src/drafts/" in file.path  # 标记是否为草稿
                }
                folder_map[current_path]["children"].append(file_node)

        # 3. 【核心逻辑】裁剪层级：跳过 src，合并 posts 和 drafts
        final_list = []
        
        # 找到 src 节点
        src_node = next((n for n in root["children"] if n["name"] == "src"), None)
        
        if src_node:
            # 提取 posts 下的内容
            posts_node = next((n for n in src_node["children"] if n["name"] == "posts"), None)
            if posts_node:
                final_list.extend(posts_node["children"])
            
            # 提取 drafts 下的内容
            drafts_node = next((n for n in src_node["children"] if n["name"] == "drafts"), None)
            if drafts_node:
                final_list.extend(drafts_node["children"])

        # 返回裁剪后的列表（直接显示 2024, 2025 等文件夹）
        return final_list

    except Exception as e:
        print(f"Tree API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/article/detail")
def get_article_detail(path: str):
    """获取文章详情"""
    try:
        content_file = client.repo.get_contents(path)
        # GitHub 返回的是 Base64 编码，需要解码为字符串
        raw_content = base64.b64decode(content_file.content).decode('utf-8')
        
        return {
            "path": path,
            "title": os.path.basename(path),
            "content": raw_content,
            "sha": content_file.sha
        }
    except Exception as e:
        print(f"读取详情失败: {e}")
        raise HTTPException(status_code=500, detail="无法从 GitHub 获取内容")

@app.post("/api/article/save")  # 必须和前端 axios.post 的地址完全一致
def save_to_github(item: SaveArticleRequest):
    try:
        # 这里调用你之前写的 github 逻辑
        # 假设你的 github 仓库对象是 repo
        repo.update_file(
            path=item.path,
            message=f"CMS update: {item.path}",
            content=item.content,
            sha=item.sha
        )
        return {"status": "success"}
    except Exception as e:
        # 这样前端就能看到具体的报错原因（比如 Token 无效或 SHA 冲突）
        raise HTTPException(status_code=500, detail=str(e))
