# 部署指南 (镜像版)

本指南介绍如何通过 Docker 镜像进行发布和更新。

## 1. 准备工作

### 方式一：使用 GitHub Actions 自动构建 (推荐)
如果你本地没有安装 Docker，或者希望自动化发布，可以使用 GitHub Actions。

1.  将代码推送到 GitHub。
2.  在 GitHub 仓库设置中 (Settings -> Secrets and variables -> Actions)，添加以下 Secrets：
    *   `DOCKER_USERNAME`: 你的 Docker Hub 用户名
    *   `DOCKER_PASSWORD`: 你的 Docker Hub 密码 (或 Access Token)
3.  每次推送到 `main` 分支时，GitHub 会自动构建镜像并推送到 Docker Hub。

### 方式二：本地手动构建
如果你想在本地手动构建：

#### 1.1 配置镜像地址
修改项目根目录下的 `.env.docker` 文件，填入你的 Docker Hub 用户名或镜像仓库地址。

```ini
DOCKER_IMAGE_FRONTEND=your_username/liu-site-cms-frontend:latest
DOCKER_IMAGE_BACKEND=your_username/liu-site-cms-backend:latest
```

### 1.2 构建并推送镜像
在本地运行发布脚本，将代码打包成镜像并推送到仓库。

**Windows:**
```powershell
./publish_images.ps1
```

**Linux/Mac:**
```bash
chmod +x publish_images.sh
./publish_images.sh
```

> **注意**: 首次推送前需要运行 `docker login` 登录你的镜像仓库账号。

---

## 前置要求

- 服务器需安装 **Docker** (新版 Docker Desktop 或 Docker Engine V2 已包含 Compose 插件)。

## 2. 服务器部署

### 2.1 上传必要文件
你只需要将以下文件上传到服务器：
- `docker-compose.yml`
- `.env.docker`
- `deploy_image.sh`
- `backend/.env` (或在服务器上创建)

### 2.2 首次部署与更新
在服务器上运行 `deploy_image.sh` 脚本即可自动拉取最新镜像并重启服务。

```bash
chmod +x deploy_image.sh
./deploy_image.sh
```

### 2.3 手动命令
如果你想手动操作：

```bash
# 加载环境变量
export $(grep -v '^#' .env.docker | xargs)

# 拉取最新镜像
docker-compose pull

# 启动服务
docker-compose up -d
```
