# 实施状态 V0.2-V1.0

## 已落地
- Model Gateway：OpenAI-compatible，兼容 OpenAI/Qwen/DeepSeek/Doubao/本地兼容 API。
- PostgreSQL + SQLite fallback 数据层。
- Redis 配置入口。
- Task/Event 持久化。
- SSE Agent streaming。
- Native Tool Registry：filesystem、Python sandbox。
- MCP Gateway 独立服务与工具注册接口。
- Approval Gate：高风险动作预览/审批/执行接口骨架。
- Browser Adapter / Computer Use Adapter 插拔接口。
- Vue 3 执行轨迹 UI。

## 下一批企业化任务
1. 接入真实 MCP SDK transport 与 OAuth/tenant auth。
2. Browser Use + Playwright/CDP 实装。
3. Computer Use 接入 UI-TARS 类模型与截图/action loop。
4. Redis event bus + Celery/Arq worker，实现长任务与并发 Agent。
5. RBAC/SSO/JWT、审计日志、租户隔离。
6. Skill manifest、版本、依赖、权限、市场。
7. 知识库：PostgreSQL pgvector 或独立向量库。
8. 企业 MCP Server：OA/ERP/项目/BIM/文档/IoT/水务。
9. Multi-Agent：researcher、planner、coder、reviewer、domain agents。
10. Desktop Electron 壳、文件权限、浏览器/桌面操作审批。
