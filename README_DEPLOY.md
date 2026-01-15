# 部署指南

本项目支持使用 Docker Compose 进行一键部署。

## 前置要求

- 服务器需安装 **Docker** 和 **Docker Compose**。

## 部署步骤

1. **上传代码**
   将本项目代码上传至服务器。

2. **配置环境变量**
   进入 `backend` 目录，复制 `.env.example` 为 `.env`，并填入你的配置信息（如 GitHub Token）。
   ```bash
   cd backend
   cp .env.example .env
   vim .env
   ```

3. **运行部署脚本**
   在项目根目录下运行：
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

   或者直接使用 Docker 命令：
   ```bash
   docker-compose up -d --build
   ```

## 访问服务

- **前端页面**: `http://<服务器IP>`
- **后端 API**: `http://<服务器IP>:3000`

## 维护命令

- **查看日志**:
  ```bash
  docker-compose logs -f
  ```
- **停止服务**:
  ```bash
  docker-compose down
  ```
- **重启服务**:
  ```bash
  docker-compose restart
  ```
