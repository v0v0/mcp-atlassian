# ruff: noqa: FBT001
import asyncio
import logging
import os
import sys
import threading
from importlib.metadata import PackageNotFoundError, version

import click
from dotenv import dotenv_values, load_dotenv

from mcp_atlassian.atlassian import apply_cli_env_overrides
from mcp_atlassian.config import resolve_runtime_config
from mcp_atlassian.transport import build_run_kwargs, describe_bind
from mcp_atlassian.utils.env import is_env_truthy
from mcp_atlassian.utils.lifecycle import ensure_clean_exit, setup_signal_handlers
from mcp_atlassian.utils.logging import setup_logging

# Inject truststore BEFORE any requests/urllib3 imports to ensure the
# OS-native trust store (e.g. Windows Certificate Store) is used for
# SSL verification instead of the bundled certifi CA certificates.
if os.getenv(
    "MCP_ATLASSIAN_USE_SYSTEM_TRUSTSTORE",
    dotenv_values().get("MCP_ATLASSIAN_USE_SYSTEM_TRUSTSTORE") or "true",
).lower() not in ("false", "0", "no"):
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:  # noqa: BLE001
        logging.getLogger("mcp-atlassian").warning(
            "Failed to inject OS trust store; falling back to bundled certificates",
            exc_info=True,
        )

# Fix high CPU usage on Windows.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    __version__ = version("mcp-atlassian")
except PackageNotFoundError:
    __version__ = "0.0.0"

logging_level = logging.WARNING
if is_env_truthy("MCP_VERBOSE"):
    logging_level = logging.DEBUG
logging_stream = sys.stdout if is_env_truthy("MCP_LOGGING_STDOUT") else sys.stderr
logger = setup_logging(logging_level, logging_stream)


async def _watch_parent_exit(stop_event: threading.Event) -> None:
    parent_pid = os.getppid()
    loop = asyncio.get_running_loop()

    def _poll_parent_alive() -> None:
        while not stop_event.wait(5):
            if os.getppid() != parent_pid:
                logger.info("Parent process exited. Shutting down STDIO server.")
                return

    await loop.run_in_executor(None, _poll_parent_alive)


async def _run_stdio_with_stdin_guard(run_kwargs: dict[str, object]) -> None:
    from mcp_atlassian.servers import main_mcp

    parent_watch_stop = threading.Event()
    server_task = asyncio.create_task(main_mcp.run_async(**run_kwargs))
    parent_task = asyncio.create_task(_watch_parent_exit(parent_watch_stop))

    done, pending = await asyncio.wait(
        {server_task, parent_task},
        return_when=asyncio.FIRST_COMPLETED,
    )
    parent_watch_stop.set()

    if parent_task in done and not server_task.done():
        logger.info("Parent process exited. Shutting down STDIO server.")
        server_task.cancel()

    for task in pending:
        task.cancel()

    await asyncio.gather(*pending, return_exceptions=True)

    if server_task.done():
        server_result = await asyncio.gather(server_task, return_exceptions=True)
        if (
            server_result
            and isinstance(server_result[0], Exception)
            and not isinstance(server_result[0], asyncio.CancelledError)
        ):
            raise server_result[0]


@click.version_option(__version__, prog_name="mcp-atlassian")
@click.command()
@click.option("-v", "--verbose", count=True, help="Increase verbosity")
@click.option("--env-file", type=click.Path(exists=True, dir_okay=False))
@click.option("--oauth-setup", is_flag=True, help="Run OAuth 2.0 setup wizard")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
)
@click.option("--stateless", is_flag=True)
@click.option("--host", default="127.0.0.1")
@click.option("--port", type=int, default=8000)
@click.option("--path", default="/mcp")
@click.option("--confluence-url")
@click.option("--confluence-username")
@click.option("--confluence-token")
@click.option("--confluence-personal-token")
@click.option("--confluence-ssl-verify/--no-confluence-ssl-verify", default=True)
@click.option("--confluence-spaces-filter")
@click.option("--jira-url")
@click.option("--jira-username")
@click.option("--jira-token")
@click.option("--jira-personal-token")
@click.option("--jira-ssl-verify/--no-jira-ssl-verify", default=True)
@click.option("--jira-projects-filter")
@click.option("--read-only", is_flag=True)
@click.option("--enabled-tools")
@click.option("--toolsets")
@click.option("--oauth-client-id")
@click.option("--oauth-client-secret")
@click.option("--oauth-redirect-uri")
@click.option("--oauth-scope")
@click.option("--oauth-cloud-id")
@click.option("--oauth-access-token")
@click.option("--http-proxy")
@click.option("--https-proxy")
@click.option("--no-proxy")
@click.option("--request-timeout", type=int, default=75, show_default=True)
@click.option("--ca-bundle")
@click.option("--insecure-skip-verify", is_flag=True)
def main(
    verbose: int,
    env_file: str | None,
    oauth_setup: bool,
    transport: str,
    stateless: bool,
    host: str,
    port: int,
    path: str,
    confluence_url: str | None,
    confluence_username: str | None,
    confluence_token: str | None,
    confluence_personal_token: str | None,
    confluence_ssl_verify: bool,
    confluence_spaces_filter: str | None,
    jira_url: str | None,
    jira_username: str | None,
    jira_token: str | None,
    jira_personal_token: str | None,
    jira_ssl_verify: bool,
    jira_projects_filter: str | None,
    read_only: bool,
    enabled_tools: str | None,
    toolsets: str | None,
    oauth_client_id: str | None,
    oauth_client_secret: str | None,
    oauth_redirect_uri: str | None,
    oauth_scope: str | None,
    oauth_cloud_id: str | None,
    oauth_access_token: str | None,
    http_proxy: str | None,
    https_proxy: str | None,
    no_proxy: str | None,
    request_timeout: int,
    ca_bundle: str | None,
    insecure_skip_verify: bool,
) -> None:  # noqa: FBT001
    if verbose == 1:
        current_logging_level = logging.INFO
    elif verbose >= 2:
        current_logging_level = logging.DEBUG
    elif is_env_truthy("MCP_VERY_VERBOSE", "false"):
        current_logging_level = logging.DEBUG
    elif is_env_truthy("MCP_VERBOSE", "false"):
        current_logging_level = logging.INFO
    else:
        current_logging_level = logging.WARNING

    log_stream = sys.stdout if is_env_truthy("MCP_LOGGING_STDOUT") else sys.stderr
    global logger
    logger = setup_logging(current_logging_level, log_stream)

    if env_file:
        load_dotenv(env_file, override=True)
    else:
        load_dotenv(override=True)

    if oauth_setup:
        from .utils.oauth_setup import run_oauth_setup

        sys.exit(run_oauth_setup())

    click_ctx = click.get_current_context(silent=True)
    if click_ctx is None:
        raise click.ClickException("Failed to initialize CLI context")

    cli_values = {
        "transport": transport,
        "stateless": stateless,
        "host": host,
        "port": port,
        "path": path,
        "confluence_url": confluence_url,
        "confluence_username": confluence_username,
        "confluence_token": confluence_token,
        "confluence_personal_token": confluence_personal_token,
        "confluence_ssl_verify": confluence_ssl_verify,
        "confluence_spaces_filter": confluence_spaces_filter,
        "jira_url": jira_url,
        "jira_username": jira_username,
        "jira_token": jira_token,
        "jira_personal_token": jira_personal_token,
        "jira_ssl_verify": jira_ssl_verify,
        "jira_projects_filter": jira_projects_filter,
        "read_only": read_only,
        "enabled_tools": enabled_tools,
        "toolsets": toolsets,
        "oauth_client_id": oauth_client_id,
        "oauth_client_secret": oauth_client_secret,
        "oauth_redirect_uri": oauth_redirect_uri,
        "oauth_scope": oauth_scope,
        "oauth_cloud_id": oauth_cloud_id,
        "oauth_access_token": oauth_access_token,
        "http_proxy": http_proxy,
        "https_proxy": https_proxy,
        "no_proxy": no_proxy,
        "request_timeout": request_timeout,
        "ca_bundle": ca_bundle,
        "insecure_skip_verify": insecure_skip_verify,
    }

    runtime_config = resolve_runtime_config(click_ctx, cli_values)
    apply_cli_env_overrides(click_ctx, cli_values)

    from mcp_atlassian.servers import main_mcp

    run_kwargs = build_run_kwargs(runtime_config, current_logging_level)
    logger.info(describe_bind(runtime_config))
    setup_signal_handlers()

    try:
        if runtime_config.transport == "stdio":
            asyncio.run(_run_stdio_with_stdin_guard(run_kwargs))
        else:
            asyncio.run(main_mcp.run_async(**run_kwargs))
    except (KeyboardInterrupt, SystemExit) as exc:
        logger.info("Server shutdown initiated: %s", type(exc).__name__)
    except Exception as exc:
        logger.error("Server encountered an error: %s", exc, exc_info=True)
        sys.exit(1)
    finally:
        ensure_clean_exit()


__all__ = ["main", "__version__"]

if __name__ == "__main__":
    main()
