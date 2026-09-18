# Parallel Agent Team Execution Plan

本项目后续采用“主 Agent + 专业 Agent Team”模式，而不是无边界创建子 Agent。

## 调度原则
- 主 Agent 负责任务拆解、依赖分析、合并和最终验收。
- 独立工作包可并行执行。
- 涉及同一代码文件的工作包必须串行合并，避免冲突。
- 高风险 Tool 必须统一进入 Approval Gate。
- 子 Agent 不直接拥有生产环境凭据。

## Team
1. Core：Runtime / Planner / Executor
2. Model：LLM / Tool Calling / Structured Output
3. MCP：企业工具协议、租户、权限
4. Browser：Playwright / CDP / DOM
5. Computer：截图、鼠标键盘、桌面应用
6. Data：PostgreSQL / Redis / Memory
7. Security：SSO / RBAC / Audit
8. Skill：技能包、版本、依赖、市场
9. Domain：项目、BIM、水务、IoT、工程文档
10. Desktop：Electron / OS 文件和应用权限

## 并行规则
P0 基础设施完成后，P1-P5 可以并行；依赖运行时 API 的任务以接口契约作为边界。
