import os
import base64
from github import Github
from dotenv import load_dotenv

load_dotenv()

class GitHubClient:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("REPO_NAME")
        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)

    def get_file_content(self, path: str):
        """读取文件内容和 SHA"""
        content_file = self.repo.get_contents(path)
        # GitHub 返回的是 Base64 编码，需要解码
        decoded_content = base64.b64decode(content_file.content).decode("utf-8")
        return decoded_content, content_file.sha

    def save_file(self, path: str, message: str, content: str, sha: str = None):
        """创建或更新文件"""
        if sha:
            return self.repo.update_file(path, message, content, sha)
        else:
            return self.repo.create_file(path, message, content)
