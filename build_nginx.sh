#!/bin/bash

# ======================
# 构建全部（默认）
# bash ./ops/nginx/build.sh

# 只构建 Web（docs、mobile 必须已有 dist）
# bash ./ops/nginx/build.sh --web

# 只构建 Docs（web、mobile 必须已有 dist）
# bash ./ops/nginx/build.sh --docs

# 只构建 Mobile（web、docs 必须已有 dist）
# bash ./ops/nginx/build.sh --mobile

# 跳过构建，直接用现有的 dist 打包镜像（用于重试推送或测试 Dockerfile）
# bash ./ops/nginx/build.sh --skip-build

# ======================

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

WEB_DIR="./web"
DOCS_DIR="./docs"
MOBILE_DIR="./mobile"
WEB_DIST="$WEB_DIR/dist"
DOCS_DIST="$DOCS_DIR/docs/.vuepress/dist"
MOBILE_DIST="$MOBILE_DIR/dist/build/h5"
DOCKERFILE_PATH="./ops/nginx/DockerfileBuild"
IMAGE_NAME="swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-nginx"

# 默认行为：构建三者
BUILD_WEB=true
BUILD_DOCS=true
BUILD_MOBILE=true
SKIP_BUILD=false

# ======================
# 解析命令行参数
# ======================
while [[ $# -gt 0 ]]; do
    case $1 in
        --web)
            BUILD_WEB=true
            BUILD_DOCS=false
            BUILD_MOBILE=false
            shift
            ;;
        --docs)
            BUILD_WEB=false
            BUILD_DOCS=true
            BUILD_MOBILE=false
            shift
            ;;
        --mobile)
            BUILD_WEB=false
            BUILD_DOCS=false
            BUILD_MOBILE=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            BUILD_WEB=false
            BUILD_DOCS=false
            BUILD_MOBILE=false
            shift
            ;;
        *)
            echo "❌ 未知参数: $1"
            echo "用法: $0 [--web] [--docs] [--mobile] [--skip-build]"
            exit 1
            ;;
    esac
done

# ======================
# 构建 Web
# ======================
if [ "$SKIP_BUILD" = false ] && [ "$BUILD_WEB" = true ]; then
    echo "🚀 构建 Web 前端..."
    cd "$WEB_DIR"
    if [ ! -f "package.json" ]; then
        echo "❌ 错误: $WEB_DIR 中未找到 package.json"
        exit 1
    fi
    NODE_OPTIONS="--max-old-space-size=4096" pnpm build
    cd -
fi

# ======================
# 构建 Docs
# ======================
if [ "$SKIP_BUILD" = false ] && [ "$BUILD_DOCS" = true ]; then
    echo "📚 构建 Docs 前端..."
    cd "$DOCS_DIR"
    if [ ! -f "package.json" ]; then
        echo "❌ 错误: $DOCS_DIR 中未找到 package.json"
        exit 1
    fi
    NODE_OPTIONS="--max-old-space-size=4096" pnpm docs:build
    cd -
fi

# ======================
# 构建 Mobile（uni-app H5）
# ======================
if [ "$SKIP_BUILD" = false ] && [ "$BUILD_MOBILE" = true ]; then
    echo "📱 构建 Mobile 前端（uni-app H5）..."
    cd "$MOBILE_DIR"
    if [ ! -f "package.json" ]; then
        echo "❌ 错误: $MOBILE_DIR 中未找到 package.json"
        exit 1
    fi
    NODE_OPTIONS="--max-old-space-size=4096" pnpm build:h5
    cd -
fi

# ======================
# 确保 Docker 构建所需的目录存在（即使为空）
# ======================
if [ ! -d "$WEB_DIST" ]; then
    echo "⚠️  $WEB_DIST 不存在，创建空目录以避免 Docker COPY 失败"
    mkdir -p "$WEB_DIST"
fi

if [ ! -d "$DOCS_DIST" ]; then
    echo "⚠️  $DOCS_DIST 不存在，创建空目录以避免 Docker COPY 失败"
    mkdir -p "$DOCS_DIST"
fi

if [ ! -d "$MOBILE_DIST" ]; then
    echo "⚠️  $MOBILE_DIST 不存在，创建空目录以避免 Docker COPY 失败"
    mkdir -p "$MOBILE_DIST"
fi


# ======================
# 构建 Docker 镜像
# ======================
echo "🐳 构建 Docker 镜像: $IMAGE_NAME"
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo "❌ 错误: Dockerfile 不存在于 $DOCKERFILE_PATH"
    exit 1
fi
export DOCKER_BUILDKIT=0
docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_NAME" .

# ======================
# 推送镜像
# ======================
echo "📤 推送镜像到 SWR..."
docker push "$IMAGE_NAME"

echo "✅ 构建与推送完成！镜像已上传至：$IMAGE_NAME"
echo
read -p "💡 构建已完成，按回车键退出..."