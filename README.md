# MCP Atlassian (Enterprise Fork)

Production-oriented MCP server for **private/self-hosted Jira + Confluence** with:

- Full existing Jira/Confluence MCP tool surface preserved
- **Streamable HTTP** deployment path for remote Codex via SSH tunnel
- **stdio** mode retained for local development
- CLI-first startup configuration (with env compatibility fallback)

## Supported transports

- `stdio` (default): local/dev IDE integrations
- `streamable-http`: recommended for enterprise workstation/bastion deployment
- `sse`: compatibility mode

## Quick start

### 1) Local stdio mode

```bash
uv run mcp-atlassian \
  --transport stdio \
  --jira-url https://jira.example.internal \
  --jira-personal-token "$JIRA_TOKEN" \
  --confluence-url https://wiki.example.internal \
  --confluence-personal-token "$CONF_TOKEN"
```

### 2) Production-leaning streamable-http mode

```bash
uv run mcp-atlassian \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8080 \
  --path /mcp \
  --jira-url https://jira.example.internal \
  --jira-personal-token "$JIRA_TOKEN" \
  --confluence-url https://wiki.example.internal \
  --confluence-personal-token "$CONF_TOKEN"
```

> Streamable HTTP requires `--port` to be explicitly provided.

## CLI arguments (key)

Core runtime:

- `--transport [stdio|sse|streamable-http]`
- `--host` (default `127.0.0.1`)
- `--port` (**required for streamable-http**)
- `--path` (default `/mcp`)

Atlassian credentials:

- `--jira-url`
- `--jira-personal-token`
- `--confluence-url`
- `--confluence-personal-token`

Enterprise network/TLS:

- `--http-proxy`
- `--https-proxy`
- `--no-proxy`
- `--request-timeout`
- `--ca-bundle`
- `--insecure-skip-verify` (development-only)

## Configuration precedence

1. CLI arguments
2. Environment variables
3. Internal defaults

Env var compatibility remains available (for example `JIRA_URL`, `JIRA_PERSONAL_TOKEN`,
`CONFLUENCE_URL`, `CONFLUENCE_PERSONAL_TOKEN`, `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`).

## Private enterprise deployment notes

- Prefer binding `--host 127.0.0.1` and expose via SSH forwarding only.
- Keep Jira/Confluence tokens on the internal host/workstation.
- Prefer TLS verification + custom `--ca-bundle` over disabling verification.

See [DEPLOYMENT.md](DEPLOYMENT.md) and [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
