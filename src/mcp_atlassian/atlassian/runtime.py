"""Atlassian runtime wiring utilities."""

from __future__ import annotations

import os
from typing import Any

import click

from mcp_atlassian.config import was_option_provided

CLI_TO_ENV: dict[str, str] = {
    "enabled_tools": "ENABLED_TOOLS",
    "toolsets": "TOOLSETS",
    "confluence_url": "CONFLUENCE_URL",
    "confluence_username": "CONFLUENCE_USERNAME",
    "confluence_token": "CONFLUENCE_API_TOKEN",
    "confluence_personal_token": "CONFLUENCE_PERSONAL_TOKEN",
    "jira_url": "JIRA_URL",
    "jira_username": "JIRA_USERNAME",
    "jira_token": "JIRA_API_TOKEN",
    "jira_personal_token": "JIRA_PERSONAL_TOKEN",
    "oauth_client_id": "ATLASSIAN_OAUTH_CLIENT_ID",
    "oauth_client_secret": "ATLASSIAN_OAUTH_CLIENT_SECRET",
    "oauth_redirect_uri": "ATLASSIAN_OAUTH_REDIRECT_URI",
    "oauth_scope": "ATLASSIAN_OAUTH_SCOPE",
    "oauth_cloud_id": "ATLASSIAN_OAUTH_CLOUD_ID",
    "oauth_access_token": "ATLASSIAN_OAUTH_ACCESS_TOKEN",
    "confluence_spaces_filter": "CONFLUENCE_SPACES_FILTER",
    "jira_projects_filter": "JIRA_PROJECTS_FILTER",
    "http_proxy": "HTTP_PROXY",
    "https_proxy": "HTTPS_PROXY",
    "no_proxy": "NO_PROXY",
    "ca_bundle": "REQUESTS_CA_BUNDLE",
}


def apply_cli_env_overrides(ctx: click.Context, cli_values: dict[str, Any]) -> None:
    """Apply CLI values to env vars used by existing Jira/Confluence config loaders."""
    for cli_key, env_name in CLI_TO_ENV.items():
        if was_option_provided(ctx, cli_key) and cli_values.get(cli_key) is not None:
            os.environ[env_name] = str(cli_values[cli_key])

    if was_option_provided(ctx, "request_timeout"):
        value = str(cli_values["request_timeout"])
        os.environ["REQUEST_TIMEOUT"] = value
        os.environ["JIRA_TIMEOUT"] = value
        os.environ["CONFLUENCE_TIMEOUT"] = value

    if was_option_provided(ctx, "read_only"):
        os.environ["READ_ONLY_MODE"] = str(cli_values["read_only"]).lower()

    if was_option_provided(ctx, "confluence_ssl_verify"):
        os.environ["CONFLUENCE_SSL_VERIFY"] = str(
            cli_values["confluence_ssl_verify"]
        ).lower()

    if was_option_provided(ctx, "jira_ssl_verify"):
        os.environ["JIRA_SSL_VERIFY"] = str(cli_values["jira_ssl_verify"]).lower()

    if was_option_provided(ctx, "insecure_skip_verify"):
        insecure = bool(cli_values["insecure_skip_verify"])
        os.environ["CONFLUENCE_SSL_VERIFY"] = str(not insecure).lower()
        os.environ["JIRA_SSL_VERIFY"] = str(not insecure).lower()
