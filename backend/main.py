from pydantic import BaseModel
from core.parser import compose_markdown

# 定义前端传来的数据结构
class SaveRequest(BaseModel):
    path: str
    title: str
    content: str
    sha: str = None  # 如果是更新已有文章，必须带上 sha
    metadata: dict = {}

@app.post("/api/save")
async def save_article(data: SaveRequest):
    try:
        # 1. 准备 Metadata (合并标题和默认字段)
        meta = data.metadata
        meta['title'] = data.title
        # 如果是新文章，自动加上日期
        if 'date' not in meta:
            import datetime
            meta['date'] = datetime.date.today().isoformat()

        # 2. 重新组合成带 YAML 头的 Markdown 字符串
        full_markdown = compose_markdown(meta, data.content)

        # 3. 调用 GitHub API 保存
        # message 是 Git 的提交信息
        commit_message = f"CMS: {'Update' if data.sha else 'Create'} {data.title}"
        client.save_file(
            path=data.path,
            message=commit_message,
            content=full_markdown,
            sha=data.sha
        )
        return {"status": "success", "path": data.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
