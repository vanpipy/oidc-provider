# Quickstart：简化 OIDC Provider 授权码流

本指南面向开发者与测试人员，帮助在本地快速运行并验证授权码登录 + UserInfo 获取的完整流程。

---

## 1. 环境准备

### 1.1 安装依赖

在项目根目录 `d:/Project/oidc-provider` 下：

```bash
pip install -e .[dev]
```

确保 Python 版本为 3.10+。

### 1.2 初始化数据库与演示数据

项目提供了多种初始化方式，可以任选一种：

1. 通过 CLI 初始化基础数据：

   ```bash
   python -m app.cli init-db
   ```

   该命令会：

   - 创建数据库表；
   - 创建默认用户 `admin` 与默认客户端 `client`。

2. 初始化 demo 用户与 demo 客户端（推荐用于演示授权码流）：

   ```bash
   python -m app.cli seed_demo
   ```

   该命令会在数据库中确保存在：

   - 用户：
     - `username = "demo"`
     - `email = "demo@example.com"`
     - `password = "demo1234"`
   - 客户端：
     - `client_id = "demo-client"`
     - `client_secret = "secret123"`
     - `redirect_uris = ["http://localhost:3000/callback"]`
     - `scopes = ["openid", "profile", "email"]`

---

## 2. 启动服务

在项目根目录下运行：

```bash
python -m app.cli dev
```

或使用 `pyproject.toml` 中的脚本（等价效果）：

```bash
python -m app.cli serve
```

默认服务地址为：

- 应用根：`http://localhost:8000`
- Issuer（在配置中）：`http://localhost:8000`

---

## 3. 手工验证授权码流程（S1）

本小节演示如何手工走通“授权码登录 + UserInfo 获取成功路径”（场景 S1）。

### 3.1 访问 Discovery 文档（可选）

在浏览器或命令行中访问：

```bash
curl http://localhost:8000/.well-known/openid-configuration
```

确认返回中包含：

- `authorization_endpoint` 指向 `/authorize`；
- `token_endpoint` 指向 `/token`；
- `userinfo_endpoint` 指向 `/userinfo`；
- `jwks_uri` 指向 `/jwks`。

### 3.2 发起授权请求（GET /authorize）

在浏览器中访问：

```text
http://localhost:8000/authorize?response_type=code&client_id=demo-client&redirect_uri=http://localhost:3000/callback&scope=openid%20profile%20email&state=xyz
```

预期行为：

- 返回一个登录页面，包含用户名、密码输入框；
- 隐藏字段中保留 `client_id`、`redirect_uri`、`scope`、`state` 等信息。

### 3.3 使用 demo 用户登录（POST /authorize）

在登录页面中输入：

- 用户名：`demo`
- 密码：`demo1234`

提交后预期：

- 浏览器收到 302 重定向到：

  ```text
  http://localhost:3000/callback?code=<authorization_code>&state=xyz
  ```

- 其中：
  - `code` 为一次性授权码；
  - `state` 原样带回 `xyz`。

在浏览器地址栏中记录下 `code` 的值，供下一步使用。

### 3.4 使用授权码换取令牌（POST /token）

在命令行中使用 `curl`（或等效工具）：

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=<上一步获得的code>" \
  -d "redirect_uri=http://localhost:3000/callback" \
  -d "client_id=demo-client" \
  -d "client_secret=secret123"
```

预期响应示例：

```json
{
  "access_token": "<access_token>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "id_token": "<id_token>",
  "scope": "openid profile email"
}
```

请记录下 `access_token`（以及需要的话 `id_token`），用于下一步调用 UserInfo。

### 3.5 使用 access_token 调用 UserInfo（GET /userinfo）

使用上一步获得的 `access_token`：

```bash
curl http://localhost:8000/userinfo \
  -H "Authorization: Bearer <access_token>"
```

预期响应示例：

```json
{
  "sub": "1",
  "name": "demo",
  "email": "demo@example.com"
}
```

注意：

- `sub` 为用户唯一标识，应与 ID Token 中的 `sub` 一致；
- `name`、`email` 对应用户资料。

---

## 4. 运行自动化测试

项目提供了 pytest 测试套件，用于验证核心行为：

```bash
python -m app.cli test
```

或直接运行：

```bash
python -m pytest -q
```

测试会覆盖：

- Discovery 端点；
- 授权码创建与使用；
- Token 颁发的正常与错误路径；
- 完整授权码流（从 `/authorize` 到 `/token` 与 `/userinfo`）。

---

## 5. 常见问题提示

- 若访问 `/authorize` 时出现 `invalid_client`：
  - 检查 `client_id` 是否为 `demo-client`；
  - 检查 `redirect_uri` 是否与注册的回调地址完全一致。
- 若调用 `/token` 时出现 `invalid_client`：
  - 检查 `client_secret` 是否为 `secret123`；
  - 确认已经正确执行 `seed_demo` 或 `init-db`。
- 若调用 `/token` 时出现 `invalid_grant`：
  - 确认授权码未被重复使用；
  - 检查 `redirect_uri` 是否与授权阶段完全一致；
  - 确认授权码未过期。
- 若调用 `/userinfo` 时返回 `invalid_token`：
  - 检查 Authorization 头格式是否为 `Bearer <access_token>`；
  - 确认 access_token 未过期且对应用户存在。

