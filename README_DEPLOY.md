# 全流程部署指南

本文档提供从零开始在服务器上部署 CMS 的详细步骤。

## 0. 服务器环境准备

在开始之前，请确保你的服务器（推荐 Ubuntu 20.04/22.04 或 CentOS 7+）已安装必要软件。

### 安装 Git
**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y git
```
**CentOS:**
```bash
sudo yum install -y git
```

### 安装 Docker & Docker Compose
如果你还没有安装 Docker，可以使用官方一键脚本（适用于大多数 Linux 发行版）：

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | bash

# 2. 启动 Docker 并设置开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 3. (可选) 验证安装
docker compose version
```

---

## 1. 获取代码

登录你的服务器，选择一个目录（例如 `/opt` 或用户主目录），拉取代码。

```bash
# 进入用户主目录
cd ~

# 克隆仓库 (请将 URL 替换为你自己的 GitHub 仓库地址)
git clone https://github.com/your-username/liu-site-CMS.git

# 进入项目目录
cd liu-site-CMS
```

---

## 2. 关键配置 (必做)

这是最重要的一步，后端需要 GitHub Token 才能读写你的文章仓库。

1.  **进入后端目录**
    ```bash
    cd backend
    ```

2.  **创建配置文件**
    ```bash
    cp .env.example .env
    ```

3.  **编辑配置文件**
    使用 `vim` 或 `nano` 编辑 `.env` 文件：
    ```bash
    nano .env
    ```
    
    **你需要修改的内容：**
    *   `GITHUB_TOKEN`: 填入你的 GitHub Personal Access Token (权限需勾选 `repo`)。
    *   `REPO_NAME`: 填入你的文章仓库地址 (例如 `yourname/blog-posts`)。
    *   `TG_IMG_API`: (可选) 如果你使用 Telegram 图床，填入 API 地址。

    *按 `Ctrl+O` 保存，按 `Enter` 确认，按 `Ctrl+X` 退出。*

4.  **返回根目录**
    ```bash
    cd ..
    ```

---

## 3. 启动服务

我们提供了一键启动脚本，它会自动构建 Docker 镜像并运行服务。

```bash
# 1. 赋予脚本执行权限
chmod +x deploy.sh server_update.sh

# 2. 执行部署
./deploy.sh
```

**等待几分钟**，直到看到 "部署成功" 的提示。

---

## 4. 验证与访问

*   **前端访问**: 打开浏览器，访问 `http://你的服务器IP`
*   **后端 API**: `http://你的服务器IP:3000/docs` (可以看到 API 文档)

如果无法访问，请检查服务器的防火墙/安全组是否开放了 **80** 和 **3000** 端口。

---

## 5. 日后更新代码

当你本地修改了代码并推送到 GitHub 后，在服务器上只需执行一个命令即可更新：

```bash
# 在项目根目录下运行
./server_update.sh
```
此脚本会自动拉取最新代码、重新构建镜像并重启服务。

---

## 6. 常用维护命令

*   **查看运行日志** (排查报错用):
    ```bash
    docker compose logs -f
    ```
    *(按 `Ctrl+C` 退出日志查看)*

*   **停止所有服务**:
    ```bash
    docker compose down
    ```

*   **重启所有服务**:
    ```bash
    docker compose restart
    ```
