import frontmatter
import io

def parse_markdown(raw_content: str):
    """
    将带有 Frontmatter 的 Markdown 字符串解析为 字典
    """
    # 使用 python-frontmatter 加载内容
    post = frontmatter.loads(raw_content)
    
    # 提取 metadata (YAML部分) 和 content (正文部分)
    return {
        "metadata": post.metadata,
        "content": post.content
    }

def compose_markdown(metadata: dict, content: str):
    """
    将元数据和正文重新组合成标准的 Markdown 字符串，准备提交给 GitHub
    """
    post = frontmatter.Post(content, **metadata)
    return frontmatter.dumps(post)
