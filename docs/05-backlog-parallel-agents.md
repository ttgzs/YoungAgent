# 并行子智能体实施 Backlog

本仓库按“可并行、可验收”的工作包拆分：

- Agent-Core：Planner/Executor/Observation/Reflection、长任务状态机
- Model：OpenAI-compatible + structured tool calling + streaming
- MCP：registry/auth/policy/tenant/audit + MCP SDK transport
- Browser：Playwright/CDP + Browser Use adapter + approval
- Computer：screenshot/action loop + UI-TARS adapter + permission
- Data：PostgreSQL/Redis/event bus/vector memory
- Security：JWT/OIDC/RBAC/tenant isolation/audit
- Skills：manifest/version/dependency/permission/marketplace
- Domain：project/BIM/document/water/IoT MCP servers
- Desktop：Electron shell + local file permission + OS action approval
- QA：unit/integration/e2e/load/security tests

合并原则：每个工作包只通过接口依赖其它模块，避免互相修改核心文件。
