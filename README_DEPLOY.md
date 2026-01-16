# 部署指南

本项目采用 **Docker Compose** 进行部署。你需要将源码上传到服务器，并在服务器上进行构建和运行。

## 1. 前置要求

- 服务器需安装 **Docker** 和 **Docker Compose** (通常包含在 Docker Desktop 或 Docker Engine 中)。

## 2. 部署步骤

### 2.1 上传代码
将整个项目目录上传至服务器。

### 2.2 配置环境变量
在服务器上，进入 `backend` 目录，创建 `.env` 文件并填入必要的配置（如 GitHub Token）。

```bash
cd backend
cp .env.example .env
vim .env
```

### 2.3 启动服务
在项目根目录下，运行部署脚本：

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**或者手动运行 Docker 命令:**
```bash
docker compose up -d --build
```

此命令会自动构建前端和后端镜像，并启动所有服务（前端、后端、Redis）。

## 3. 访问服务

- **前端页面**: `http://<服务器IP>`
- **后端 API**: `http://<服务器IP>:3000`

## 4. 维护命令

- **查看日志**:
  ```bash
  docker compose logs -f
  ```
- **停止服务**:
  ```bash
  docker compose down
  ```
- **重启服务**:
  ```bash
  docker compose restart
  ```
- **更新代码**:
  1. 拉取最新代码 (git pull) 或 重新上传代码
  2. 重新运行 `./deploy.sh` (它会重新构建镜像)
