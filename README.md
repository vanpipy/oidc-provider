# 身份提供者

一个基于 FastAPI 的 OIDC 身份提供者骨架。

运行：

1. 安装依赖：`pip install -e .[dev]`
2. 运行开发服务器：`uvicorn app.main:app --reload`
3. 初始化数据库：`python -m scripts.init_db`

演示客户端：

- `client_id`: `demo-client`
- `client_secret`: `secret123`
- `redirect_uri`: `http://localhost:3000/callback`

授权码流程：

1. 浏览器访问：`http://localhost:8000/authorize?response_type=code&client_id=demo-client&redirect_uri=http://localhost:3000/callback&scope=openid%20profile%20email&state=xyz`
2. 使用 `demo/demo1234` 登录，回调将携带 `code`
3. 令牌交换：向 `/token` 发送 `grant_type=authorization_code` 等表单字段获取 `access_token` 与 `id_token`

