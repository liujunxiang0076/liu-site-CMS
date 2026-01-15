#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}开始基于镜像的部署流程...${NC}"

# 1. 检查文件
if [ ! -f .env.docker ]; then
    echo -e "${RED}错误: 未找到 .env.docker 配置文件。${NC}"
    exit 1
fi

# 加载镜像变量
export $(grep -v '^#' .env.docker | xargs)

# 2. 检查并创建 .env 配置
if [ ! -f backend/.env ]; then
    echo -e "${GREEN}检测到 backend/.env 不存在，正在从 .env.example 复制...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${RED}警告: 请务必编辑 backend/.env 文件，填入正确的 GitHub Token，然后重新运行此脚本！${NC}"
    exit 1
fi

# 3. 拉取最新镜像
echo -e "${GREEN}正在拉取最新镜像...${NC}"
echo "Frontend: ${DOCKER_IMAGE_FRONTEND}"
echo "Backend:  ${DOCKER_IMAGE_BACKEND}"

docker-compose pull

# 4. 启动服务
echo -e "${GREEN}正在启动服务...${NC}"
docker-compose up -d

# 5. 检查状态
if [ $? -eq 0 ]; then
    echo -e "${GREEN}部署成功！${NC}"
    echo "服务已基于最新镜像运行。"
else
    echo -e "${RED}部署失败。${NC}"
fi
