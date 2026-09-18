# 验收标准

## V0.2
- `/health` 返回 ok。
- `/api/v1/agent/run` 能创建任务并保存 task/event。
- `/api/v1/agent/stream` 持续输出 SSE 事件。
- 无模型配置时系统仍可运行骨架任务，不泄漏密钥。
- filesystem 与 Python sandbox 可用。
- MCP Gateway 可独立启动并返回 tools。
- Approval Gate 可创建/批准/查询审批。

## V0.3
- 浏览器导航、截图、下载上传、CDP 生命周期可测试。
- 浏览器写操作必须经过 approval。

## V0.4
- 截图 -> 模型 -> action -> 截图闭环。
- 鼠标键盘动作有域名/应用/坐标级权限策略。

## V0.5
- OIDC/JWT、RBAC、tenant isolation、audit 完成。
- Skill 有 manifest、版本、依赖、权限声明。
- Knowledge 支持检索、引用和删除。

## V1.0
- 多 Agent DAG/并行执行、失败重试、人工接管。
- Project/BIM/Document/IoT/Water 领域 MCP 可插拔。
- E2E、负载、权限和审计测试通过。
