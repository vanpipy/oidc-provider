# 身份提供者

一个基于 FastAPI 的简化 OIDC 授权码流身份提供者骨架。

运行：

1. 安装依赖：`pip install -e .[dev]`
2. 启动开发服务器：`python -m app.cli dev`
3. 初始化数据库与演示数据（可选但推荐）：`python -m app.cli seed_demo`

演示用户与客户端：

- 用户：
  - `username`: `demo`
  - `password`: `demo1234`
- 客户端：
  - `client_id`: `demo-client`
  - `client_secret`: `secret123`
  - `redirect_uri`: `http://localhost:3000/callback`

授权码流程（简化示例）：

1. 浏览器访问：
   `http://localhost:8000/authorize?response_type=code&client_id=demo-client&redirect_uri=http://localhost:3000/callback&scope=openid%20profile%20email&state=xyz`
2. 使用 `demo/demo1234` 登录，浏览器将被重定向回 `redirect_uri`，并在查询参数中携带 `code` 和 `state`。
3. 令牌交换：向 `/token` 发送 `application/x-www-form-urlencoded` 表单：
   - `grant_type=authorization_code`
   - `code=<上一步获得的 code>`
   - `redirect_uri=http://localhost:3000/callback`
   - `client_id=demo-client`
   - `client_secret=secret123`

   成功后将返回：
   - `access_token`
   - `id_token`
   - `token_type=Bearer`
   - `expires_in`
   - `scope`

4. 使用 `access_token` 调用 `/userinfo`：
   - 请求头：`Authorization: Bearer <access_token>`
   - 返回包含 `sub`、`name`、`email` 等字段的用户信息。

相关规范与详细说明请参考：

- `specs/1-oidc-auth-code/spec.md`
- `specs/1-oidc-auth-code/quickstart.md`

