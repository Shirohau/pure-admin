# OA SDK 接入说明

本次仅增加 OA SDK 登录适配，原登录页、页面样式、菜单、业务功能及账号权限保持原实现。SDK 包位于 `web/vendor/oa-jsapi-0.1.0.tgz`，不需要访问 npm 下载 `@oa/jsapi`，也不依赖 OA 主仓库的本地路径。

## 已接入的流程

员工从 OA 工作台打开本应用时，前端通过 SDK 取码，Django 后台兑换并验证签名、nonce、PKCE 和企业身份。首次登录自动创建本应用普通账号并保存身份关联，后续登录复用该账号，返回原应用格式的登录结果。前端继续使用原有菜单和权限逻辑。

直接打开本应用且没有 OA 启动上下文时，仍使用原账号密码登录。OA 访问令牌与客户端密钥保存在后台，不交给前端；前端仍按原应用方式保存本应用自己的登录令牌。

OA 登录建立的本地会话存入现有 Redis 的独立 `vdd:oa-sso:` 命名空间并加密。后续 HTTP 请求、令牌刷新/验证和 WebSocket 连接或消息会重新检查该 OA 授权。普通登录不增加 OA 授权要求。退出先停止本地会话，再由现有 Celery worker/beat 每 30 秒处理持久撤销队列。

## 开启前需要填写

复制根目录 `.env.oa-sso.example` 为 `.env.oa-sso`。文件已加入 Git 忽略规则，不把实际密钥提交到仓库。

### 仅测试免登时

在已有 `.env.oa-sso` 中增加 `OA_SSO_TEST_MODE=1`，即可跳过后台对代理转发协议的判断。适用于浏览器访问 HTTPS、上游再通过 HTTP 转给外接应用的测试部署，不需要为此修改 Nginx、增加代理信任名单或配置挂载。此模式降低了后台对访问协议的检查要求，仅用于隔离的测试环境；正式部署恢复为 `0` 并配置正确的 HTTPS 转发。

测试模式下最少的免登配置如下（凭据填写本应用实际值）：

```ini
OA_SSO_ENABLED=1
OA_SSO_TEST_MODE=1
OA_ISSUER=https://ecpdev.detuotech.com
OA_CLIENT_ID=填写实际客户端ID
OA_CLIENT_SECRET=填写实际客户端密钥
OA_REDIRECT_URI=https://oa-sdktest.rekeymed.com/welcome
```

其他应用原有环境配置继续使用。测试模式允许省略 `OA_APP_ORIGIN`，从完整回调地址取得；如果显式填写，仍应为实际应用的 HTTPS 来源。允许省略 `OA_STORE_ENCRYPTION_KEY`，后台从现有 `DJANGO_SECRET_KEY` 按平台及客户端派生固定加密密钥，不会每次启动随机生成。已有存储密钥时建议保留，代码优先使用原值；删除旧密钥、变更 Django 密钥或切换加密方式会使原会话不可读，需要重新登录。模板中的密钥占位文字不是空值，应删除该行或填写有效密钥。

登录准备、登录完成、退出三个接口共同使用测试模式。浏览器仍须通过同源 HTTPS 访问，页面来源校验、Secure Cookie、一次性事务、PKCE、nonce、身份签名与有效期、企业身份匹配、会话失效检查均正常执行。测试模式只申请 `openid tenant`，不要求 `profile`；平台未返回姓名时，自动创建的账号显示为“ECP 员工”加身份摘要。

首次免登自动建立普通本地账号，不要求提前创建账号、分配业务角色或填写员工绑定。账号被停用后仍拒绝登录，业务操作仍遵守原有权限；测试模式不会把员工设为管理员。免登成功后业务页面提示无权限不代表免登失败，可用登录完成接口的“登录成功”响应及本应用登录状态判断。

后台源码更新后，使用原主 Compose 叠加免登配置重新创建后台服务，前端和 Nginx 不需要因本次测试模式改动重新构建：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml up -d --build --no-deps --force-recreate django celery
```

### 配置说明

| 配置 | 填写方式 |
| --- | --- |
| `OA_SSO_ENABLED` | 实际配置齐全后改为 `1`，模板默认关闭 |
| `OA_SSO_TEST_MODE` | 默认 `0`；仅测试时设为 `1`，具体简化项见上文 |
| `OA_ISSUER` | 可由浏览器和 Django、Celery 容器访问且证书可信的 OA HTTPS 来源 |
| `OA_CLIENT_ID` / `OA_CLIENT_SECRET` | 平台为本应用签发的登录客户端凭据，不使用开发者 AppSecret，也不共用其他示例应用的凭据 |
| `OA_APP_ORIGIN` | 本应用实际 HTTPS 来源，如 `https://app.example.com`；测试模式可从回调地址自动取得 |
| `OA_REDIRECT_URI` | 平台登记的准确完整地址，如 `https://app.example.com/` |
| `OA_STORE_ENCRYPTION_KEY` | 固定保存的随机 32 字节密钥，以 64 位十六进制填写；测试模式未填写时使用上述派生方式 |
| `OA_CA_BUNDLE` | 可选的 CA 文件路径；若使用本机自签证书，需将 CA 文件只读挂载进 Django 和 Celery 容器，并填写容器内路径 |

不再需要填写 `OA_ACCOUNT_BINDINGS`，旧文件中的这一行可以删除，代码也不再读取它。Redis 中的令牌和会话始终加密；已配置 `OA_STORE_ENCRYPTION_KEY` 时保留原值可避免已有会话失效。

身份关联使用经过验证的 ECP 平台地址、企业标识和员工 `sub`，复用项目已有的 `system_user_oauth` 表，以内部来源 `oa_sso` 保存。不同平台或企业不会因为员工同名而共用账号。首次创建使用随机本地用户名，显示姓名来自已验证的 ECP 身份资料；不提供普通登录密码，不填充邮箱、手机号，不分配管理员身份或任何业务角色。

后续登录按已保存的关联找到同一个本地账号，保留管理员设置的角色、部门和其他本地资料。账号被停用后拒绝免登，不自动恢复启用。HTTP 请求、令牌刷新/验证及 WebSocket 授权检查只读取已有关联，不在后台业务请求中创建账号。并发首次登录依靠身份表已有唯一约束和数据库事务保证只保留一个账号。

此内部关联不通过通用第三方账号接口手动编辑或解绑。不按姓名、用户名、邮箱或手机号自动合并历史账号。旧的环境变量绑定不会自动转入新关联；原本地账号和业务数据保留，已有 OA 会话在关联不匹配时失效，员工需从工作台重新进入并使用自动创建的普通账号。

平台侧还需将本应用首页、可信来源和客户端关联到已发布的应用，允许该员工使用。正常模式范围为 `openid tenant profile`（`profile` 用于取得员工显示姓名），测试模式范围为 `openid tenant`。旧客户端若仅允许 `openid tenant`，在正常模式下需要补充 `profile`；当前 ECP 自动创建的登录客户端已包含该范围。安装 SDK 不会自动完成应用发布和人员范围设置。

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

本次自动建号复用已有用户表、第三方身份表及其唯一约束，没有修改数据库结构。更新本次后台源码后，需要重建 Django/Celery 镜像使新逻辑生效；仅重启旧容器不能更新镜像中的代码。在外接应用项目根目录执行：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml up -d --build --no-deps --force-recreate django celery
```

`.env.oa-sso` 中保留 `OA_SSO_ENABLED=1`、平台地址、应用凭证、应用来源、完整回调地址和存储加密密钥，删除 `OA_ACCOUNT_BINDINGS` 即可。不要把实际 Client Secret 或加密密钥写入源码及文档。

前端继续使用原 `VITE_API_URL`。生产配置为 `/api`，原 Nginx 会去掉一层 `/api`，因此浏览器访问 `/api/api/oa-sso/prepare/`，Django 实际收到 `/api/oa-sso/prepare/`，与原 `/api/token/` 接口的路径规则一致。开发环境须让前端及认证接口也经过同源 HTTPS 代理；当前开发配置的跨源 `http://127.0.0.1:8000` 不适合使用 Secure Cookie 完成免登。

如使用本机 OA 联调地址，注意容器内的 `localhost` 指向容器自身。需要让同一个 OA issuer 在浏览器与容器内都可解析、可连接且通过证书校验；不要把关闭证书验证当作解决方法。具体域名和证书取决于最终选择的应用地址。

应用首页请求会携带一次性 `oa_ticket`。部署代理应对携带该参数的请求关闭访问日志，并设置 `Referrer-Policy: no-referrer`；认证接口不记录请求体和授权头。原 Nginx 日志配置未在本次接入中整体调整，需在实际测试来源对应的代理处落实。

## 验证步骤

1. 在 OA 发布应用并将测试员工加入可用范围，外接应用启用免登配置。
2. 使用该员工登录 OA，从工作台点击本应用；无需提前创建本地账号或填写身份绑定。
3. 本应用无需再输入密码，进入原页面。首次创建的账号没有管理员和业务角色；业务菜单由本应用管理员授权。再次从工作台进入时复用原账号，不重复建号。
4. 点击原退出按钮，返回原登录页；再次免登需从 OA 工作台重新打开。
5. 不在应用可用范围的员工、未登记来源、重复使用票据或登录码应被拒绝。在 OA 停用员工或在本应用停用账号后，后续业务请求不得继续凭旧 OA 会话通过。
6. 同时发起同一员工的首次登录，确认只保留一个本地账号及一条身份关联；确认其他企业员工和本地同名账号不被误合并。

接口路径为 `config/`、`prepare/`、`complete/`、`logout/`，都挂载在 Django 的 `/api/oa-sso/` 下。失败响应只提供脱敏原因；没有添加新的页面、登录表单或调试页面。

## 当前待补的信息

实际 issuer、应用 HTTPS 地址和登录客户端凭据由部署环境填写；模板默认关闭，不再需要提供员工与本地账号的映射。此应用没有新增 OA 刷新令牌轮换和后台退出推送接收端，OA 授权到期后从工作台重新打开。
