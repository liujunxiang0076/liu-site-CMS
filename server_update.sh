#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}开始更新服务...${NC}"

# 0. 备份重要数据 (防止 Git 更新删除配置文件)
# 迁移逻辑：如果发现旧的 auth.json 但没有新的 auth_data.json，则尝试迁移
if [ -f "backend/auth.json" ] && [ ! -f "backend/auth_data.json" ]; then
    echo "正在迁移旧的密码配置 auth.json -> auth_data.json..."
    cp backend/auth.json backend/auth_data.json
fi

# 正常备份流程
if [ -f "backend/auth_data.json" ]; then
    echo "正在备份 auth_data.json..."
    cp backend/auth_data.json backend/auth_data.json.bak
fi

# 1. 拉取最新代码
echo "正在从 Git 拉取最新代码..."
# 强制重置本地修改，确保脚本自身也能更新
git fetch --all
git reset --hard origin/main
git pull

# 1.1 恢复重要数据
if [ -f "backend/auth_data.json.bak" ]; then
    echo "正在恢复 auth_data.json..."
    mv backend/auth_data.json.bak backend/auth_data.json
fi

# 1.2 赋予自身执行权限 (防止更新后权限丢失)
chmod +x server_update.sh deploy.sh

# 检查 git pull 是否成功
if [ $? -ne 0 ]; then
    echo "Git 拉取失败，请检查网络或冲突。"
    exit 1
fi

# 1.5 清理可能存在的错误目录 (修复 backend.log 报错)
if [ -d "backend/backend.log" ]; then
    echo "检测到 backend.log 错误目录，正在自动清理..."
    rm -rf backend/backend.log
fi

# 2. 重新构建并启动
echo -e "${GREEN}正在深度清理旧容器...${NC}"

# 停止并删除容器，清理匿名卷 (关键步骤：彻底清除旧的错误状态)
docker compose down -v

echo -e "${GREEN}正在重新构建并重启服务...${NC}"
# 使用 --build 确保镜像被重新构建
docker compose up -d --build

# 3. 清理无用的旧镜像 (可选，释放空间)
docker image prune -f

echo -e "${GREEN}更新完成！${NC}"
