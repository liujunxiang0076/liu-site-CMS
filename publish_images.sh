#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 加载配置
if [ -f .env.docker ]; then
    echo -e "${GREEN}正在加载 .env.docker 配置...${NC}"
    export $(grep -v '^#' .env.docker | xargs)
else
    echo -e "${RED}未找到 .env.docker 文件，将使用 docker-compose.yml 中的默认值。${NC}"
fi

# 2. 构建并推送
echo -e "${GREEN}开始构建并推送镜像...${NC}"

# 构建
docker compose build

if [ $? -eq 0 ]; then
    # 推送
    docker compose push
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}镜像推送成功！${NC}"
        echo "前端镜像: ${DOCKER_IMAGE_FRONTEND}"
        echo "后端镜像: ${DOCKER_IMAGE_BACKEND}"
    else
        echo -e "${RED}推送失败，请检查是否已登录 (docker login) 以及是否有权限。${NC}"
    fi
else
    echo -e "${RED}构建失败。${NC}"
fi
