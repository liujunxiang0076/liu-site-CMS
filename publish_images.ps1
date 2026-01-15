# 编译并推送到镜像仓库脚本

# 1. 加载配置
if (Test-Path ".env.docker") {
    Write-Host "正在加载 .env.docker 配置..." -ForegroundColor Cyan
    Get-Content ".env.docker" | ForEach-Object {
        if ($_ -match "^[^#]*=") {
            $key, $value = $_ -split "=", 2
            [Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
        }
    }
} else {
    Write-Host "未找到 .env.docker 文件，将使用 docker-compose.yml 中的默认值。" -ForegroundColor Yellow
}

# 2. 检查 Docker 登录状态 (可选)
# docker login

# 3. 构建并推送
Write-Host "开始构建并推送镜像..." -ForegroundColor Green
docker-compose build
if ($?) {
    docker-compose push
    if ($?) {
        Write-Host "镜像推送成功！" -ForegroundColor Green
        Write-Host "前端镜像: $env:DOCKER_IMAGE_FRONTEND"
        Write-Host "后端镜像: $env:DOCKER_IMAGE_BACKEND"
    } else {
        Write-Host "推送失败，请检查是否已登录 (docker login) 以及是否有权限。" -ForegroundColor Red
    }
} else {
    Write-Host "构建失败。" -ForegroundColor Red
}
