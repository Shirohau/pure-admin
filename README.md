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

## 接入 ECP 全量通讯录与事件同步

这部分由应用后台调用服务端 API。现有页面 JS SDK 继续用于免登，通讯录默认复用 `.env.oa-sso` 中的 `OA_ISSUER`、`OA_CLIENT_ID`、`OA_CLIENT_SECRET`。例如当前 ECP 地址为 `https://ecpdev.detuotech.com`，接口根地址会自动采用 `https://ecpdev.detuotech.com/api/platform`，无需再配置一套应用凭据。

### ECP 应用权限

在已经完成免登的同一项应用中，开通部门信息读、部门成员读、人员详情读，权限标识分别为 `directory.departments.read`、`directory.department_members.read`、`directory.members.read`。数据范围选择全部成员。手机号和邮箱权限按实际需要另行开通。免登可用与通讯录读取授权分别检查。

全量拉取依次获取应用 token、检查 `/auth/scopes`，从根部门 `1` 逐级调用 `/topapi/v2/department/listsubid`，再读取 `/topapi/v2/department/get` 和分页的 `/topapi/v2/user/list`。人员使用 `userid` 去重；`dept_id_list` 的全部归属另存关系表。本应用的原生用户仅有一个部门字段，使用返回列表中首个可访问部门。

### 应用入库

本应用已经有正常运行的数据库及免登配置。更新代码后，先使用现有 Compose 配置执行新增表的迁移：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml exec django python manage.py migrate oa_directory
```

叠加通讯录配置，启动应用后台及独立事件处理进程：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml -f docker-compose.ecp-directory.yml up -d django ecp-directory-worker
```

新增配置只有 `OA_DIRECTORY_SYNC_ENABLED=1`，由叠加文件设置。企业编号优先沿用已有、已验签免登记录；还没有登录记录时可通过验证事件连接自动取得，也可按 `.env.ecp-directory.example` 指定企业编号。后台、同步进程须使用同一应用及同一数据库。

先检查应用凭据能否读取完整范围；此命令不改组织数据：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml -f docker-compose.ecp-directory.yml exec django python manage.py sync_ecp_directory --dry-run
```

确认返回的部门、人员数量后，完成覆盖入库：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml -f docker-compose.ecp-directory.yml exec django python manage.py sync_ecp_directory --replace-organization --snapshot private/ecp-directory.json
```

全部数据读取、分页和部门树检查成功后才提交本地修改。旧部门和人员状态会先备份到 `backend/private/directory-backups/`。原有部门节点保留历史引用并停用，当前组织页默认展示有效部门；同步部门和人员写入现有 `system_dept`、`system_user`。重复全量同步保留已建立的本地编号。管理员、密码、角色及历史业务记录不会被删除或重建。角色中原来指定的旧部门范围，仍由应用管理员按新组织配置。

已有免登账号以经过验证的 `member_uid` 关联。旧版免登记录尚未保存该编号的，在下次成功免登时补齐关联，并保留原用户 ID、角色和业务历史；不按姓名、手机号或邮箱合并账号。仅为目录展示创建的人员没有可用密码和管理员权限。

### 事件订阅

公网回调地址为 `https://oa-sdktest.rekeymed.com/api/oa-events/callback/`。继续使用已有的 `OA_EVENT_APP_ID`、`OA_EVENT_TOKEN`、`OA_EVENT_AES_KEY`，与 ECP 应用页面配置一致。更新后台后重新验证连接，订阅人员新增、更改、离职和部门创建、修改、删除六类事件。

先启用接收并验证连接，再执行首次全量同步。回调验签、解密，将对象编号及版本保存到数据库后返回加密的 `success`；独立进程在首次全量完成后处理事件。人员事件调用 `/topapi/v2/user/get` 查询当前详情，部门事件调用部门详情接口，再更新同一批本地记录。事件按编号去重，旧版本不会覆盖较新状态，请求失败会保留事件并重试。

需要人工处理一次积累事件时：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml -f docker-compose.ecp-directory.yml exec django python manage.py process_oa_directory_events
```

离职会停用本地人员并清除归属；部门删除会停用对应部门。应用本地手动停用的账号不会因资料更新而自动启用。没有被授予通讯录范围与员工离职分别处理；收回资料读取范围本身不会撤销已有免登身份。建议应用定期执行全量核对，用于恢复漏收事件后的当前组织数据。

本次本地检查使用独立 SQLite 数据库，上游 HTTP 为明确标注的桩，涵盖 17 项入库、身份关联、权限范围、部门排序、事件及失败处理检查。它不代表服务器上的真实全量读取已执行。服务器实际结果由上述 `--dry-run`、全量命令输出及本地组织页面确认。

流程参考：[钉钉配置事件推送方式](https://open.dingtalk.com/document/development/configure-stream-push)、[开发 HTTP 事件服务](https://open.dingtalk.com/document/development/develop-stream-mode-push-server)、[人员新增事件](https://open.dingtalk.com/document/orgapp/event-v3user-add-org)、[人员离职事件](https://open.dingtalk.com/document/orgapp/event-v3user-leave-org)。应用沿用 ECP 的对象编号、事件类型与 App ID，参考钉钉的凭据、权限范围、全量读取和事件后查询详情流程。

