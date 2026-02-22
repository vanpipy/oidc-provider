# Tasks: OIDC Provider 的 Docker 部署

- Feature Spec: `specs/2-docker-deployment/spec.md`
- Plan: `specs/2-docker-deployment/plan.md`
- Checklist: `specs/2-docker-deployment/checklists/requirements.md`

本任务清单按 speckit.tasks 风格组织，覆盖从镜像构建到文档更新的主要工作。

任务格式遵循：

```text
- [ ] TD01 描述 + 具体文件路径
```

---

## Phase D1 – 设计与规格完善

- [ ] TD01 审阅并在必要时修订 Docker 部署需求规格（specs/2-docker-deployment/spec.md）
- [ ] TD02 使用 requirements 清单对规格进行自检并更新勾选状态（specs/2-docker-deployment/checklists/requirements.md）

---

## Phase D2 – 镜像构建与本地运行

- [ ] TD03 设计并实现基础 Docker 镜像定义（仓库根目录，Docker 相关文件）
- [ ] TD04 在本地构建镜像并验证容器运行（端点与授权码流行为与现有实现一致）
- [ ] TD05 增加针对容器运行场景的最小化验证步骤（可纳入 quickstart 或单独文档）

---

## Phase D3 – 测试与 CI 集成

- [ ] TD06 设计测试在容器环境中运行的策略（复用 `python -m app.cli test` 或变体）
- [ ] TD07 在本地验证使用容器运行测试的可行性（可选，不强制要求替代当前流程）
- [ ] TD08 在 CI 配置中预留或增加使用 Docker 镜像运行测试的步骤（CI 配置文件）

---

## Phase D4 – 文档与开发者体验

- [ ] TD09 在 quickstart 或新文档中补充 Docker 运行说明（specs/2-docker-deployment 下或 quickstart.md）
- [ ] TD10 在 README 中增加简要的 Docker 部署说明，并指向详细文档（README.md）

---

## Dependencies & Execution Order

高层依赖关系：

1. Phase D1（TD01–TD02）为所有后续工作的规格基础，应优先完成。
2. Phase D2（TD03–TD05）提供可用的本地镜像，是测试与 CI 集成的前提。
3. Phase D3（TD06–TD08）依赖镜像构建和本地验证结果，用于扩展到 CI 场景。
4. Phase D4（TD09–TD10）在主要功能稳定后执行，用于收尾与文档对齐。

