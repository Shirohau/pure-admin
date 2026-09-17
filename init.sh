#!/bin/bash

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

# 如果 .env 已存在，直接退出
if [ -f "$ENV_FILE" ]; then
    echo "检测到 $ENV_FILE 已存在，跳过初始化。如需重新生成，请先删除该文件。"
    exit 0
fi

# 检查 .env.example 是否存在
if [ ! -f "$EXAMPLE_FILE" ]; then
    echo "错误: $EXAMPLE_FILE 不存在！请确保项目根目录下有 .env.example 文件。"
    exit 1
fi

# 从 .env.example 复制一份 .env
cp "$EXAMPLE_FILE" "$ENV_FILE"

echo "正在生成 MYSQL 随机密码（18位）..."
MYSQL_PASSWORD=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 18)
sed -i "s|^MYSQL_PASSWORD=.*|MYSQL_PASSWORD=$MYSQL_PASSWORD|" "$ENV_FILE"
echo "已更新 MYSQL_PASSWORD=$MYSQL_PASSWORD"

echo "正在生成 REDIS 随机密码（12位）..."
REDIS_PASSWORD=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 12)
sed -i "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|" "$ENV_FILE"
echo "已更新 REDIS_PASSWORD=$REDIS_PASSWORD"

echo "正在生成 DJANGO_SECRET_KEY（50位）..."
DJANGO_SECRET_KEY=$(head /dev/urandom | tr -dc A-Za-z0-9_- | head -c 50)
sed -i "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY|" "$ENV_FILE"
echo "已更新 DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY"

echo "正在获取服务器公网 IP..."
PUBLIC_IP=$(curl -s https://ipinfo.io/ip || curl -s https://ifconfig.me || curl -s https://icanhazip.com)
sed -i "s|^PUBLIC_IP=.*|PUBLIC_IP=$PUBLIC_IP|" "$ENV_FILE"
echo "已更新 PUBLIC_IP=$PUBLIC_IP"

ADMIN_URL="http://$PUBLIC_IP:8080"
sed -i "s|^ADMIN_URL=.*|ADMIN_URL=$PUBLIC_IP|" "$ENV_FILE"
echo "已更新 ADMIN_URL=$ADMIN_URL"

# 创建外部共享网络
docker network create shared-net

# 启动项目
echo "正在启动服务..."
docker compose up -d

# 执行 Django 命令
echo "执行数据库迁移..."
docker compose exec django python manage.py makemigrations
docker compose exec django python manage.py migrate
docker compose exec django python manage.py init
docker compose exec django python manage.py init_area
docker compose exec django python manage.py collectstatic --noinput

echo ""
echo "🎉 欢迎使用后台数据管理平台项目！"
echo "前端地址：http://$PUBLIC_IP:8080"
echo "后端地址：http://$PUBLIC_IP:8000"
echo "如访问不到，请检查防火墙、安全组及 Docker 网络配置。"