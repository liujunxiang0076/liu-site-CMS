FROM python:3.9-slim

WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

## 安装依赖
COPY requirements.txt .
# 安装编译工具，防止 bcrypt 等库安装失败
RUN apt-get update && apt-get install -y build-essential libffi-dev && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
