# 部署指南

## 推荐方式：使用 Git 进行部署

相比于手动上传整个文件夹，使用 **Git** 是最简单、最高效的方式。你只需要在服务器上拉取代码即可，每次更新只需几秒钟。

### 1. 首次部署

1.  **在服务器上克隆代码**
    ```bash
    # 替换为你的仓库地址
    git clone https://github.com/your-username/liu-site-CMS.git
    cd liu-site-CMS
    ```

2.  **配置环境变量**
    进入 `backend` 目录，创建 `.env` 文件。
    ```bash
    cd backend
    cp .env.example .env
    vim .env  # 填入 GitHub Token
    cd ..     # 返回根目录
    ```

3.  **启动服务**
    给予脚本执行权限并运行：
    ```bash
    chmod +x deploy.sh server_update.sh
    ./deploy.sh
    ```

---

### 2. 后续更新

当你本地修改了代码并 `git push` 后，在服务器上只需运行更新脚本：

```bash
./server_update.sh
```

这个脚本会自动执行以下操作：
1.  `git pull` 拉取最新代码。
2.  `docker compose up -d --build` 重新构建并重启服务。
3.  清理旧的 Docker 镜像。

---

## 备选方式：手动上传

如果你不使用 Git，也可以手动上传文件。

1.  将项目文件夹压缩为 `zip`。
2.  上传到服务器并解压。
3.  配置 `backend/.env`。
4.  运行 `./deploy.sh`。

## 常用命令

- **查看日志**: `docker compose logs -f`
- **停止服务**: `docker compose down`
