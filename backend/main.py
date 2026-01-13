import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import base64

# 导入你自定义的工具类
from core.github_client import GitHubClient
from core.image_uploader import TelegramUploader

# 1. 加载配置
load_dotenv()

# 2. 实例化 FastAPI
app = FastAPI()

# 3. 初始化工具类
# GitHubClient 内部会读取 .env 中的 GITHUB_TOKEN 和 REPO_NAME
client = GitHubClient()
uploader = TelegramUploader()

# 定义请求模型
class SaveArticleRequest(BaseModel):
    path: str
    content: str
    sha: str
    message: Optional[str] = None  # 允许为空

@app.get("/api/articles")
def get_articles():
    try:
        # 使用 client.repo 获取全量文件树
        tree = client.repo.get_git_tree("main", recursive=True)
        
        root = {"name": "Root", "children": []}
        folder_map = {"": root}

        for file in tree.tree:
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
                
                file_node = {
                    "name": path_parts[-1],
                    "path": file.path,
                    "type": "file",
                    "sha": file.sha,
                    "isDraft": "src/drafts/" in file.path
                }
                folder_map[current_path]["children"].append(file_node)

        final_list = []
        src_node = next((n for n in root["children"] if n["name"] == "src"), None)
        
        if src_node:
            posts_node = next((n for n in src_node["children"] if n["name"] == "posts"), None)
            if posts_node:
                final_list.extend(posts_node["children"])
            
            drafts_node = next((n for n in src_node["children"] if n["name"] == "drafts"), None)
            if drafts_node:
                final_list.extend(drafts_node["children"])

        return final_list

    except Exception as e:
        print(f"Tree API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/article/detail")
def get_article_detail(path: str):
    try:
        # 同样使用 client.repo
        content_file = client.repo.get_contents(path)
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

@app.post("/api/article/save")
def save_to_github(item: SaveArticleRequest):
    try:
        # 逻辑：如果有输入则用输入，没输入则系统自动生成
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        default_msg = f"CMS Update: {os.path.basename(item.path)} ({now})"
        
        final_msg = item.message.strip() if item.message and item.message.strip() else default_msg

        client.repo.update_file(
            path=item.path,
            message=final_msg,
            content=item.content,
            sha=item.sha,
            branch="main"
        )
        return {"status": "success"}
    except Exception as e:
        print(f"GitHub 保存报错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
