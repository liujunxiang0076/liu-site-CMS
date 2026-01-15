# Build stage
FROM node:18-alpine as build-stage

WORKDIR /app

# 安装 pnpm
RUN npm install -g pnpm

# 复制依赖定义
COPY package.json pnpm-lock.yaml* ./

# 安装依赖
RUN pnpm install

# 复制源码
COPY . .

# 构建
RUN pnpm build

# Production stage
FROM nginx:stable-alpine as production-stage

# 复制构建产物
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
