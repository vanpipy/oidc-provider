# 实现计划：简化 OIDC Provider 授权码流

- Feature Spec: `specs/1-oidc-auth-code/spec.md`
- Checklist: `specs/1-oidc-auth-code/checklists/requirements.md`
- 代码仓库根目录: `d:/Project/oidc-provider`

---

## 1. 技术上下文（Technical Context）

### 1.1 技术栈概览

- 语言与运行时
  - Python 3.10+
- Web 框架
  - FastAPI（同步视图风格，依赖注入用于获取 DB Session）
  - Uvicorn 作为开发/运行服务器（通过 `project.scripts` 中的 `dev` / `serve` 命令）
- HTTP 模式与接口层
  - RESTful HTTP 端点
  - 路由组织在 `app/api/v1/endpoints/*`
  - OIDC 相关端点当前主要分布在：
    - Discovery: `app/api/v1/endpoints/oidc/discovery.py`
    - Authorization, Token, UserInfo: `app/api/v1/endpoints/oidc/authorization.py`, `token.py`, `userinfo.py`（已经存在并被测试引用）
- 配置管理
  - `pydantic-settings` + `.env` / `.env.<env>`
    - 配置定义：`app/config.py`
    - 核心字段：`DATABASE_URL`, `OIDC_ISSUER_URL`, `ACCESS_TOKEN_EXPIRE_SECONDS`, `ID_TOKEN_EXPIRE_SECONDS` 等
- 数据访问与持久化
  - SQLAlchemy 2.x，同步 Session 模式
  - SQLite 默认数据库（`DATABASE_URL: "sqlite:///./app.db"`）
  - Session/Engine 定义：`app/infrastructure/database/session.py`
  - 领域相关模型：`app/infrastructure/database/models.py` 中有 `User`, `Client`, `AuthorizationCode` 等
- 模板与静态资源
  - Jinja2 模板引擎，用于渲染登录页面等
  - 静态资源、模板目录已在 `app/main.py` 中正确挂载
- 加密与 JWT/OIDC
  - `python-jose[cryptography]` 用于 JWT 签名与验证
  - 密码哈希：`passlib[bcrypt]` + `bcrypt<4.0.0`
  - OIDC 相关 JWT/JWKS 封装：`app/infrastructure/auth/jwt.py`（例如 `jwks` 函数）
- 测试
  - 测试运行入口：`pyproject.toml` 中 `test = "app.cli:test"`
  - 框架：pytest
  - HTTP 客户端：FastAPI TestClient / httpx
  - 已有关键测试：
    - Discovery：`tests/test_discovery.py`
    - 完整授权码流 E2E：`tests/test_oidc_flow.py`
    - 应用服务与 claims：`tests/test_client_service.py`, `tests/test_authorization_service.py`, `tests/test_token_service.py`, `tests/test_claims.py`
- CLI 与初始化脚本
  - CLI 入口：`app/cli.py`
  - 提供命令：
    - `init-db`, `reset-db`, `drop-db`
    - `create-user`, `create-client`
    - `print-jwks`, `print-settings`
    - `test`（执行测试）

### 1.2 当前 OIDC 授权码流实现现状

- Discovery
  - 已有端点 `GET /.well-known/openid-configuration`
    - 返回 issuer、authorization_endpoint、token_endpoint、userinfo_endpoint、jwks_uri 以及支持的 scopes/response_types/grant_types
- Authorization / Token / UserInfo
  - 授权端点 `/authorize`、令牌端点 `/token`、用户信息端点 `/userinfo` 已存在，并可通过 `tests/test_oidc_flow.py` 验证完整授权码流
  - 部分逻辑已经抽取为应用服务：
    - AuthorizationService：`app/application/services/authorization_service.py`
    - TokenService：`app/application/services/token_service.py`
    - ClientService / UserService：`app/application/services/client_service.py`, `user_service.py`
    - Claims 相关逻辑：`app/application/services/claims.py`（或同名模块）
- JWKS
  - JWKS 生成逻辑存在于 `app/infrastructure/auth/jwt.py` 中（`jwks()` 或类似函数）
  - JWKS 端点（`/jwks`）已通过 Discovery 文档暴露，并在 CLI 中也有打印功能（`print-jwks`）
- 测试覆盖
  - E2E 测试完整走通 S1 场景（授权码登录 + token 交换 + userinfo）；
  - 单元/应用层测试覆盖授权码生成、token 签发、claims 构造等关键逻辑；
  - Discovery 有独立测试校验响应字段。

### 1.3 约束与假设（实现侧）

- 同步风格 FastAPI（当前不切换到 async + async SQLAlchemy）
- 单一 Issuer，单数据库实例（SQLite），不考虑多租户、多 region 部署
- 使用现有依赖，不引入新的大型框架或身份组件（如 Keycloak 等）
- 继续沿用现有 CLI 及测试命令，集成在现有 Dev Flow 中

### 1.4 未决问题（NEEDS CLARIFICATION）

当前需求规格经过自检，不存在阻碍实现的关键需求级未知。  
在实现计划层面，仅有一些可选决策点，可在实现中按合理默认处理，无需阻塞。  
因此，本计划不标记 `[NEEDS CLARIFICATION]` 条目。

---

## 2. 宪章检查（Constitution Check）

宪章主要来自 `Design.md` 以及团队对「低耦合 / 高内聚 / 可测试性」的共识。

### 2.1 关键宪章条目映射

- 分层架构
  - 接口层（FastAPI 端点）只负责协议适配与 DTO 映射，不直接处理复杂业务规则和持久化细节。
  - 应用层（用例服务）聚焦授权码生成、token 签发、claims 构造等用例逻辑。
  - 领域层（如逐步补全）专注领域模型与规约。
  - 基础设施层封装 ORM 模型、存储、JWT 加密等。
- 依赖方向
  - 接口层 → 应用层 → 领域层 → 基础设施层，禁止反向依赖。
- 可测试性
  - 领域/应用层逻辑可通过单元测试在隔离环境下验证；
  - 基础设施层可通过集成测试验证；
  - 全局通过端到端测试验证完整 OIDC 授权码流。
- 安全
  - 不泄露敏感信息（密码、client_secret）；
  - 密码与 client_secret 使用哈希存储与安全比较；
  - 授权码一次性使用 + 短期有效。

### 2.2 现状评估

- 接口层已有部分逻辑仍稍偏「粗颗粒业务」，但总体已开始通过 AuthorizationService/TokenService 下沉；
- 应用服务使用了 Session 注入的模式，对 DB 依赖集中处理，是合理方向；
- 测试结构已开始体现“单元 / 集成 / E2E”分层；
- JWT 与 JWKS 已通过基础设施模块抽象。

### 2.3 宪章 Gate 评估（是否允许进入设计/实施）

- 分层约束：允许（当前实现虽不完美，但不违反方向性约束，后续可逐步收束）
- 可测试性：允许（已有较好的起点，本计划会进一步补齐 FR/NFR 所需测试）
- 安全集：允许（基于现有密码学方案，不引入高风险变更）

结论：当前计划在宪章约束下可以继续推进。

---

## 3. Phase 0：研究与决策（Outline & Research）

### 3.1 决策：同步 FastAPI + 同步 SQLAlchemy

- 决策
  - 保持现有同步 FastAPI 路由 + 同步 SQLAlchemy Session。
- 理由
  - 现有代码、测试和 CLI 均围绕该模式构建；
  - 授权码流本身不是高并发瓶颈，本阶段无需为 async 重构付出成本；
  - 同步风格更便于调试和教学。
- 替代方案
  - 全面改为 async 路由 + async SQLAlchemy，引入更复杂的 Session 管理与测试模式；
  - 考虑到当前需求与时间价值，本阶段不采用。

### 3.2 决策：使用 python-jose + 内部密钥管理实现 JWT/ID Token

- 决策
  - 继续使用 `python-jose[cryptography]` 和现有 `app/infrastructure/auth/jwt.py` 实现 access_token 和 id_token。
- 理由
  - 依赖已在项目中使用，JWKS/签名逻辑已存在；
  - 满足当前 spec 对 ID Token 签名与 JWKS 的要求。
- 替代方案
  - 引入 authlib 的完整 OIDC Provider 能力；
  - 改用其他 JWT 库（如 PyJWT），会增加迁移成本且对业务价值有限。

### 3.3 决策：保持 SQLite + SQLAlchemy 模式

- 决策
  - 开发与测试环境继续使用 SQLite（文件级），通过 SQLAlchemy 抽象。
- 理由
  - 对当前特性（授权码流）而言，SQLite 已足够；
  - 通过 SQLAlchemy，未来迁移 RDBMS 成本可控。
- 替代方案
  - 直接切换至 Postgres/MySQL 等，增加本阶段运维复杂度，收益有限。

---

## 4. Phase 1：设计与契约（Design & Contracts）

目标：在不改动需求规格的前提下，把「数据模型」「外部契约」和「开发者指南」层面的设计固化下来。

### 4.1 数据模型设计（Data Model）

最终计划落地为 `specs/1-oidc-auth-code/data-model.md`，主要内容包括：

- 实体列表与字段
  - Client
    - 对应 ORM：`Client` 模型
    - 字段：`client_id`, `client_secret_hash`, `redirect_uris`, `scopes`, `grant_types`, `response_types`, `is_active` 等。
  - EndUser
    - 对应 ORM：`User` 模型
    - 字段：`id`, `username`, `password_hash`, `email`, `is_active` 等。
  - AuthorizationCode
    - 对应 ORM：`AuthorizationCode` 模型
    - 字段：`code`, `client_id`, `user_id`, `redirect_uri`, `scope`, `expires_at`，以及「已使用」标记（如存在）。
  - TokenSet（值对象）
    - 非持久化表；
    - 用于在应用/领域层表示一次 `/token` 成功颁发的结果：`access_token`, `id_token`, `token_type`, `expires_in`。
- 约束与规则
  - 授权码一次性使用与过期规则；
  - client 与 `redirect_uri` 必须匹配；
  - `scope` 允许范围（`openid`/`profile`/`email`）与默认行为（未提供时默认为 `openid`）。
- 关系与导航
  - AuthorizationCode → Client / EndUser 的关联；
  - 访问令牌与 UserInfo/ID Token 中 `sub` 的一致性。

### 4.2 外部契约设计（Contracts）

最终计划落地为 `specs/1-oidc-auth-code/contracts/` 下的文档，围绕 HTTP API：

- Authorization Endpoint
  - `GET /authorize`
    - Query 参数：`response_type`, `client_id`, `redirect_uri`, `scope`, `state`。
    - 正常响应：登录表单 HTML。
    - 错误响应：HTTP 400 + 错误信息（如 `invalid_client`）。
  - `POST /authorize`
    - Form 参数：`username`, `password`, `client_id`, `redirect_uri`, `scope`, `state`。
    - 成功：302 重定向至 `redirect_uri`，携带 `code`, `state`。
    - 错误：HTTP 400 + 错误信息（如 `access_denied`）。
- Token Endpoint：`POST /token`
  - Form 参数：`grant_type`, `code`, `redirect_uri`, `client_id`, `client_secret`。
  - 成功响应：与 `TokenResponse` 一致的 JSON 结构。
  - 错误响应：HTTP 400 + OIDC 错误码（`invalid_client` / `invalid_grant` / `unsupported_grant_type`）。
- UserInfo Endpoint：`GET /userinfo`
  - 认证：`Authorization: Bearer <access_token>`。
  - 成功响应：与 `UserInfoResponse` 一致的 JSON 结构。
  - 错误响应：401/400 + 错误信息。
- Discovery & JWKS
  - Discovery：响应字段与 spec 中 FR-1 ~ FR-5 对齐。
  - JWKS：`{"keys": [...]}` 结构，与当前 `jwks()` 输出对齐。

### 4.3 Quickstart / 开发者指南

最终计划落地为 `specs/1-oidc-auth-code/quickstart.md`，覆盖：

- 环境准备
  - 安装依赖：`pip install -e .[dev]`。
  - 初始化数据库：如通过 `init-db` 命令。
  - 创建 demo 用户与 client：通过 CLI 调用。
- 启动服务
  - 使用 CLI 命令 `dev` 或 `serve` 启动开发/生产服务器。
- 手工验证授权码流
  - 发起 `/authorize` 请求；
  - 使用 demo 用户登录；
  - 调用 `/token` 换取 access_token 和 id_token；
  - 调用 `/userinfo` 获取用户信息。

---

## 5. Phase 2：实现与重构计划（Implementation Plan）

### 5.1 接口层对齐与瘦身

目标：确保 `app/api/v1/endpoints/oidc/*` 端点只负责协议/DTO，不承载复杂业务逻辑。

- 步骤
  1. 审查 `authorization.py`, `token.py`, `userinfo.py`：
     - 检查是否仍有直接对 ORM（`SessionLocal`, `User`, `Client`, `AuthorizationCode` 等）的访问；
     - 检查是否存在重复的 client/redirect_uri 校验逻辑。
  2. 将剩余业务逻辑统一下沉到应用服务层：
     - AuthorizationService：处理 S1/S3 中的授权码生成与错误场景；
     - TokenService：集中处理 S1/S2/S3 中所有 token 颁发规则和错误码映射；
     - UserInfoService（如尚未存在）：封装访问令牌校验和用户信息返回。
  3. 端点层只负责：
     - 参数绑定；
     - 调用对应服务；
     - 将业务异常映射为 HTTP 状态码和错误码。
  4. 为每个端点编写或补充集成测试（pytest + TestClient）：
     - 正常路径测试；
     - 错误路径测试（`invalid_client` / `invalid_grant` / `unsupported_grant_type` / 未授权）。

### 5.2 应用层服务收敛与增强

目标：让应用层完整承载 spec 中的 FR/NFR，用例清晰、可单元测试。

- AuthorizationService
  - 行为：
    - 校验 client/redirect_uri/scope；
    - 校验用户凭据（委托 UserService 等）；
    - 创建 AuthorizationCode 记录（一次性、短期有效）。
  - 单元测试覆盖：
    - 正常授权码发放；
    - 无效 client/redirect_uri；
    - 错误凭据；
    - 授权码持久化后的字段与 spec 的一致性。

- TokenService
  - 行为：
    - 校验 `client_id` + `client_secret`；
    - 校验 `grant_type`；
    - 校验 `code` + `redirect_uri` + 过期/已使用状态；
    - 颁发 access_token 与 id_token；
    - 使授权码失效（删除或标记）。
  - 单元测试覆盖：
    - S1/S2/S3 的所有分支；
    - 授权码一次性使用；
    - scope 传递与返回一致。

- UserInfo 服务
  - 提供独立函数/服务：
    - 从 access_token 中解析用户标识（sub）；
    - 加载用户信息；
    - 生成 UserInfoResponse。
  - 单元测试覆盖：
    - 有效 token → 正确用户信息；
    - 无效/过期 token → 错误。

### 5.3 领域概念与规约（可渐进实现）

目标：在不大动现有代码的前提下，为后续领域建模预留位置。

- 实施要点
  - 在合适位置创建基础实体/值对象（如不与当前 ORM 冲突）；
  - 将「合法授权请求」「合法 token 请求」等规则封装为规约（Specification）或领域服务；
  - 初期可以只在应用服务内部使用这些对象，逐步从 ORM 模型中解耦业务规则。

### 5.4 JWT / JWKS 实现对齐

目标：确保 spec 中对 JWKS 和 token 的要求与现有实现完全一致，并可被外部系统验证。

- 检查点
  - `app/infrastructure/auth/jwt.py` 中：
    - key 生成与持久化策略；
    - JWKS 输出字段是否完整（`kty`/`use`/`alg`/`kid`/`n`/`e` 等）；
    - ID Token 与 access_token 使用的签名算法和 kid 是否与 JWKS 对齐。
  - 如果存在多个 key：
    - 定义「当前激活 key」策略；
    - 如有需要，确保旧 key 仍可用于验证历史 token。

- 测试
  - 增加测试：
    - 调用 `/jwks` 获得公钥；
    - 使用该公钥验证 `/token` 返回的 id_token 签名。

### 5.5 测试矩阵补齐

目标：确保 FR/NFR 全部有可自动化验证的测试。

- E2E 测试
  - 已有：`tests/test_oidc_flow.py` 覆盖 S1；
  - 补充：
    - 针对 S2（错误 `client_secret`）、S3（无效/过期授权码）的 E2E 或高层级集成测试。

- 端点级集成测试
  - Discovery：已有 `tests/test_discovery.py`；
  - `/authorize`：
    - GET 参数缺失/错误时的行为；
    - 登录失败时的行为（`access_denied`）。
  - `/token`：
    - `invalid_client` / `invalid_grant` / `unsupported_grant_type`。
  - `/userinfo`：
    - 无 Authorization 头；
    - 使用过期或伪造 token。

- 单元测试
  - 覆盖 AuthorizationService、TokenService、UserInfoService、Claims 服务。

### 5.6 Quickstart 与 README 对齐

目标：让 `README.md` 和 quickstart 与最新实现和 spec 同步。

- 对齐点
  - README 中的授权码流程示例 URL 与实际接口一致；
  - README 中的 demo 用户/客户端与初始化脚本保持一致；
  - 指向 Discovery 和 JWKS 的说明与实际路径一致；
  - 补充一小节「本项目实现的 OIDC 能力范围」（与 spec Non-Goals 保持一致）。

---

## 6. 输出物总结（Planned Artifacts）

实现本计划后，将形成如下设计与实现产出：

- 设计类文档
  - `specs/1-oidc-auth-code/spec.md`
  - `specs/1-oidc-auth-code/checklists/requirements.md`
  - `specs/1-oidc-auth-code/data-model.md`
  - `specs/1-oidc-auth-code/contracts/*`
  - `specs/1-oidc-auth-code/quickstart.md`
- 代码与测试
  - 接口层端点精简与统一的错误处理
  - AuthorizationService / TokenService / UserInfoService 及其单元测试的完善
  - JWT/JWKS 对齐 spec 的实现与测试
  - 针对 FR/NFR 的集成与 E2E 测试矩阵
- 文档与开发者体验
  - README 与 quickstart 同步更新
  - CLI 使用说明与 demo 流程说明

该计划将作为后续拆解任务（tasks）和执行实现的指导基础。

---

## 7. 与 Design.md / 宪章的差异与未来演进

### 7.1 已知差异（有意识的收敛）

- 同步 vs 异步
  - `Design.md` 示例大量采用 async 仓储、async UseCase、AsyncSession 等；
  - 本计划保持当前同步 FastAPI 路由 + 同步 SQLAlchemy Session，不引入 async 复杂度。
- 领域建模深度
  - `Design.md` 中展示了完整的领域层：富实体（Client/EndUser）、值对象（TokenSet）、领域服务（TokenIssuer）、规约（ValidAuthorizationRequestSpec）；
  - 本计划仅在 5.3 预留「领域概念与规约」演进点，短期内仍以应用服务 + 现有 ORM 模型为主承载业务规则。
- 仓储与 UoW 抽象
  - `Design.md` 中使用 `AbstractClientRepository`、`UnitOfWork` 等抽象隔离持久化；
  - 当前实现和本计划阶段继续使用直接依赖 SQLAlchemy Session 的方式，尚未引入完整仓储接口/UoW 框架。
- 安全与可观测性范围
  - 宪章强调安全与可观测性（structured logs、metrics、threat modeling 等）是核心原则；
  - 本计划在授权码流特性上优先落实协议正确性、token 安全和错误处理，对日志/metrics/审计等只在高层原则上承认，尚未拆解为具体实施任务。

这些差异均为**在 B 计划约束下的有意识收敛**：优先保证当前授权码流的可用性和可测试性，而不是一次性推完所有理想化架构示例。

### 7.2 未来演进方向（后续特性候选）

以下演进点不在本次授权码流特性的 Scope 内，但与 `Design.md` 和宪章强相关，适合作为后续独立特性：

1. 引入真正的领域层实现
   - 将 Client / EndUser / AuthorizationCode 从 ORM 模型中抽象为领域实体；
   - 引入值对象（TokenSet、DiscoveryDocument 等）和领域服务（TokenIssuer、CryptoService）；
   - 将「合法授权请求 / 合法 token 请求」规则下沉为规约，实现与 `Design.md` 中示例相近的结构。

2. 仓储与 UnitOfWork 抽象
   - 基于 `Design.md` 的仓储接口示例，为 Client/User/AuthorizationCode 提供抽象仓储接口；
   - 在应用层引入明确的 UnitOfWork 边界，集中管理事务；
   - 通过替换仓储实现支持不同数据库或存储后端。

3. Async 化与高并发友好改造
   - 在现有同步实现稳定后，评估是否需要：
     - 将端点迁移为 async 路由；
     - 引入 AsyncSession 和 async 仓储实现；
   - 该演进应作为单独特性，配合性能目标和压力测试一起设计。

4. 安全与可观测性加强特性
   - 专门的「安全与可观测性」特性，用于：
     - 按宪章要求设计和实现结构化日志、关键 OIDC 事件 metrics；
     - 为认证/授权/加密相关变更补充威胁建模和误用场景测试；
     - 明确日志中不允许出现的敏感字段列表（密码、client_secret、token、key 片段等）。

5. 管理 API 与运维能力
   - 按 `Design.md` 顶层架构中提到的 `/admin/clients` 等管理端点，设计管理类 spec/plan；
   - 提供客户端/用户/密钥等资源的可视化或 API 级管理能力；
   - 保持与分层/宪章一致的架构约束。

未来每当启动上述演进点之一时，应：

- 新建对应的 feature spec（描述业务需求与范围）；
- 新建对应的 plan（明确与本次授权码流 plan 的边界与衔接关系）；
- 在实施前再次对照 `constitution.md` 和 `Design.md`，确保新特性延续当前分层和治理原则。

