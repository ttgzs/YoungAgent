# YoungAgent V5.0 — Enterprise Agent OS

V5.0 consolidates Agent Studio, Workflow Studio, Marketplace, Knowledge, MCP/Tools, Approval and Audit into one enterprise console.

## Development

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

Web: http://localhost:5173
Agent API: http://localhost:8000

## macOS Apple Silicon

```bash
cd apps/desktop
npm install
npm run dist:mac-arm64
```

The desktop project targets `arm64` for Apple Silicon Macs.
