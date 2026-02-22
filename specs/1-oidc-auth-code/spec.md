# 简化 OIDC Provider 授权码流

## 1. 概要（Feature Summary）

本特性旨在提供一个简化版的 OpenID Connect Provider，支持标准的授权码流程（Authorization Code Flow），使内部或实验环境中的客户端应用（RP）可以：

- 将用户浏览器重定向到本 Provider 完成登录；
- 通过授权码从 Provider 换取访问令牌（access_token）与 ID Token；
- 使用访问令牌访问 UserInfo 端点获取用户信息。

该能力是后续扩展（如 PKCE、Refresh Token、多租户等）的基础。

---

## 2. 业务问题与动机（Problem & Motivation）

当前需求背景：

- 需要一个可运行的 OIDC Provider：
  - 为内部应用提供统一登录能力；
  - 作为学习和验证 OIDC 授权码流程的实验环境。
- 现有 `Design.md` 提供了理想化的分层与领域建模示例，但与现有代码实现不完全一致，容易导致实现和约束脱节。
- 缺少一份基于当前实现现状和未来 B 计划目标的「单一真相」需求规格，来指导后续技术方案和实现演进。

引入本特性的动机：

- 用一个功能范围清晰、行为可预期的授权码流作为系统的稳定基础；
- 将对外协议（端点、参数、响应、错误码）明确下来，便于客户端集成；
- 在保证用户价值的前提下，引入分层架构和可测试性约束，为后续迭代留足空间。

---

## 3. 目标（Goals）

1. 提供一个单 Issuer 的 OIDC Provider，支持授权码流程完成用户登录与用户信息获取。
2. 提供一组稳定的 OIDC 相关端点：
   - Discovery：`/.well-known/openid-configuration`
   - Authorization：`GET /authorize` 与 `POST /authorize`
   - Token：`POST /token`
   - UserInfo：`GET /userinfo`
   - JWKS：`GET /jwks`
3. 至少支持一个演示客户端与一个演示用户，可以通过完整授权码流程完成登录。
4. 在内部，使用清晰的分层和用例服务：
   - 接口层负责协议适配与响应拼装；
   - 应用层负责授权码发放、token 签发等用例编排；
   - 领域层（如存在）聚焦业务规则；
   - 基础设施层封装存储与加密细节。
5. 为核心用例提供稳定的自动化测试（单元、集成和端到端），使后续重构在受控范围内进行。

---

## 4. 非目标（Non-Goals）

本特性阶段明确**不包含**以下能力：

- PKCE 支持；
- Refresh Token 流程；
- 动态客户端注册与客户端自助管理；
- 多 Issuer、多租户支持；
- 完整对齐 OIDC 规范的错误重定向（如在错误时统一重定向回 redirect_uri 携带 error 参数）；
- 与外部身份源（其他 IdP）的联合登录；
- 针对高并发、大规模集群部署的性能和可用性优化。

这些将视后续需求，拆分为独立特性迭代。

---

## 5. 角色与用户（Actors & Users）

- **End-User（最终用户）**
  - 希望通过某个客户端应用登录，并允许该应用获取自己的基础资料（如名称、邮箱）。

- **Client / RP（依赖方应用）**
  - 使用本 OIDC Provider 作为认证源；
  - 通过标准授权码流程为用户建立登录会话。

- **OP 管理者 / 开发者**
  - 需要方便地初始化演示用户和演示客户端；
  - 需要清晰的协议和行为，以便在本地和 CI 环境中编写测试和排查问题。

---

## 6. 用户场景与验收（User Scenarios & Acceptance）

### 场景 S1：授权码登录 + UserInfo 获取（成功路径）

**描述**

用户在客户端应用中选择使用 OIDC 登录，最终成功登录并在客户端看到自己的基础信息。

**步骤**

1. 用户在 RP 页面点击「使用 OIDC 登录」。
2. RP 将浏览器重定向到 OP 的授权端点：
   - 路径：`/authorize`
   - 携带参数：
     - `client_id`：预先注册的客户端标识；
     - `redirect_uri`：在 OP 备案的回调地址；
     - `response_type=code`；
     - `scope`：至少包含 `openid`，可以附加 `profile`、`email`；
     - `state`：RP 生成，用于防止 CSRF。
3. OP 验证 `client_id` 合法且处于启用状态，并验证 `redirect_uri` 属于该客户端的注册列表。
4. 校验通过后，OP 返回登录页面，其中包含用户名/密码表单以及隐藏字段保存上述参数。
5. 用户输入正确的用户名和密码并提交。
6. OP 校验凭据：
   - 如果凭据错误，返回错误响应（不颁发授权码）；
   - 如果凭据正确，创建授权码，并通过 302 跳转浏览器回到：
     - `redirect_uri?code=<authorization_code>&state=<原 state>`。
7. RP 接收回调请求，从查询参数中提取 `code` 和 `state`，校验 `state` 的匹配性。
8. RP 在后端调用 OP 的 Token 端点 `/token`，提交：
   - `grant_type=authorization_code`；
   - `code`（第 6 步中获得）；
   - `redirect_uri`（必须与授权时一致）；
   - `client_id`；
   - `client_secret`（RP 与 OP 共享的密钥）。
9. OP 校验客户端密钥、授权码有效性、redirect_uri 匹配及授权码未过期。
10. 校验通过后，OP 返回包含 access_token 和 id_token 的 JSON 响应，并在内部标记该授权码为已使用。
11. RP 使用 access_token 调用 `/userinfo` 获取用户的 `sub`、`name`、`email` 等信息，并建立自己的登录会话。
12. 用户在 RP 前端看到自己的登录状态与基础信息。

**验收要点**

- Discovery 文档中公布的 endpoints 与上述调用路径一致；
- `state` 值在回调中被原样带回；
- 同一授权码只能使用一次；
- UserInfo 中的 `sub` 与 ID Token 中的 `sub` 一致。

---

### 场景 S2：错误的客户端密钥导致 Token 获取失败

**描述**

客户端在换取 token 时使用了错误的客户端密钥，OP 必须拒绝请求。

**步骤**

1. RP 通过 S1 流程成功获得一个授权码 `code`。
2. RP 在调用 `/token` 时，使用了错误的 `client_secret`。
3. OP 校验客户端密钥失败。
4. OP 返回包含 `invalid_client` 错误码的错误响应，HTTP 状态码为 400。
5. RP 不建立用户登录态，可以提示用户重试或联系管理员。

**验收要点**

- 不返回 access_token 或 id_token；
- 错误信息足够明确（例如 detail/错误码），但不泄露额外安全信息（如确认 client 是否存在）。

---

### 场景 S3：无效或过期授权码被使用

**描述**

客户端使用了无效、已经使用过或已过期的授权码，OP 必须拒绝请求。

**步骤**

1. RP 尝试使用一个无效授权码调用 `/token`，可能情况包括：
   - 授权码从未存在；
   - 授权码已被使用；
   - 授权码已过期；
   - 授权码属于其他客户端；
   - 授权码绑定的 redirect_uri 与当前请求的 redirect_uri 不一致。
2. OP 校验授权码失败。
3. OP 返回包含 `invalid_grant` 错误码的错误响应，HTTP 状态码为 400。
4. RP 记录失败并可重新发起授权流程。

**验收要点**

- 上述所有情况均被统一视为 `invalid_grant`；
- 授权码在成功兑换后，不能再次被兑换。

---

## 7. 功能需求（Functional Requirements）

### 7.1 Discovery：`GET /.well-known/openid-configuration`

- **FR-1**：系统必须提供 `GET /.well-known/openid-configuration` 端点，正常情况下返回 200。
- **FR-2**：响应体必须包含以下字段：
  - `issuer`
  - `authorization_endpoint`
  - `token_endpoint`
  - `userinfo_endpoint`
  - `jwks_uri`
- **FR-3**：响应体必须声明支持的 scopes，其中至少包含 `openid`，并应包含 `profile` 与 `email`。
- **FR-4**：响应体必须声明支持的 `response_types`，其中至少包含 `"code"`。
- **FR-5**：响应体必须声明支持的 `grant_types`，其中至少包含 `"authorization_code"`。

### 7.2 授权端点：`GET /authorize`

- **FR-6**：`GET /authorize` 必须接受以下查询参数：
  - `response_type`（必填，期望值 `"code"`）；
  - `client_id`（必填）；
  - `redirect_uri`（必填）；
  - `scope`（可选，未提供时默认 `"openid"`）；
  - `state`（可选）。
- **FR-7**：当 `client_id` 不存在或 `redirect_uri` 不属于该客户端已注册的 URIs 时，系统必须拒绝请求，返回带有 `invalid_client` 的错误响应（HTTP 400）。
- **FR-8**：当上述参数合法时，系统必须返回一个 HTML 登录页面：
  - 页面中包含用户名和密码输入字段；
  - 页面中以隐藏字段或等效方式保留 `client_id`、`redirect_uri`、`scope`、`state` 信息，以便 POST 提交时使用。

### 7.3 授权端点：`POST /authorize`

- **FR-9**：`POST /authorize` 必须处理以下表单字段：
  - `username`、`password`；
  - `client_id`、`redirect_uri`、`scope`、`state`。
- **FR-10**：当用户名不存在或密码不正确时，系统必须拒绝登录并返回带有 `access_denied` 的错误响应（HTTP 400），不创建授权码。
- **FR-11**：当用户凭据有效且 client/redirect_uri 合法时，系统必须创建一条授权码记录，至少包含：
  - 唯一授权码值 `code`；
  - 对应 `client_id`；
  - 对应 `user_id`；
  - `redirect_uri`；
  - 授予的 `scope`；
  - 过期时间 `expires_at`，距离当前时间不超过配置的有效期（例如 5 分钟）。
- **FR-12**：成功创建授权码后，系统必须通过 302 重定向浏览器到：
  - `redirect_uri?code=<code>`；
  - 若存在 `state` 参数，必须追加 `&state=<state>`。
- **FR-13**：每个授权码在被 `/token` 成功兑换一次后，必须立即失效并不可重复使用。

### 7.4 Token 端点：`POST /token`

- **FR-14**：`POST /token` 必须接受以下表单字段：
  - `grant_type`；
  - `code`；
  - `redirect_uri`；
  - `client_id`；
  - `client_secret`。
- **FR-15**：当 `client_id` 不存在或 `client_secret` 不正确时，系统必须返回带有 `invalid_client` 的错误响应（HTTP 400）。
- **FR-16**：当 `grant_type` 不为 `"authorization_code"` 时，系统必须返回带有 `unsupported_grant_type` 的错误响应（HTTP 400）。
- **FR-17**：当授权码无效、已被使用、已过期或者与请求中的 `client_id` / `redirect_uri` 不匹配时，系统必须返回带有 `invalid_grant` 的错误响应（HTTP 400）。
- **FR-18**：当请求合法且授权码有效时，系统必须：
  - 基于授权码关联的用户和客户端生成访问令牌（access_token），该令牌应能标识用户和客户端，并带有有效期信息；
  - 基于用户和客户端生成 ID Token，包含用户标识（sub）以及与 scope 相应的声明；
  - 使该授权码以后不可再用（例如删除记录或标记为已使用）。
- **FR-19**：成功响应体必须包含：
  - `access_token`：非空；
  - `token_type`：值为 `"Bearer"`；
  - `expires_in`：访问令牌的有效期（秒）；
  - `id_token`：非空；
  - `scope`：与授权阶段授予的 scope 相同。

### 7.5 UserInfo 端点：`GET /userinfo`

- **FR-20**：`GET /userinfo` 必须从请求中提取访问令牌（例如基于 Authorization 头）。
- **FR-21**：当访问令牌缺失、无效或已过期时，系统必须拒绝请求并返回错误响应（例如 HTTP 401 或 400）。
- **FR-22**：当访问令牌合法时，响应体必须至少包含：
  - `sub`：用户唯一标识；
  - `name`：用户的展示名称；
  - `email`：用户邮箱字段，可以为空。
- **FR-23**：UserInfo 响应中的 `sub` 必须与 ID Token 中的 `sub` 一致，并在系统内唯一标识一个用户。

### 7.6 JWKS 端点：`GET /jwks`

- **FR-24**：`GET /jwks` 必须返回 200 响应，主体为一个 JWKS 对象：
  - 顶层字段 `keys` 为数组；
  - 至少包含一个可用于验证当前发行令牌的 key。
- **FR-25**：`keys` 中的每个 key 必须包含必要的元数据（例如密钥类型、用途、算法标识、密钥 ID 等），以便外部系统能够根据 JWKS 成功验证 ID Token 和 access_token 的签名。

### 7.7 演示数据初始化

- **FR-26**：系统必须提供一种方式，在开发和测试环境中初始化至少一个演示用户和一个演示客户端，例如：
  - 用户：`username="demo"`，具有可预期的密码；
  - 客户端：`client_id="demo-client"`，配置一个本地可访问的 `redirect_uri`。
- **FR-27**：演示用户和客户端必须可重复初始化（例如通过脚本或命令），以支持测试环境重置。

---

## 8. 非功能需求（Non-Functional Requirements）

### 8.1 安全性

- **NFR-1**：用户密码和客户端密钥不得以明文存储，必须使用安全的单向散列和安全比较方式。
- **NFR-2**：访问令牌和 ID Token 必须经过签名，外部系统应能通过公开信息验证其完整性与来源。
- **NFR-3**：授权码必须具有时间限制和一次性使用特性，以降低重放攻击风险。

### 8.2 可测试性

- **NFR-4**：必须提供自动化测试，覆盖：
  - Discovery、Authorize、Token、UserInfo、JWKS 端点的集成测试；
  - 授权码创建、token 签发等核心用例服务的单元测试；
  - 至少一条完整授权码流的端到端测试。
- **NFR-5**：测试应当可以在本地和 CI 环境中自动执行，不依赖外部第三方服务。

### 8.3 架构约束

- **NFR-6**：实现应遵循分层与低耦合原则：
  - 接口层：处理 HTTP 协议和输入输出；
  - 应用层：编排用例逻辑（授权码生成、token 签发等）；
  - 领域层（如存在）：专注业务规则与领域概念；
  - 基础设施层：封装存储、加密和其他技术细节。
- **NFR-7**：新增业务逻辑必须以可单元测试的方式组织，避免将复杂规则直接散布在接口层。

---

## 9. 关键领域概念（Key Domain Concepts）

> 本小节描述业务概念和领域语言，不限制具体实现细节。

- **Client（客户端）**
  - 代表一个接入本 Provider 的应用；
  - 具有唯一标识、注册的 redirect_uris、允许的 scopes 和启用状态。

- **EndUser（最终用户）**
  - 代表系统中的一个用户；
  - 具有唯一标识（用于 sub）、用户名、邮箱和激活状态。

- **AuthorizationCode（授权码）**
  - 代表一次成功授权结果的短期票据；
  - 绑定 client、user、redirect_uri、scope 与过期时间；
  - 一次性使用。

- **TokenSet（令牌集）**
  - 代表一次 `/token` 调用成功时发放的一组令牌；
  - 包含 access_token、id_token、token_type 和 expires_in。

---

## 10. 假设与依赖（Assumptions & Dependencies）

- **A-1**：客户端与本 Provider 通过安全传输通道通信（如 HTTPS），但证书和反向代理细节不在本规格范围。
- **A-2**：本特性优先面向开发/测试和内部场景，尚未针对大规模高并发进行优化。
- **A-3**：客户端和用户数量在可管理范围内，管理操作可以通过脚本或简单界面完成。

---

## 11. 成功标准（Success Criteria）

- **SC-1：完整授权码流程可用**  
  有自动化测试覆盖从 `/authorize` 到 `/token` 和 `/userinfo` 的完整授权码流，并稳定通过。

- **SC-2：关键错误场景有清晰反馈**  
  对错误 client_secret、无效/过期授权码、不支持的 grant_type 等情况，系统通过自动化测试验证返回正确的错误码和 HTTP 状态。

- **SC-3：对外契约清晰一致**  
  Discovery 文档中的端点地址和能力描述与实际行为一致，外部系统可使用 JWKS 验证 ID Token 签名。

- **SC-4：可维护与可扩展**  
  在不破坏现有自动化测试的前提下，可以平滑引入新的业务规则或协议能力（如 PKCE），分层架构和测试策略仍然适用。

