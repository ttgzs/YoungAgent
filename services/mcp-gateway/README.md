# Enterprise MCP Gateway

V3.6 provides a domain connector MCP-compatible service behind this gateway.

Domain connector groups:
- project: Project schedule, variance, Microsoft Project XML summary
- bim: IFC summary/elements/quantity
- water: wastewater KPIs and advisory aeration
- iot: telemetry aggregation and threshold alarms

The gateway remains the policy boundary. Vendor-specific systems should be connected behind the domain MCP service, not directly from Agent Runtime.
