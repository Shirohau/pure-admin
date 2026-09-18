# OA SDK 接入说明

本次仅增加 OA SDK 登录适配，原登录页、页面样式、菜单、业务功能及账号权限保持原实现。SDK 包位于 `web/vendor/oa-jsapi-0.1.0.tgz`，不需要访问 npm 下载 `@oa/jsapi`，也不依赖 OA 主仓库的本地路径。

## 已接入的流程

员工从 OA 工作台打开本应用时，前端通过 SDK 取码，Django 后台兑换并验证签名、nonce、PKCE 和企业身份。首次登录自动创建本应用普通账号并保存身份关联，后续登录复用该账号，返回原应用格式的登录结果。前端继续使用原有菜单和权限逻辑。

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
| `OA_CA_BUNDLE` | 可选的 CA 文件路径；若使用本机自签证书，需将 CA 文件只读挂载进 Django 和 Celery 容器，并填写容器内路径 |

不再需要填写 `OA_ACCOUNT_BINDINGS`，旧文件中的这一行可以删除，代码也不再读取它。`OA_STORE_ENCRYPTION_KEY` 仍用于加密 Redis 中的令牌和会话，必须保留原值。

身份关联使用经过验证的 ECP 平台地址、企业标识和员工 `sub`，复用项目已有的 `system_user_oauth` 表，以内部来源 `oa_sso` 保存。不同平台或企业不会因为员工同名而共用账号。首次创建使用随机本地用户名，显示姓名来自已验证的 ECP 身份资料；不提供普通登录密码，不填充邮箱、手机号，不分配管理员身份或任何业务角色。

后续登录按已保存的关联找到同一个本地账号，保留管理员设置的角色、部门和其他本地资料。账号被停用后拒绝免登，不自动恢复启用。HTTP 请求、令牌刷新/验证及 WebSocket 授权检查只读取已有关联，不在后台业务请求中创建账号。并发首次登录依靠身份表已有唯一约束和数据库事务保证只保留一个账号。

此内部关联不通过通用第三方账号接口手动编辑或解绑。不按姓名、用户名、邮箱或手机号自动合并历史账号。旧的环境变量绑定不会自动转入新关联；原本地账号和业务数据保留，已有 OA 会话在关联不匹配时失效，员工需从工作台重新进入并使用自动创建的普通账号。

平台侧还需将本应用首页、可信来源和客户端关联到已发布的应用，允许该员工使用，范围为 `openid tenant profile`（`profile` 用于取得员工显示姓名）。旧客户端若仅允许 `openid tenant`，需要补充 `profile`；当前 ECP 自动创建的登录客户端已包含该范围。安装 SDK 不会自动完成应用发布和人员范围设置。

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

额外 Compose 文件给 Django 与 Celery 传入免登变量，同时为 Nginx 挂载免登所需的代理配置。原端口、Web 配置目录、数据库、Redis、证书和业务服务配置继续沿用主 Compose。原项目本身所需的 `.env`、本地配置模块、数据库初始化、证书和外部网络仍按其原部署方式准备。

本次自动建号复用已有用户表、第三方身份表及其唯一约束，没有修改数据库结构。更新本次后台源码后，需要重建 Django/Celery 镜像使新逻辑生效；仅重启旧容器不能更新镜像中的代码。在外接应用项目根目录执行：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml up -d --build --no-deps --force-recreate django celery
```

`.env.oa-sso` 中保留 `OA_SSO_ENABLED=1`、平台地址、应用凭证、应用来源、完整回调地址和存储加密密钥，删除 `OA_ACCOUNT_BINDINGS` 即可。不要把实际 Client Secret 或加密密钥写入源码及文档。

前端继续使用原 `VITE_API_URL`。生产配置为 `/api`，原 Nginx 会去掉一层 `/api`，因此浏览器访问 `/api/api/oa-sso/prepare/`，Django 实际收到 `/api/oa-sso/prepare/`，与原 `/api/token/` 接口的路径规则一致。开发环境须让前端及认证接口也经过同源 HTTPS 代理；当前开发配置的跨源 `http://127.0.0.1:8000` 不适合使用 Secure Cookie 完成免登。

如使用本机 OA 联调地址，注意容器内的 `localhost` 指向容器自身。需要让同一个 OA issuer 在浏览器与容器内都可解析、可连接且通过证书校验；不要把关闭证书验证当作解决方法。具体域名和证书取决于最终选择的应用地址。

### HTTPS 与页面来源报错

认证接口分别检查后台收到的原始访问协议及浏览器的 `Origin`。旧版本将两种失败都提示为“请从应用自己的 HTTPS 页面发起登录”；新版本分别提示，登录准备、兑换和退出接口共用同一检查。

- “应用后台未识别到 HTTPS”：检查外接应用自己的整条代理链。Django 已设置 `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`，需要紧邻 Django 的代理正确传递原始协议。如果浏览器 HTTPS 在上游终止，再通过 HTTP 到本应用 Nginx，旧配置 `proxy_set_header X-Forwarded-Proto $scheme` 会把原始协议覆盖为 `http`。修改 ECP 网关不会自动修改外接应用的代理。
- “登录页面来源与 OA_APP_ORIGIN 不一致”：确认容器中的 `OA_APP_ORIGIN` 等于浏览器实际来源，例如 `https://oa-sdktest.rekeymed.com`，不包含 `/welcome` 等路径。代理应保留浏览器的 `Origin`，不要改成 ECP 平台地址，也不要由代理伪造该头。修改 `.env.oa-sso` 后需使用额外 Compose 文件重新创建 Django/Celery 容器。

只核对应用来源、转发协议和实际代理配置即可，不需要重新生成 Client ID、Client Secret 或签名私钥。

本应用的三套 Web Nginx 配置（`conf.d`、`conf.http`、`conf.https`）统一引用 `ops/nginx/oa-proxy/forwarded-proto.conf`，仅对 `trusted-proxies.conf` 中的直接上游接受准确的 `https` 或 `http` 转发头，其他情况按实际连接协议处理。当前测试部署已确认上游是 `192.168.1.2`，因此名单中配置 `192.168.1.2/32 1;`；其他部署需要替换为自己的代理 IP，直接使用本应用 HTTPS 则可清空名单。不要将整个内网或所有地址设为可信代理。

上游负责 `oa-sdktest.rekeymed.com` 的 HTTPS 入口仍需覆盖设置 `proxy_set_header X-Forwarded-Proto $scheme;`，不能原样透传浏览器提供的值。内层 Nginx 到 Django 使用 `$oa_forwarded_proto`。同时保留原始 `Host` 和浏览器 `Origin`。

`docker-compose.oa-sso.yml` 已包含 `./ops/nginx/oa-proxy:/etc/nginx/oa-proxy:ro` 挂载；服务器可继续使用自己定制的主 Compose，只需叠加此文件，无需手动向主文件补挂载。主 Compose 已有相同挂载时，Compose 按容器挂载目标合并。首次应用此修复必须重新创建 Nginx 容器，单独 reload 不会添加挂载。同步代码并保留服务器自己的域名、证书及原有配置后，在项目根目录执行（有其他部署覆盖文件时一并沿用）：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml up -d --build --no-deps --force-recreate nginx django celery
```

此项改动不改变数据库结构，也无需重新构建前端静态资源。

如果后台代码已经更新，此次只是补齐 Nginx 挂载（如服务器将 `23767:80` 映射到 `conf.http`），更新额外 Compose 文件后只需重新创建 Nginx，不需要构建镜像或重启其他服务：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml up -d --no-deps --force-recreate nginx
```

若出现 `open() "/etc/nginx/oa-proxy/forwarded-proto.conf" failed`，说明配置挂载未生效或宿主机缺少对应文件；不是身份校验失败。确认源码中的 `ops/nginx/oa-proxy` 已同步，并使用包含该挂载的额外 Compose 文件重新创建容器。

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
