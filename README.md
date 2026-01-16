# Liu Site CMS

A lightweight, modern Content Management System designed for managing static blogs hosted on GitHub. It provides a user-friendly interface to write, edit, and manage your Markdown posts, syncing everything directly with your GitHub repository.

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
