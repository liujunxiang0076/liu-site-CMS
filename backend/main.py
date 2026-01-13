import os
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from github import Github

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


# 确保在这些类定义之前已经导入了 BaseModel
class SaveRequest(BaseModel):
    path: str
    title: str
    content: str
    sha: Optional[str] = None
    metadata: dict = {}


@app.get("/api/articles")
def get_articles():
    try:
        # 使用 recursive=True 参数，GitHub 会直接返回整个项目的扁平化文件树
        tree = client.repo.get_git_tree("main", recursive=True)
        articles = []
        
        for file in tree.tree:
            # 过滤出位于指定目录下且以 .md 结尾的文件
            if file.path.startswith(("src/posts/", "src/drafts/")) and file.path.endswith(".md"):
                # 识别类型
                art_type = "post" if "src/posts/" in file.path else "draft"
                
                articles.append({
                    "name": os.path.basename(file.path), # 只显示文件名
                    "path": file.path,                   # 完整路径用于后续读取
                    "type": art_type
                })
        return articles
    except Exception as e:
        print(f"获取全量树失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/save")
async def save_article(data: SaveRequest):
    try:
        # 1. 整理 Metadata
        # 确保包含用户提供的字段，并强制更新标题
        meta = data.metadata
        meta["title"] = data.title

        # 2. 构造完整的 Markdown 内容
        full_content = compose_markdown(meta, data.content)

        # 3. 决定保存路径 (如果是新文章且没路径，默认存入草稿)
        save_path = data.path if data.path else f"src/drafts/{data.title}.md"

        # 4. 调用 GitHub API
        message = f"CMS: {'Update' if data.sha else 'Create'} {data.title}"
        res = client.save_file(
            path=save_path, message=message, content=full_content, sha=data.sha
        )

        # 返回新的 sha，防止前端连续点击保存报错
        return {
            "status": "success",
            "path": save_path,
            "sha": res["content"].sha if not data.sha else res["commit"].sha,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
