<div align="center">

<h1>vue-django-docker</h1>

![License](https://img.shields.io/badge/License-MIT-2ea44f)
![Python](https://img.shields.io/badge/Python-%3E%3D%203.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/django-%3E%3D%205.2-blue?logo=django&logoColor=white)
![Node](https://img.shields.io/badge/node-%3E%3D%2022.13-blue)
[![Gitee stars](https://gitee.com/Muzi-Li-Chine/vue-django-docker/badge/star.svg?theme=dark)](https://gitee.com/Muzi-Li-Chine/vue-django-docker)

**一款基于 Vue3 + django + docker的构建的前后端项目，入门简单、开箱即用的企业级后台管理系统框架**

[快速开始](#快速开始) | [演示地址](https://admin.vuedj.com/) | [文档地址](https://docs.vuedj.com/)
</div>

---

💏 特别感谢开源项目：
- 项目灵感来源：[django-vue3-admin](https://www.django-vue-admin.com/)
- 前端基础框架：[Pure Admin](https://pure-admin.cn/)
- 前端快速开发：[FastCrud](https://fast-crud.docmirror.cn/)

# 演示地址

- 每天会自动重置数据
- 地址：https://admin.vuedj.com/
- 账号：superadmin
- 密码：admin123456

# 快速开始

## 本地开发

```bash
# 克隆项目
git clone https://gitee.com/Muzi-Li-Chine/vue-django-docker.git
# 进入项目目录
cd vue-django-docker
```

### 启动后端
- 如果要使用邮箱，第三方登录和短信验证码，请在 `extends` 中添加相关配置文件
```bash
# 进入后端项目目录
cd backend
# 安装依赖环境
pip install -r requirements.txt
# 执行迁移命令
python manage.py makemigrations
python manage.py migrate
# 初始化数据
python manage.py init
python manage.py init_area
# 启动服务
python manage.py runserver 0.0.0.0:8849
```

### 启动前端

```bash
# 进入前端项目目录
cd web
# 安装依赖环境
pnpm install
# 启动服务
pnpm dev
```

## 线上部署

>
> - 采用本地构建镜像，减少服务器资源开销
> - 用docker部署，最好有一个自己的私有镜像仓库
> - 在本地构建好镜像，然后将镜像上传到自己的私有镜像仓库
> - 在修改 `docker-compose.yml` 文件，将镜像改为自己的镜像标签

1. 下载([轩辕镜像](https://xuanyuan.cloud/))本项目用到的**基础镜像**：
    - MySQL 镜像：`mysql:8.0`
    - Redis 镜像：`redis:8.2.7`
    - Python 镜像：`python:3.11-slim`
    - Nginx 镜像：`nginx:stable-alpine3.23-perl`
2. 构建项目的后端 django 镜像
    ```bash
    # 使用 Git Bash
    bash ./build_django.sh
    ```
3. 构建项目的前端 Nginx 镜像
    ```bash
   # 使用 Git Bash
    bash ./build_nginx.sh
    ```

### 首次启动

```bash
# 登录服务器
# 克隆项目
git clone https://gitee.com/Muzi-Li-Chine/vue-django-docker.git
# 进入项目目录
cd vue-django-docker
# 启动项目
sh init.sh
```

### 更新项目

```bash
# 登录服务器
# 进入项目目录
cd vue-django-docker
# 更新项目
sh release.sh
```

