# OA SDK 接入说明

本次仅增加 OA SDK 登录适配，原登录页、页面样式、菜单、业务功能及账号权限保持原实现。SDK 包位于 `web/vendor/oa-jsapi-0.1.0.tgz`，不需要访问 npm 下载 `@oa/jsapi`，也不依赖 OA 主仓库的本地路径。

## 已接入的流程

员工从 OA 工作台打开本应用时，前端通过 SDK 取码，Django 后台兑换并验证签名、nonce、PKCE 和企业身份，再映射到已配置的本应用账号，返回原应用格式的登录结果。前端继续使用原有菜单和权限逻辑。

直接打开本应用且没有 OA 启动上下文时，仍使用原账号密码登录。OA 访问令牌与客户端密钥保存在后台，不交给前端；前端仍按原应用方式保存本应用自己的登录令牌。

OA 登录建立的本地会话存入现有 Redis 的独立 `vdd:oa-sso:` 命名空间并加密。后续 HTTP 请求、令牌刷新/验证和 WebSocket 连接或消息会重新检查该 OA 授权。普通登录不增加 OA 授权要求。退出先停止本地会话，再由现有 Celery worker/beat 每 30 秒处理持久撤销队列。

## 开启前需要填写

复制根目录 `.env.oa-sso.example` 为 `.env.oa-sso`。文件已加入 Git 忽略规则，不把实际密钥提交到仓库。

| 配置 | 填写方式 |
| --- | --- |
| `OA_SSO_ENABLED` | 实际配置齐全后改为 `1`，模板默认关闭 |
| `OA_ISSUER` | 可由浏览器和 Django、Celery 容器访问且证书可信的 OA HTTPS 来源 |
| `OA_CLIENT_ID` / `OA_CLIENT_SECRET` | 平台为本应用签发的登录客户端凭据，不使用开发者 AppSecret，也不共用其他示例应用的凭据 |
| `OA_APP_ORIGIN` | 本应用实际 HTTPS 来源，如 `https://app.example.com` |
| `OA_REDIRECT_URI` | 平台登记的准确完整地址，如 `https://app.example.com/` |
| `OA_STORE_ENCRYPTION_KEY` | 固定保存的随机 32 字节密钥，以 64 位十六进制填写 |
| `OA_ACCOUNT_BINDINGS` | 明确的 OA 身份到本地账号映射，格式见下文 |
| `OA_CA_BUNDLE` | 可选的 CA 文件路径；若使用本机自签证书，需将 CA 文件只读挂载进 Django 和 Celery 容器，并填写容器内路径 |

账号映射示意（所有值需要替换，不是可直接使用的测试账号）：

```json
[
  {
    "tenant_id": "平台确认的企业标识",
    "sub": "平台确认的员工身份主体标识",
    "username": "本应用中已经存在的账号"
  }
]
```

`sub` 不是姓名或用户名，也不能自行假定等于数据库用户 ID。平台侧确认具体测试员工的主体标识后，应用管理员再显式绑定。一个 OA 企业与主体组合只能配置一次。未匹配、账号不存在或账号停用时拒绝免登；不自动创建账号、不自动赋予管理员角色。

平台侧还需将本应用首页、可信来源和客户端关联到已批准的应用，允许该员工使用，范围为 `openid tenant`。当前这些配置不会因安装 SDK 自动完成。

## 依赖与部署接入

前端新增的依赖和锁文件均指向随源码提供的安装包。在 `web` 目录按原项目方式执行 `pnpm install --frozen-lockfile`，之后沿用原页面构建流程。

后端 `requirements.txt` 新增 `PyJWT[crypto]` 用于 RS256 验签。已有 Docker 基础镜像不会因为源码变化自动安装依赖，需要按原项目方式更新 Python 依赖镜像。本地只构建、不推送的命令为：

```powershell
docker build -f ops/django/DockerfileBuild -t swr.cn-southwest-2.myhuaweicloud.com/muzili/vdd-base-django .
```

原 `build_django.sh` 同时包含镜像推送；仅本机验证时不要将它误当成纯构建命令。完成原项目的前端和后端构建后，叠加免登环境配置启动：

```powershell
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml up -d --build
```

额外 Compose 文件只给 Django 与 Celery 传入免登变量，未修改原端口、数据库、Redis、证书和业务服务配置。原项目本身所需的 `.env`、本地配置模块、数据库初始化、证书和外部网络仍按其原部署方式准备。

前端继续使用原 `VITE_API_URL`。生产配置为 `/api`，原 Nginx 会去掉一层 `/api`，因此浏览器访问 `/api/api/oa-sso/prepare/`，Django 实际收到 `/api/oa-sso/prepare/`，与原 `/api/token/` 接口的路径规则一致。开发环境须让前端及认证接口也经过同源 HTTPS 代理；当前开发配置的跨源 `http://127.0.0.1:8000` 不适合使用 Secure Cookie 完成免登。

如使用本机 OA 联调地址，注意容器内的 `localhost` 指向容器自身。需要让同一个 OA issuer 在浏览器与容器内都可解析、可连接且通过证书校验；不要把关闭证书验证当作解决方法。具体域名和证书取决于最终选择的应用地址。

应用首页请求会携带一次性 `oa_ticket`。部署代理应对携带该参数的请求关闭访问日志，并设置 `Referrer-Policy: no-referrer`；认证接口不记录请求体和授权头。原 Nginx 日志配置未在本次接入中整体调整，需在实际测试来源对应的代理处落实。

## 验证步骤

1. 使用原密码登录确认目标本地账号及其权限已经配置好，然后退出。
2. 使用已绑定的测试员工登录 OA，从工作台点击本应用。
3. 本应用无需再输入密码，进入原页面，右上角显示所绑定的本地账号；菜单权限与该账号原权限一致。
4. 点击原退出按钮，返回原登录页；再次免登需从 OA 工作台重新打开。
5. 未绑定员工、未登记来源、重复使用票据或登录码应被拒绝。停用员工后，后续业务请求不得继续凭旧 OA 会话通过。

接口路径为 `config/`、`prepare/`、`complete/`、`logout/`，都挂载在 Django 的 `/api/oa-sso/` 下。失败响应只提供脱敏原因；没有添加新的页面、登录表单或调试页面。

## 当前待补的信息

尚未填写实际 issuer、应用 HTTPS 地址、登录客户端凭据，以及测试员工与本地账号的映射；模板默认关闭。接入代码完成不等于这些部署信息已具备。此应用也没有新增 OA 刷新令牌轮换和后台退出推送接收端，本次 OA 授权到期后从工作台重新打开。
