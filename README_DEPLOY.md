# 全流程部署指南

## 常见问题解决

### 🔴 端口冲突 (Address already in use)
报错 `failed to bind host port 0.0.0.0:80/tcp` 说明服务器的 **80** 端口被占用了（可能是 Nginx/Apache）。

**解决方法 1：修改端口（推荐）**
我们已经默认将端口修改为 **8080**。
- 访问地址变为：`http://服务器IP:8080`

**解决方法 2：释放 80 端口**
如果你一定要用 80 端口，需要先停止占用该端口的程序：
```bash
# 查看谁占用了 80 端口
sudo netstat -tulpn | grep :80

# 停止相关服务 (例如 nginx)
sudo systemctl stop nginx
# 或者杀掉进程
sudo kill -9 <PID>
```
然后修改 `docker-compose.yml` 将 `8080:80` 改回 `80:80`。

### 🔴 内存不足
... (保持原有内容)

### 🔴 彻底重置 (Hard Reset)
如果遇到无法解决的玄学问题，可以使用我提供的重置脚本，它会删除所有容器、镜像和数据卷，并从头开始部署。

```bash
# 在服务器上执行
chmod +x clean_redeploy.sh
./clean_redeploy.sh
```

## 0. 服务器环境准备
... (保持原有内容)

## 4. 验证与访问

*   **前端访问**: `http://你的服务器IP:8080`
*   **后端 API**: `http://你的服务器IP:3000/docs`

... (保持原有内容)
