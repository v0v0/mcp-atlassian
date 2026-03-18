from click.testing import CliRunner

import mcp_atlassian
from mcp_atlassian import main


def _short_circuit_asyncio_run(coro):
    coro.close()
    return None


def test_cli_precedence_over_env_for_jira_token(monkeypatch):
    monkeypatch.setenv("TRANSPORT", "stdio")
    monkeypatch.setenv("JIRA_PERSONAL_TOKEN", "from-env")
    monkeypatch.setattr(mcp_atlassian.asyncio, "run", _short_circuit_asyncio_run)

    runner = CliRunner()
    result = runner.invoke(main, ["--jira-personal-token", "from-cli"])

    assert result.exit_code == 0


def test_streamable_http_requires_port_argument(monkeypatch):
    monkeypatch.setenv("TRANSPORT", "stdio")
    monkeypatch.setattr(mcp_atlassian.asyncio, "run", _short_circuit_asyncio_run)
    runner = CliRunner()
    result = runner.invoke(main, ["--transport", "streamable-http"])

    assert result.exit_code != 0
    assert "--port is required" in result.output


def test_streamable_http_accepts_explicit_port(monkeypatch):
    monkeypatch.setenv("TRANSPORT", "stdio")
    monkeypatch.setattr(mcp_atlassian.asyncio, "run", _short_circuit_asyncio_run)
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--transport",
            "streamable-http",
            "--host",
            "127.0.0.1",
            "--port",
            "8080",
        ],
    )

    assert result.exit_code == 0
