# Data Model：简化 OIDC Provider 授权码流

本数据模型文档描述当前实现下，与简化授权码流特性直接相关的核心持久化实体与派生概念。  
目标是作为实现与测试的“单一真相”，而不是强行引入理想化设计。

---

## 1. User（用户）

- 物理表：`users`
- 用途：
  - 表示系统中的最终用户；
  - 作为授权码与令牌中的 `sub` 来源。
- 字段：
  - `id: int` 主键，自增，内部唯一标识；
  - `username: str` 用户名，要求全局唯一，用于登录；
  - `email: str` 邮箱地址，要求全局唯一，用于展示与通知；
  - `hashed_password: str` 经过安全哈希的密码摘要；
  - `is_active: bool` 是否为激活状态用户；
  - `created_at: datetime` 创建时间，默认当前 UTC 时间。
- 约束与关系：
  - `username`、`email` 均设置唯一索引；
  - 与 `AuthorizationCode.user_id` 建立一对多关系（一个用户可拥有多个授权码）。

---

## 2. Client（客户端）

- 物理表：`clients`
- 用途：
  - 表示接入本 Provider 的 RP 应用；
  - 在授权码流中作为 `client_id` 与 `aud` 的来源。
- 字段：
  - `id: int` 主键，自增；
  - `client_id: str` 面向外部的客户端标识，要求全局唯一；
  - `client_secret: str` 客户端密钥（存储为明文或哈希，由当前实现决定）；
  - `redirect_uris: str` 逗号分隔的回调地址列表；
  - `scopes: str` 逗号分隔的允许 scopes 列表，例如 `openid,profile,email`；
  - `grant_types: str` 逗号分隔的允许 grant_types 列表（当前实现通常包含 `authorization_code`）；
  - `response_types: str` 逗号分隔的允许 response_types 列表（当前实现通常包含 `code`）；
  - `created_at: datetime` 创建时间。
- 约束与关系：
  - `client_id` 设置唯一索引；
  - 通过 `client_id` 与 `AuthorizationCode.client_id` 关联（逻辑关联，而非外键）；
  - 用于：
    - 校验授权端点中的 `client_id`/`redirect_uri`；
    - 校验 token 端点中的 `client_id`/`client_secret`；
    - 为 ID Token / access_token 的 `aud` 提供值。

---

## 3. AuthorizationCode（授权码）

- 物理表：`authorization_codes`
- 用途：
  - 表示一次成功授权后的短期票据；
  - 是授权码流中 `/authorize` 与 `/token` 之间的“桥梁”。
- 字段：
  - `id: int` 主键，自增；
  - `code: str` 授权码值，唯一，用于在 `/token` 请求中作为凭据；
  - `client_id: str` 授权时的客户端标识；
  - `user_id: int` 授权时的用户标识，外键指向 `users.id`；
  - `redirect_uri: str` 授权时记录的回调地址；
  - `scope: str` 授予的 scope 集合，当前以原始字符串形式存储，例如 `"openid profile email"`；
  - `expires_at: datetime` 授权码过期时间。
- 约束与关系：
  - `code` 设置唯一索引；
  - `user_id` 为外键，ORM 层维护 `AuthorizationCode.user` 关系；
  - 一次性使用：
    - `/token` 调用成功后会删除对应记录；
    - 过期时间由创建时设置，当前实现默认 5 分钟左右。
- 与规格的对应关系：
  - 对应 `spec.md` 中的 `AuthorizationCode` 领域概念；
  - 满足 FR-11 对字段的要求；
  - 支持 FR-13 关于“单次使用及失效”的约束。

---

## 4. TokenSet（令牌集，逻辑概念）

- 物理存储：
  - 当前实现不在数据库中存储 token，仅在 `/token` 调用时计算并返回；
  - access_token 与 id_token 以 JWT 字符串形式存在，由调用方持有。
- 组成：
  - `access_token: str` 访问令牌；
  - `id_token: str` ID Token；
  - `token_type: str` 当前固定为 `"Bearer"`；
  - `expires_in: int` 有效期（秒），当前实现为 3600。
- 约束与关系：
  - `access_token` 与 `id_token` 的 `sub` 字段都来自 `User.id`；
  - `aud` 字段来自 `Client.client_id`；
  - `scope` 字段与对应授权码中的 scope 一致。
- 与规格的对应关系：
  - 对应 `spec.md` 中的 `TokenSet` 概念；
  - 与 FR-18、FR-19 和 NFR-2 一致。

---

## 5. 关系示意（简化）

- 一个 `User` 可以与多个 `AuthorizationCode` 关联；
- 一个 `Client` 可以与多个 `AuthorizationCode` 关联（通过 `client_id`）；
- 每条 `AuthorizationCode` 通过 `/token` 调用生成一次 `TokenSet`，之后自身失效（删除）。

---

## 6. 与后续领域建模的关系

本数据模型文档描述的是当前实现下的持久化结构与核心逻辑概念，它：

- 为后续在领域层引入更丰富的实体/值对象提供参考（例如单独的 `RedirectUri`、`ScopeSet` 类型）；
- 与 `spec.md` 中的领域概念（Client、EndUser、AuthorizationCode、TokenSet）保持一一对应；
- 不强制要求在当前迭代中修改数据库结构，而是作为理解与测试的对齐基础。

