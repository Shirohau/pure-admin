#!/bin/bash
echo "🔄 拉取最新代码..."
git pull

echo "🛑 停止并移除旧服务..."
docker compose down

echo "📥 拉取最新前端镜像（非构建服务）..."
docker pull swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-nginx

echo "🏗️ 重新构建并启动服务..."
docker compose up -d --build

echo "🗃️ 执行数据库迁移..."
docker compose exec django python manage.py makemigrations --no-input
docker compose exec django python manage.py migrate --no-input

echo "✅ 部署完成！"