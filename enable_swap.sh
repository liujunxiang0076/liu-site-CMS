#!/bin/bash

# 检查是否已有 swap
if [ $(free | awk '/^Swap:/ {exit !$2}') ] || [ $(free | awk '/^Swap:/ {exit !$2}') ]; then
    echo "Swap 已经开启："
    free -h
else
    echo "正在创建 2GB Swap 分区..."
    
    # 1. 创建 swap 文件
    sudo fallocate -l 2G /swapfile
    if [ $? -ne 0 ]; then
        echo "fallocate 失败，尝试使用 dd..."
        sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    fi

    # 2. 设置权限
    sudo chmod 600 /swapfile

    # 3. 格式化为 swap
    sudo mkswap /swapfile

    # 4. 启用 swap
    sudo swapon /swapfile

    # 5. 永久生效
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

    echo "Swap 创建成功！"
    free -h
fi
