# 企业 MCP 规划

建议每个企业系统独立 MCP Server：

- oa-mcp
- erp-mcp
- project-mcp
- bim-mcp
- iot-mcp
- water-mcp
- document-mcp
- database-mcp

Agent 只看到经过权限过滤后的 tools。

## Tool 命名
`domain.action`

示例：
- project.list_projects
- project.get_task
- project.update_task
- bim.search_elements
- bim.detect_clashes
- iot.query_points
- water.query_realtime
- document.search

## 高风险操作
写入、删除、审批、发送邮件、控制设备等操作必须支持：
`preview -> approval -> execute -> audit`
