# ==============================
# 生产部署用 Nginx 镜像（docker-compose.yml 的 nginx 服务构建使用）
# 说明：web / docs / mobile 静态构建产物均由 build_nginx.sh 配合 DockerfileBuild 打包进
#      vdd-base-nginx 基础镜像并推送至 SWR，此处直接继承即可（无需重复 COPY）。
#      若需在服务器上单独重新打包静态资源，请先执行 build_nginx.sh 或 DockerfileBuild。
# ==============================
FROM swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-nginx