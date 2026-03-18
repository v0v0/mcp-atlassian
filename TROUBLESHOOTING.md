# Troubleshooting

## Proxy issues

- Verify `--http-proxy` / `--https-proxy` values.
- Add Atlassian host to `--no-proxy` when proxy bypass is needed.

## DNS / routing issues

- Test host resolution from the MCP host (`nslookup jira.example.internal`).
- Validate internal routing/firewall from MCP host to Jira/Confluence.

## Certificate / CA issues

- Prefer `--ca-bundle /path/to/internal-ca.pem` for private PKI.
- Use `--insecure-skip-verify` only for short-lived development diagnostics.

## Atlassian auth failures

- Confirm URL/token pair belong to the same deployment.
- For Server/DC, use personal tokens (`--jira-personal-token`, `--confluence-personal-token`).

## MCP endpoint unreachable

- Streamable HTTP requires explicit `--port`.
- Validate bind target is reachable (`curl http://127.0.0.1:8080/mcp`).
- Validate SSH tunnel local port maps to the MCP host listen port.

## Invalid CLI combos

- `--stateless` is valid only with `--transport streamable-http`.
- `--transport streamable-http` requires explicit `--port`.
