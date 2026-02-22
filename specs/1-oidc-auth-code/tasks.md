# Tasks: 简化 OIDC Provider 授权码流

- Feature Spec: `specs/1-oidc-auth-code/spec.md`
- Plan: `specs/1-oidc-auth-code/plan.md`
- Checklist: `specs/1-oidc-auth-code/checklists/requirements.md`

本任务清单按 speckit.tasks 约定组织，分为：

- Phase 1–2：通用准备与基础工作（无特定用户故事标签）
- Phase 3+：按用户场景（US1–US3）划分的实现与测试任务
- Final Phase：收尾与跨切关注点

任务格式遵循：

```text
- [ ] T001 [P?] [US?] 描述 + 具体文件路径
```

---

## Phase 1 – Setup（环境与基础命令）

- [ ] T001 验证测试命令配置是否可用（pyproject.toml, app/cli.py）
- [ ] T002 [P] 确认本地开发环境与依赖安装方式（pyproject.toml, README.md）

---

## Phase 2 – Foundational（跨故事基础设计与检查）

- [ ] T003 审阅现有 OIDC 端点实现并对照 spec 映射行为（app/api/v1/endpoints/oidc/authorization.py）
- [ ] T004 审阅现有 Token 端点与 UserInfo 端点实现并对照 spec 映射行为（app/api/v1/endpoints/oidc/token.py）
- [ ] T005 [P] 在数据模型文档中描述实体与约束（specs/1-oidc-auth-code/data-model.md）
- [ ] T006 [P] 在契约文档中整理各 OIDC 端点的请求和响应格式（specs/1-oidc-auth-code/contracts/endpoints.md）
- [ ] T007 [P] 在 quickstart 文档中记录手工走通授权码流的步骤（specs/1-oidc-auth-code/quickstart.md）
- [ ] T008 检查并记录 JWT 与 JWKS 实现与计划的一致性（app/infrastructure/auth/jwt.py）

---

## Phase 3 – User Story 1（US1：授权码登录 + UserInfo 获取成功）

目标：实现并验证「S1：授权码登录 + UserInfo 获取（成功路径）」的完整用例，满足 spec 中对正常流程的所有 FR 要求。

- [ ] T009 [US1] 校对 AuthorizationService 行为与 S1 场景和 FR-6~FR-13 一致（app/application/services/authorization_service.py）
- [ ] T010 [US1] 校对 TokenService 行为与 S1 场景和 FR-14~FR-19 一致（app/application/services/token_service.py）
- [ ] T011 [US1] 设计或完善 UserInfo 服务/逻辑以满足 FR-20~FR-23（app/api/v1/endpoints/oidc/userinfo.py）
- [ ] T012 [P] [US1] 为 AuthorizationService S1 正常路径补充单元测试（tests/test_authorization_service.py）
- [ ] T013 [P] [US1] 为 TokenService S1 正常路径补充单元测试（tests/test_token_service.py）
- [ ] T014 [P] [US1] 为 UserInfo 服务补充单元测试覆盖合法 access_token 情况（tests/test_userinfo.py）
- [ ] T015 [US1] 扩充或调整 E2E 测试以完全覆盖 S1 期望行为（tests/test_oidc_flow.py）

---

## Phase 4 – User Story 2（US2：错误客户端密钥处理 invalid_client）

目标：实现并验证「S2：错误 client_secret 导致 token 获取失败」的错误路径，用 OIDC `invalid_client` 错误码清晰反馈。

- [ ] T016 [US2] 确认 TokenService 中错误 client_secret 时返回业务层 invalid_client 错误（app/application/services/token_service.py）
- [ ] T017 [P] [US2] 为错误 client_secret 场景补充单元测试，覆盖 invalid_client 分支（tests/test_token_service.py）
- [ ] T018 [P] [US2] 为错误 client_secret 场景新增或扩展集成/E2E 测试用例（tests/test_oidc_flow.py）

---

## Phase 5 – User Story 3（US3：无效或过期授权码处理 invalid_grant）

目标：实现并验证「S3：无效或过期授权码被使用」的错误路径，用 OIDC `invalid_grant` 错误码统一反馈所有无效授权码情形。

- [ ] T019 [US3] 完整实现 TokenService 对无效/已用/过期授权码和不匹配 redirect_uri 的 invalid_grant 处理（app/application/services/token_service.py）
- [ ] T020 [P] [US3] 为 invalid_grant 场景补充单元测试，覆盖所有无效授权码分支（tests/test_token_service.py）
- [ ] T021 [P] [US3] 为无效/过期授权码场景新增或扩展集成/E2E 测试用例（tests/test_oidc_flow.py）

---

## Final Phase – Polish & Cross-Cutting Concerns

- [ ] T022 对齐 README 中的授权码流程说明与当前实现及 spec（README.md）
- [ ] T023 审查并微调接口层端点以保持“薄控制器”原则（app/api/v1/endpoints/oidc/authorization.py）
- [ ] T024 对照 plan.md 7.2 中的未来演进点，记录当前实现的已完成程度（specs/1-oidc-auth-code/plan.md）

---

## Dependencies & Execution Order

高层依赖关系：

1. Phase 1（T001–T002）为所有后续工作的前置条件。
2. Phase 2（T003–T008）为理解现状和对齐文档的基础，应在开始具体用户故事实现前完成。
3. Phase 3（US1，T009–T015）依赖 Phase 1–2，是本特性的 MVP 范围。
4. Phase 4（US2，T016–T018）依赖 US1 中 TokenService 的基本成功路径实现。
5. Phase 5（US3，T019–T021）依赖 US1 中授权码成功路径逻辑和数据模型。
6. Final Phase（T022–T024）在主要功能实现后执行，用于收尾与文档对齐。

---

## Parallel Execution Examples

在以下任务之间，可以安全并行执行（标记为 `[P]` 的任务尤为适合并行）：

- Phase 2：
  - T005（data-model.md）与 T006（contracts/endpoints.md）、T007（quickstart.md）可以在完成 T003–T004 后并行推进。
- Phase 3（US1）：
  - T012、T013、T014 三个单元测试任务彼此独立，可并行实施。
- Phase 4（US2）与 Phase 5（US3）：
  - T017、T018 与 T020、T021 可以在对应业务逻辑实现完成后并行编写和运行。

---

## Implementation Strategy（MVP 优先）

- 首个 MVP 范围建议为 **US1（Phase 3，T009–T015）**：
  - 在已存在的基础上，确保授权码登录 + UserInfo 成功路径与 spec 完全一致，并通过单元 + E2E 测试验证。
- 在 MVP 稳定后，依次实现 US2 → US3，以补齐关键错误路径和安全性。
- 最后执行 Final Phase，保证 README、plan 和实际实现对齐，为后续更深层次的领域建模和安全/可观测性增强特性铺路。

