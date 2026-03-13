# Liu Site CMS

A lightweight, modern Content Management System designed for managing static blogs hosted on GitHub. It provides a user-friendly interface to write, edit, and manage your Markdown posts, syncing everything directly with your GitHub repository.

## 中文版

一个轻量、现代的内容管理系统（CMS），用于管理托管在 GitHub 上的静态博客。提供友好的界面来编写、编辑和管理 Markdown 文章，并将更改同步到你的 GitHub 仓库。

## ✨ 功能亮点

- **📝 强大的 Markdown 编辑器**：集成 Vditor / MdEditor，提供流畅的写作体验。
- **🔄 GitHub 同步**：通过 GitHub API 直接同步，改动自动提交到仓库。
- **📂 文件管理**：在 CMS 中直接创建、编辑、重命名和删除文章。
- **🖼️ 图片上传**：内置图片上传支持（默认配置为 Telegram Bot）。
- **⚡ 高性能**：基于 FastAPI 与 Redis，响应快速并支持缓存。
- **🔐 安全**：内置认证系统，保护你的内容安全。

## 🛠️ 技术栈

- **前端**：Vue 3、Vite、TypeScript、Element Plus、Sass
- **后端**：Python FastAPI、PyGithub、Redis
- **部署**：Docker、Nginx

## 🚀 快速开始（本地开发）

### 环境依赖

- Python 3.9+
- Node.js 与 pnpm
- Redis

### 1. 后端启动

1. 进入后端目录：
   ```bash
   cd backend
   ```

2. 创建虚拟环境（可选但推荐）：
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   将 `.env.example` 复制为 `.env` 并填写配置：
   ```bash
   cp .env.example .env
   ```
   - `GITHUB_TOKEN`：GitHub 个人访问令牌（需要 repo 权限）
   - `REPO_NAME`：要管理的仓库（如 `yourname/your-blog-repo`）
   - `TG_IMG_API`：图片上传服务接口

5. 启动服务：
   ```bash
   python main.py
   ```
   后端运行在 `http://localhost:8000`，API 文档地址为 `http://localhost:8000/docs`。

### 2. 前端启动

1. 进入前端目录：
   ```bash
   cd frontend
   ```

2. 安装依赖：
   ```bash
   pnpm install
   ```

3. 启动开发服务器：
   ```bash
   pnpm dev
   ```
   前端运行在 `http://localhost:5173`。

## 🔑 默认登录

- **默认密码**：`admin123`
- 请在首次登录后通过设置页面及时修改密码。

## 📦 部署

生产环境 Docker 部署请参考 [README_DEPLOY.md](./README_DEPLOY.md)。

## ⚙️ 配置说明

系统通过环境变量配置，关键变量位于 `backend/.env`：

| 变量 | 说明 |
|------|------|
| `GITHUB_TOKEN` | GitHub 个人访问令牌（需要 repo 权限）。 |
| `REPO_NAME` | 目标仓库（例如 `username/blog`）。 |
| `TG_IMG_API` | 图片上传服务 API 地址。 |
| `SECRET_KEY` | JWT 令牌密钥，请务必修改！ |
| `REDIS_HOST` | Redis 服务地址（默认：localhost）。 |
| `REDIS_PORT` | Redis 端口（默认：6379）。 |

## 📄 许可证

[ISC](https://opensource.org/licenses/ISC)

## ✨ Features

- **📝 Rich Markdown Editor**: Integrated with powerful Markdown editors (Vditor/MdEditor) for a seamless writing experience.
- **🔄 GitHub Sync**: Direct integration with GitHub API. Changes are committed to your repository automatically.
- **📂 File Management**: Create, edit, rename, and delete articles directly from the CMS.
- **🖼️ Image Upload**: Built-in support for image uploading (configured for Telegram Bot by default).
- **⚡ High Performance**: Built with FastAPI and Redis for fast response times and caching.
- **🔐 Secure**: Authentication system to protect your content.

## 🛠️ Tech Stack

- **Frontend**: Vue 3, Vite, TypeScript, Element Plus, Sass
- **Backend**: Python FastAPI, PyGithub, Redis
- **Deployment**: Docker, Nginx

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.9+
- Node.js & pnpm
- Redis

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   ```
   - `GITHUB_TOKEN`: Your GitHub Personal Access Token (needs repo permissions).
   - `REPO_NAME`: The repository you want to manage (e.g., `yourname/your-blog-repo`).
   - `TG_IMG_API`: API endpoint for image uploading.

5. Start the server:
   ```bash
   python main.py
   ```
   The backend runs on `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Start the development server:
   ```bash
   pnpm dev
   ```
   The frontend runs on `http://localhost:5173`.

## 🔑 Default Login

- **Default Password**: `admin123`
- Please change your password immediately after the first login via the settings menu.

## 📦 Deployment

For production deployment using Docker, please refer to [README_DEPLOY.md](./README_DEPLOY.md).

## ⚙️ Configuration

The system relies on environment variables for configuration. Key variables in `backend/.env`:

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub Personal Access Token with repo scope. |
| `REPO_NAME` | Target GitHub repository (e.g., `username/blog`). |
| `TG_IMG_API` | Image upload service API URL. |
| `SECRET_KEY` | Secret key for JWT token generation. Change this! |
| `REDIS_HOST` | Redis server host (default: localhost). |
| `REDIS_PORT` | Redis server port (default: 6379). |

## 📄 License

[ISC](https://opensource.org/licenses/ISC)
