# Deployment Guide

## Recommended topology

`Codex (remote Linux) -> SSH tunnel -> localhost-bound MCP server -> private Jira/Confluence`

Run MCP on the internal workstation/bastion, not on the remote Codex machine.

## Start server (streamable-http)

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

Optional enterprise flags:

```bash
  --http-proxy http://proxy.internal:8080 \
  --https-proxy http://proxy.internal:8080 \
  --no-proxy localhost,127.0.0.1,.example.internal \
  --ca-bundle /etc/ssl/certs/internal-ca.pem \
  --request-timeout 60
```

## SSH forward example

From Codex host to internal host:

```bash
ssh -N -L 18080:127.0.0.1:8080 user@internal-host
```

Then Codex points to `http://127.0.0.1:18080/mcp`.

## Codex MCP URL example

```json
{
  "mcpServers": {
    "atlassian-private": {
      "url": "http://127.0.0.1:18080/mcp"
    }
  }
}
```

## Security notes

- Default bind should stay `127.0.0.1` unless intentional external exposure is required.
- Keep personal tokens on internal host only.
- If directly exposed on network, prefer HTTPS termination, network ACLs, and host firewall rules.
