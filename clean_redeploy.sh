#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}⚠️  警告: 此操作将删除所有相关容器、镜像和数据卷，并重新构建。${NC}"
echo "5秒后开始执行..."
sleep 5

# 1. 停止容器并删除卷 (清除数据残留)
echo -e "${GREEN}1. 停止容器并清理挂载卷...${NC}"
docker compose down -v

# 2. 删除旧镜像 (确保从头构建)
echo -e "${GREEN}2. 删除旧镜像...${NC}"
# 尝试删除可能存在的镜像名
docker rmi liu-site-cms-frontend liu-site-cms-backend cms-frontend cms-backend 2>/dev/null || true
# 清理悬空镜像
docker image prune -f

# 3. 清理文件系统残留
echo -e "${GREEN}3. 清理残留文件...${NC}"
rm -rf backend/backend.log
rm -rf backend/__pycache__

# 4. 强制同步最新代码
echo -e "${GREEN}4. 同步最新代码...${NC}"
git fetch --all
git reset --hard origin/main
chmod +x deploy.sh server_update.sh clean_redeploy.sh

# 5. 重新部署
echo -e "${GREEN}5. 开始重新部署...${NC}"
./deploy.sh
