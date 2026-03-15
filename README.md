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

## 📦 部署（服务器 Docker）

以下步骤适用于 **Linux 服务器**（推荐 Ubuntu / Debian / CentOS）。如果你不想拉整个仓库，可以只下载 `docker-compose.yml` 进行快捷部署（需使用已发布的镜像）。

### 1. 服务器环境准备

1. 安装 Docker 与 Docker Compose 插件（示例）：
   ```bash
   # Ubuntu / Debian
   sudo apt update
   sudo apt install -y docker.io docker-compose-plugin
   sudo systemctl enable --now docker
   ```
   ```bash
   # CentOS / Rocky
   sudo yum install -y docker
   sudo systemctl enable --now docker
   sudo yum install -y docker-compose-plugin
   ```

2. 放行端口（默认）：前端 `2912`、后端 `8000`。如需修改端口，编辑 `docker-compose.yml` 中的 `ports` 映射。

3. 内存较小的服务器（1G/2G）建议开启 Swap：
   ```bash
   chmod +x enable_swap.sh
   ./enable_swap.sh
   ```

### 2. 快捷部署（不拉仓库）

1. 创建目录并下载 `docker-compose.yml`：
   ```bash
   mkdir -p liu-site-cms && cd liu-site-cms
   curl -fsSL https://github.com/liujunxiang0076/liu-site-CMS/blob/main/docker-compose.yml -o docker-compose.yml
   ```

2. 准备后端配置文件与认证文件：
   ```bash
   mkdir -p backend
   curl -fsSL <你的env示例文件地址> -o backend/.env
   echo "{}" > backend/auth_data.json
   ```
   编辑 `backend/.env`，重点填写：`GITHUB_TOKEN`（需要 `repo` 权限）、`REPO_NAME`（如 `username/your-blog`）、`SECRET_KEY`（务必修改）。

3. 配置镜像并启动：
   在当前目录新建 `.env`（用于 Docker Compose 变量），写入：
   ```bash
   DOCKER_IMAGE_FRONTEND=你的前端镜像
   DOCKER_IMAGE_BACKEND=你的后端镜像
   FRONTEND_PORT=2912
   BACKEND_PORT=8000
   TZ=Asia/Shanghai
   ```
   启动：
   ```bash
   docker compose up -d
   ```

说明：快捷部署依赖你已经将前后端镜像发布到镜像仓库。如果没有镜像，请使用“拉取代码并配置环境变量”方式进行构建部署。

### 3. 拉取代码并配置环境变量

1. 拉取项目：
   ```bash
   git clone <你的仓库地址>
   cd liu-site-CMS
   ```

2. 配置后端环境变量：
   ```bash
   cp backend/.env.example backend/.env
   ```
   编辑 `backend/.env`，重点填写：`GITHUB_TOKEN`（需要 `repo` 权限）、`REPO_NAME`（如 `username/your-blog`）、`SECRET_KEY`（务必修改）、`TG_IMG_API`（可选）。

3. 生成认证文件（避免 Docker 把文件创建成目录）：
   ```bash
   echo "{}" > backend/auth_data.json
   ```

### 4. 启动 Docker（首次部署）

```bash
docker compose up -d --build
```

检查状态与日志：
```bash
docker compose ps
docker compose logs -f backend
```

访问地址：前端 `http://服务器IP:2912`，后端 API `http://服务器IP:8000/docs`。

### 5. 更新与重部署（可选）

1. **更新代码并重建**（保留认证数据）：
   ```bash
   chmod +x server_update.sh
   ./server_update.sh
   ```
   注意：该脚本包含 `git reset --hard origin/main`，会清理本地未提交改动。

2. **彻底重置并重新部署**（清理容器、镜像、卷）：
   ```bash
   chmod +x clean_redeploy.sh
   ./clean_redeploy.sh
   ```
   注意：会删除 Docker 卷与缓存，谨慎使用。

如需更完整的排障指南，请查看 `README_DEPLOY.md`。

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

## 📦 Deployment (Docker on Server)

These steps are for **Linux servers**. If you do not want to clone the full repo, you can deploy with only `docker-compose.yml` using prebuilt images.

### 1. Server Prerequisites

1. Install Docker and Docker Compose plugin (example):
   ```bash
   # Ubuntu / Debian
   sudo apt update
   sudo apt install -y docker.io docker-compose-plugin
   sudo systemctl enable --now docker
   ```
   ```bash
   # CentOS / Rocky
   sudo yum install -y docker
   sudo systemctl enable --now docker
   sudo yum install -y docker-compose-plugin
   ```

2. Open ports (defaults): frontend `2912`, backend `8000`. To change ports, edit `ports` in `docker-compose.yml`.

3. Low-memory servers should enable swap:
   ```bash
   chmod +x enable_swap.sh
   ./enable_swap.sh
   ```

### 2. Quick Deploy (No Full Repo)

1. Create a directory and download `docker-compose.yml`:
   ```bash
   mkdir -p liu-site-cms && cd liu-site-cms
   curl -fsSL https://github.com/liujunxiang0076/liu-site-CMS/blob/main/docker-compose.yml -o docker-compose.yml
   ```

2. Prepare backend config and auth file:
   ```bash
   mkdir -p backend
   curl -fsSL <your-env-example-url> -o backend/.env
   echo "{}" > backend/auth_data.json
   ```
   Edit `backend/.env` and fill in: `GITHUB_TOKEN`, `REPO_NAME`, `SECRET_KEY`.

3. Set images and start:
   Create a `.env` in the current directory for compose vars:
   ```bash
   DOCKER_IMAGE_FRONTEND=your-frontend-image
   DOCKER_IMAGE_BACKEND=your-backend-image
   FRONTEND_PORT=2912
   BACKEND_PORT=8000
   TZ=Asia/Shanghai
   ```
   Start:
   ```bash
   docker compose up -d
   ```

Note: quick deploy requires published images. If you do not have images, use the “Clone and Configure” flow to build locally.

### 3. Clone and Configure

1. Clone repository:
   ```bash
   git clone <your-repo-url>
   cd liu-site-CMS
   ```

2. Configure backend env:
   ```bash
   cp backend/.env.example backend/.env
   ```
   Edit `backend/.env` and fill in: `GITHUB_TOKEN`, `REPO_NAME`, `SECRET_KEY`, `TG_IMG_API` (optional).

3. Create auth file (prevents Docker from creating a directory):
   ```bash
   echo "{}" > backend/auth_data.json
   ```

### 4. Start Docker (First Deploy)

```bash
docker compose up -d --build
```

Check status and logs:
```bash
docker compose ps
docker compose logs -f backend
```

Access: frontend `http://SERVER_IP:2912`, backend API `http://SERVER_IP:8000/docs`.

### 5. Update / Redeploy (Optional)

1. **Update code and rebuild** (keeps auth data):
   ```bash
   chmod +x server_update.sh
   ./server_update.sh
   ```
   Note: this script runs `git reset --hard origin/main` and will discard local changes.

2. **Hard reset** (removes containers, images, and volumes):
   ```bash
   chmod +x clean_redeploy.sh
   ./clean_redeploy.sh
   ```
   Note: this removes Docker volumes and caches.

For troubleshooting, see `README_DEPLOY.md`.

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
