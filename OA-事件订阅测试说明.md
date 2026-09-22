# 通讯录事件订阅测试

## 平台填写的请求网址

```text
https://oa-sdktest.rekeymed.com/api/oa-events/callback/
```

请保留末尾 `/`。这是应用后台接收事件的接口，不是首页，也不是免登的 `OA_REDIRECT_URI`。平台从服务器发送 POST，请求不依赖浏览器登录。直接在浏览器打开返回 405 是正常现象，不能据此判断连接验证是否通过。

当前仓库的 Nginx 会去掉 `/api/` 前缀，后端路由为 `/oa-events/callback/`；同时支持保留 `/api/` 的代理。已有 Nginx `/api/` 代理规则即可使用，无需增加公网端口。

## 配置测试应用

在测试服务器这份应用已有的 `.env.oa-sso` 中增加三项（不要覆盖原免登配置）：

```ini
OA_EVENT_APP_ID=开发者平台应用基础信息里的AppID
OA_EVENT_AES_KEY=事件订阅页面里的43位加密aes_key
OA_EVENT_TOKEN=事件订阅页面里的签名token
```

AppID 不是免登的 `OA_CLIENT_ID`。aes_key 和 token 可在平台页面点击重置生成后显示并复制，两边必须完全一致。修改密钥时需要同时更新应用配置并重新创建后台容器，再回平台重新验证。三项为空时接收接口返回 503，不影响原来的账号密码登录和 OA 免登。

这是接收应用新增的配置；平台服务器使用公网 HTTPS 回调不需要配置 `DEVELOPER_EVENT_LOCAL_CALLBACK_ORIGINS`。接收端复用应用已有的 Redis，原有 Redis 配置不变。

将本次后台代码同步到测试服务器，在应用根目录执行：

```bash
docker compose -f docker-compose.yml -f docker-compose.oa-sso.yml up -d --build --no-deps --force-recreate django
```

必须重新创建容器，单纯 `restart` 不会重新读取环境变量文件。后台恢复健康后，沿用本项目现有方式刷新 Nginx 的后台地址：

```bash
docker compose exec nginx nginx -s reload
```

本次复用已有 PyCryptodome 和 Redis 依赖，不需要修改前端或数据库结构。

## 操作与确认

1. 平台的事件订阅页填入相同的 aes_key、token 和上方请求网址，保存后点击“已完成接入、验证连接通道”。
2. 验证成功后开启需要测试的六项通讯录事件并保存。
3. 在同一企业内执行用户增加、更改、离职，或部门创建、修改、删除。
4. 平台“最近推送记录”应显示“已投递”；测试应用日志应出现对应事件。

在测试应用服务器查看日志：

```bash
docker compose logs --tail=200 django | grep OA_EVENT
```

日志含 `verified` 表示连接验证通过；`received` 表示首次收到事件；`duplicate` 表示收到同一事件的重试，未重复记录。不会记录密钥、签名和密文。

查看带中文名称、接收时间和对象标识的最近记录：

```bash
docker compose exec -T django python -m extends.oa_events.inspect
```

记录保存在已有 Redis 的独立 `vdd:oa-events:` 命名空间，最多 100 条，7 天过期；重复事件按事件 ID 去重 7 天。Redis 保存失败时返回 503，让平台重试。Redis 数据保留程度仍取决于应用现有持久化配置。

接收端会验签、解密、检查时间和 AppID，并返回加密的 `success`。它用于确认事件送达，只保存接收记录，不自动更改这份测试应用自己的员工、部门或账号权限。平台发送对象标识，不发送完整员工资料。

常见情况：验证失败先核对三项配置、两边服务器时间、后台日志和域名代理；验证通过但没有推送，检查平台 `developer-event-worker` 是否运行、订阅是否保存、业务操作是否发生在该应用所属企业。

## 本地检查结果

2026-09-22：在隔离容器中使用平台实际加密/确认校验代码和独立 Redis，7 项测试通过，覆盖验证握手、六种事件、重复记录、错误密钥/签名/AppID/过期请求拒绝、Redis 不可用、缺少配置和未知事件。

请求由 Django RequestFactory 构造；此次没有向线上域名发送回调，没有部署到测试服务器。公网代理、服务器配置和实际业务操作仍需部署后按上述步骤确认。
