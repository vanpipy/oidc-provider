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

## 测试与验证

下表汇总了当前可用的测试命令及其适用场景。

| 场景 | 命令 | 描述 | 依赖/前提 |
|------|------|------|-----------|
| 全量测试（单元 + 内嵌 e2e） | `python -m app.cli test` | 运行整个 pytest 测试套件（`tests/` + `e2e/`），适合作为本地回归检查。 | 已安装依赖：`pip install -e .[dev]` |
| 仅单元/服务层测试 | `python -m app.cli test_unit` | 只运行 `tests/` 目录下的用例，快速验证领域服务、应用服务等逻辑，不启动 HTTP 服务器。 | 已安装依赖 |
| 内嵌服务器 e2e 黑盒测试 | `python -m app.cli test_e2e_embedded` | 在当前进程内启动 uvicorn 服务器并运行 `e2e/` 目录下的端到端用例，使用本地 SQLite 与 `seed_demo` 初始化的数据。 | 已安装依赖；本地可绑定端口 `8001`（测试默认使用 `E2E_BASE_URL=http://127.0.0.1:8001`） |
| 外部服务器 e2e 黑盒测试（手动起服务） | `python -m app.cli test_e2e_external` | 假设 OIDC Provider 已经在外部运行，仅作为“纯客户端”针对 `E2E_BASE_URL` 运行 `e2e/` 用例，用于黑盒验证已有服务。 | 需要预先启动服务并设置 `E2E_BASE_URL`（默认 `http://127.0.0.1:8001`） |
| Docker 容器化 e2e 测试（一键） | `python scripts/docker_e2e_test.py` | 基于已构建的 Docker 镜像自动 `docker run` 启动容器、等待服务就绪，然后以外部模式运行 `e2e/` 黑盒测试，最后自动停止容器。 | 需要本地 Docker 环境；需先执行 `docker build -t oidc-provider .` |

