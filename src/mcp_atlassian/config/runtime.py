"""Runtime configuration resolution for MCP Atlassian server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import click

from mcp_atlassian.utils.env import is_env_truthy


@dataclass
class RuntimeConfig:
    """Resolved runtime configuration with CLI-over-env precedence."""

    transport: str
    stateless_http: bool
    host: str
    port: int | None
    path: str
    request_timeout: int


def was_option_provided(ctx: click.Context, param_name: str) -> bool:
    """Return True when a Click option came from CLI args."""
    source = ctx.get_parameter_source(param_name)
    return (
        source != click.core.ParameterSource.DEFAULT_MAP
        and source != click.core.ParameterSource.DEFAULT
    )


def _resolve_value(
    *,
    ctx: click.Context,
    cli_name: str,
    cli_value: Any,
    env_name: str,
    default: Any,
) -> Any:
    if was_option_provided(ctx, cli_name):
        return cli_value
    env_value = os.getenv(env_name)
    if env_value is not None:
        return env_value
    return default


def resolve_runtime_config(
    ctx: click.Context, cli_values: dict[str, Any]
) -> RuntimeConfig:
    """Resolve runtime server options with precedence CLI > ENV > defaults."""
    transport = str(
        _resolve_value(
            ctx=ctx,
            cli_name="transport",
            cli_value=cli_values["transport"],
            env_name="TRANSPORT",
            default="stdio",
        )
    ).lower()

    if transport not in {"stdio", "sse", "streamable-http"}:
        message = (
            f"Unsupported transport '{transport}'. "
            "Use stdio, sse, or streamable-http."
        )
        raise click.BadParameter(
            message,
            param_hint="--transport",
        )

    stateless_env = is_env_truthy("STATELESS", "false")
    stateless_http = (
        cli_values["stateless"]
        if was_option_provided(ctx, "stateless")
        else stateless_env
    )

    if stateless_http and transport != "streamable-http":
        raise click.BadParameter(
            "--stateless is only valid with --transport streamable-http.",
            param_hint="--stateless",
        )

    host = str(
        _resolve_value(
            ctx=ctx,
            cli_name="host",
            cli_value=cli_values["host"],
            env_name="HOST",
            default="127.0.0.1",
        )
    )

    path = str(
        _resolve_value(
            ctx=ctx,
            cli_name="path",
            cli_value=cli_values["path"],
            env_name="STREAMABLE_HTTP_PATH",
            default="/mcp",
        )
    )

    request_timeout_raw = _resolve_value(
        ctx=ctx,
        cli_name="request_timeout",
        cli_value=cli_values["request_timeout"],
        env_name="REQUEST_TIMEOUT",
        default=75,
    )
    try:
        request_timeout = int(request_timeout_raw)
    except (TypeError, ValueError) as exc:
        raise click.BadParameter(
            "REQUEST_TIMEOUT/--request-timeout must be an integer.",
            param_hint="--request-timeout",
        ) from exc

    port: int | None = None
    if transport in {"sse", "streamable-http"}:
        if transport == "streamable-http" and not was_option_provided(ctx, "port"):
            raise click.BadParameter(
                "--port is required for --transport streamable-http.",
                param_hint="--port",
            )

        raw_port = _resolve_value(
            ctx=ctx,
            cli_name="port",
            cli_value=cli_values["port"],
            env_name="PORT",
            default=8000,
        )
        try:
            port = int(raw_port)
        except (TypeError, ValueError) as exc:
            raise click.BadParameter(
                "PORT/--port must be an integer.",
                param_hint="--port",
            ) from exc

    return RuntimeConfig(
        transport=transport,
        stateless_http=stateless_http,
        host=host,
        port=port,
        path=path,
        request_timeout=request_timeout,
    )
