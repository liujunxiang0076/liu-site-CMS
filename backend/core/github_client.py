import os
import base64
import logging
from github import Github
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("CMS-GitHub")

class GitHubClient:
    def __init__(self):
        token = (os.getenv("GITHUB_TOKEN") or "").strip()
        repo_name = (os.getenv("REPO_NAME") or "").strip()
        timeout = int(os.getenv("GITHUB_TIMEOUT", "8"))

        if not token:
            raise ValueError("GITHUB_TOKEN 未配置或为空")
        if not repo_name:
            raise ValueError("REPO_NAME 未配置或为空")
        
        # 增加 SSL 验证配置，解决部分网络环境下的 SSL 报错
        verify_ssl = os.getenv("GITHUB_VERIFY_SSL", "true").lower() == "true"
        
        # 检查代理设置
        proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        if proxy:
            logger.info(f"Detected HTTPS_PROXY: {proxy}")
        
        if not verify_ssl:
            logger.warning("SSL verification is DISABLED. This is insecure but allows connection through some proxies.")
        
        # 初始化 Github 客户端
        # verify 参数用于控制 SSL 证书验证
        self.g = Github(auth=None, login_or_token=token, verify=verify_ssl, timeout=timeout)
        
        try:
            self.repo = self.g.get_repo(repo_name)
            logger.info(f"Successfully connected to repo: {repo_name}")
        except Exception as e:
            logger.error(f"Failed to connect to GitHub repo: {e}")
            status = getattr(e, "status", None)
            if status == 401 or "Bad credentials" in str(e):
                raise ValueError("GitHub 认证失败：请检查 GITHUB_TOKEN 是否有效且有访问权限") from e
            raise e

    def get_latest_commit_sha(self, branch: str = "main") -> str:
        """获取指定分支的最新 Commit SHA，作为数据版本号"""
        try:
            branch_obj = self.repo.get_branch(branch)
            return branch_obj.commit.sha
        except Exception as e:
            logger.error(f"Failed to get branch sha: {e}")
            return None

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
