# V0.3 Browser / Computer Use

## 目标
把 Agent 从“只能调用后端 API”推进到“能够安全操作网页”。

## 安全边界
1. 浏览默认只读。
2. click / type / submit / upload / download 等产生外部副作用的动作必须经过 Approval Gate。
3. 浏览器运行在独立容器，不允许直接访问宿主机文件系统。
4. 每个会话拥有独立 browser context。
5. 所有动作写入 Audit Event：session、url、selector、action、approval_id、timestamp。
6. 禁止把密码、token、cookie 写入普通 Agent 日志。

## V0.3 接口
- POST /session
- POST /navigate
- GET /snapshot/{session_id}
- POST /click
- POST /type

## 下一步
- Playwright/CDP adapter 接入 Agent Runtime
- DOM + screenshot 双模观察
- download/upload 沙箱
- 登录态隔离
- Computer Use provider adapter
- 失败重试与页面状态机
