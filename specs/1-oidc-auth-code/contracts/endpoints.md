# Contracts：OIDC 授权码流相关端点

本文件描述当前实现下，与简化授权码流特性直接相关的 HTTP 端点契约。  
目标是为客户端与测试提供清晰、稳定的接口说明。

---

## 1. Discovery：GET `/.well-known/openid-configuration`

- 请求：
  - 方法：`GET`
  - 路径：`/.well-known/openid-configuration`
  - 认证：无
- 成功响应：
  - 状态码：`200`
  - 响应体（示意）：
    ```json
    {
      "issuer": "http://localhost:8000",
      "authorization_endpoint": "http://localhost:8000/authorize",
      "token_endpoint": "http://localhost:8000/token",
      "userinfo_endpoint": "http://localhost:8000/userinfo",
      "jwks_uri": "http://localhost:8000/jwks",
      "response_types_supported": ["code"],
      "grant_types_supported": ["authorization_code"],
      "subject_types_supported": ["public"],
      "id_token_signing_alg_values_supported": ["RS256"],
      "scopes_supported": ["openid", "profile", "email"]
    }
    ```

---

## 2. Authorization：`GET /authorize`

- 请求：
  - 方法：`GET`
  - 路径：`/authorize`
  - 查询参数：
    - `response_type: str` 必填，当前仅支持 `"code"`；
    - `client_id: str` 必填，必须是已注册客户端；
    - `redirect_uri: str` 必填，必须属于该客户端的注册回调地址列表；
    - `scope: str` 可选，未提供时默认 `"openid"`，可包含 `profile`、`email`；
    - `state: str` 可选，由客户端生成，用于 CSRF 防护。
  - 认证：无
- 成功响应：
  - 状态码：`200`
  - 响应体：HTML 登录页面
    - 包含用户名、密码输入字段；
    - 以隐藏字段或等效方式保留 `client_id`、`redirect_uri`、`scope`、`state`。
- 错误响应：
  - `400 unsupported_response_type`：
    - 当 `response_type != "code"` 时；
  - `400 invalid_client`：
    - 当 `client_id` 不存在；
    - 或 `redirect_uri` 不在该客户端的注册列表中。

---

## 3. Authorization：`POST /authorize`

- 请求：
  - 方法：`POST`
  - 路径：`/authorize`
  - 表单字段：
    - `username: str` 必填；
    - `password: str` 必填；
    - `client_id: str` 必填；
    - `redirect_uri: str` 必填；
    - `scope: str` 可选；
    - `state: str` 可选。
  - 认证：表单用户名/密码。
- 成功响应：
  - 行为：创建一条 `AuthorizationCode` 记录；
  - 状态码：`302`；
  - Location：
    - 基础：`redirect_uri?code=<code>`；
    - 若存在 `state`：追加 `&state=<state>`。
- 错误响应：
  - `400 access_denied`：
    - 当用户名不存在或密码不正确时；
    - 不创建授权码记录。

---

## 4. Token：POST `/token`

- 请求：
  - 方法：`POST`
  - 路径：`/token`
  - Content-Type：`application/x-www-form-urlencoded`
  - 表单字段：
    - `grant_type: str` 必填，期望值 `"authorization_code"`；
    - `code: str` 必填，由 `/authorize` 返回；
    - `redirect_uri: str` 必填，必须与授权阶段一致；
    - `client_id: str` 必填；
    - `client_secret: str` 必填。
- 成功响应：
  - 状态码：`200`
  - 响应体（示意）：
    ```json
    {
      "access_token": "<access_token>",
      "token_type": "Bearer",
      "expires_in": 3600,
      "id_token": "<id_token>",
      "scope": "openid profile email"
    }
    ```
- 错误响应：
  - `400 invalid_client`：
    - 当 `client_id` 不存在或 `client_secret` 不正确时；
  - `400 unsupported_grant_type`：
    - 当 `grant_type` 不为 `"authorization_code"` 时；
  - `400 invalid_grant`：
    - 当授权码不存在；
    - 或已被使用；
    - 或已过期；
    - 或与请求中的 `client_id` / `redirect_uri` 不匹配。

---

## 5. UserInfo：GET `/userinfo`

- 请求：
  - 方法：`GET`
  - 路径：`/userinfo`
  - 认证：
    - `Authorization: Bearer <access_token>`
- 成功响应：
  - 状态码：`200`
  - 响应体（示意）：
    ```json
    {
      "sub": "1",
      "name": "Demo User",
      "email": "demo@example.com"
    }
    ```
- 错误响应：
  - `401 invalid_token`：
    - Authorization 头缺失；
    - 或 access_token 无法解码；
    - 或 token 中的用户不存在。

---

## 6. JWKS：GET `/jwks`

- 请求：
  - 方法：`GET`
  - 路径：`/jwks`
  - 认证：无
- 成功响应：
  - 状态码：`200`
  - 响应体（示意）：
    ```json
    {
      "keys": [
        {
          "kty": "RSA",
          "use": "sig",
          "alg": "RS256",
          "kid": "key-id",
          "n": "<modulus>",
          "e": "AQAB"
        }
      ]
    }
    ```
- 约束：
  - `keys` 至少包含一个可用于验证当前发行 token 的 key；
  - 与实际 `id_token` / `access_token` 的签名算法和 kid 对齐。

