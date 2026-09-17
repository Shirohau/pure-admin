#!/bin/bash

# ======================
# 错误时暂停，防止窗口闪退
# ======================
set -e

# 定义错误处理函数
on_error() {
    echo "💥 脚本执行出错！请查看以上日志。"
    read -p "按回车键退出..."
    exit 1
}

# 设置 trap：任何错误都会触发 on_error
trap on_error ERR

# ======================
# 配置区
# ======================
BACKEND_DIR="./backend"
DOCKERFILE_PATH="./ops/django/DockerfileBuild"
IMAGE_NAME="swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-django"

# ======================
# 构建 Django 后端  镜像
# ======================
echo "🐳 正在构建 Docker 镜像: $IMAGE_NAME"

if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo "❌ 错误: DockerfileBuild 不存在于 $DOCKERFILE_PATH"
    exit 1
fi

export DOCKER_BUILDKIT=0
docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_NAME" .

# ======================
# 推送镜像到 私有仓库
# ======================
echo "📤 正在推送镜像到 私有仓库..."
docker push "$IMAGE_NAME"

echo "✅ 构建与推送完成！镜像已上传至：$IMAGE_NAME"
echo
read -p "💡 构建已完成，按回车键退出..."
