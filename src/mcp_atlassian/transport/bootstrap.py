"""Transport bootstrapping helpers for stdio and HTTP modes."""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import settings as fastmcp_settings

from mcp_atlassian.config import RuntimeConfig

logger = logging.getLogger("mcp-atlassian.transport")


def build_run_kwargs(config: RuntimeConfig, logging_level: int) -> dict[str, Any]:
    """Build FastMCP run kwargs from resolved runtime config."""
    run_kwargs: dict[str, Any] = {"transport": config.transport}

    if config.transport in {"sse", "streamable-http"}:
        if config.port is None:
            raise ValueError("HTTP transports require a resolved listen port.")

        run_kwargs.update(
            {
                "host": config.host,
                "port": config.port,
                "path": config.path,
                "stateless_http": config.stateless_http,
                "log_level": logging.getLevelName(logging_level).lower(),
            }
        )

    return run_kwargs


def describe_bind(config: RuntimeConfig) -> str:
    """Generate startup log message for active transport/bind."""
    if config.transport == "stdio":
        return "Starting server with STDIO transport."

    if config.port is None:
        raise ValueError("HTTP transports require a port.")

    effective_path = config.path
    if not effective_path:
        if config.transport == "sse":
            effective_path = fastmcp_settings.sse_path or "/sse"
        else:
            effective_path = fastmcp_settings.streamable_http_path or "/mcp"

    return (
        f"Starting server with {config.transport.upper()} transport on "
        f"http://{config.host}:{config.port}{effective_path}"
    )
