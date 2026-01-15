#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始部署流程...${NC}"

# 1. 检查 Docker 环境
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: 未检测到 Docker，请先安装 Docker。${NC}"
    exit 1
fi

# 2. 检查并创建 .env 配置
if [ ! -f backend/.env ]; then
    echo -e "${GREEN}检测到 backend/.env 不存在，正在从 .env.example 复制...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${RED}警告: 请务必编辑 backend/.env 文件，填入正确的 GitHub Token 和其他配置，然后重新运行此脚本！${NC}"
    exit 1
fi

# 3. 启动服务
echo -e "${GREEN}正在构建并启动服务...${NC}"
docker compose up -d --build

# 4. 检查状态
if [ $? -eq 0 ]; then
    echo -e "${GREEN}部署成功！${NC}"
    echo "前端访问地址: http://localhost (或服务器IP)"
    echo "后端API地址: http://localhost:3000"
else
    echo -e "${RED}部署失败，请检查 Docker 日志。${NC}"
fi
