# 企业 Agent 平台 V1.0 架构

```text
Vue3/Electron
      |
      v
API Gateway
      |
      v
Agent Runtime
  | Planner
  | Executor
  | Observation
  | Memory
  |
  +---- Tool Registry
  |        +-- Native Tools
  |        +-- MCP Tools
  |        +-- Skills
  |
  +---- Browser Adapter
  |
  +---- Computer Use Adapter
  |
  +---- Model Gateway
             +-- OpenAI
             +-- Qwen
             +-- DeepSeek
             +-- Doubao
             +-- Local
```

## 原则
1. Agent Runtime 自己掌握任务状态，不把业务逻辑绑死在某个开源 Agent。
2. 外部能力优先 MCP 化。
3. Browser/Computer Use 通过 Adapter 插拔。
4. Model Gateway 屏蔽模型差异。
5. Skill 是业务能力封装，不直接污染 Agent Core。
6. 所有高风险动作预留 Approval Gate。

## 开源项目使用策略
- OpenManus：General Agent 架构参考
- Trae Agent：模块化 Agent/Tool/CLI 参考
- OpenHands：Coding Agent/Sandbox 参考
- Browser Use：Browser Adapter 候选
- UI-TARS Desktop：Computer Use 候选
- MCP：企业系统统一工具协议
