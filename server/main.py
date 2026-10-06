"""Main server module for the Trakt MCP server."""

import logging
import os
import sys
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Final

from mcp.server.fastmcp import FastMCP

from client.pool import shutdown_clients

# Import all module registration functions
from .auth import register_auth_resources, register_auth_tools
from .checkin import register_checkin_tools
from .comments import register_comment_tools
from .episodes import register_episode_tools
from .movies import register_movie_resources, register_movie_tools
from .people import register_people_tools
from .progress import register_progress_tools
from .prompts.basic import register_basic_prompts
from .recommendations import register_recommendation_tools
from .search import register_search_tools
from .seasons import register_season_tools
from .shows import register_show_resources, register_show_tools
from .sync import register_sync_tools
from .user import register_user_resources, register_user_tools

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("trakt_mcp")

REGISTRATIONS: Final[tuple[Callable[[FastMCP], object], ...]] = (
    register_auth_resources,
    register_auth_tools,
    register_show_resources,
    register_show_tools,
    register_movie_resources,
    register_movie_tools,
    register_comment_tools,
    register_user_resources,
    register_user_tools,
    register_search_tools,
    register_checkin_tools,
    register_sync_tools,
    register_progress_tools,
    register_recommendation_tools,
    register_season_tools,
    register_episode_tools,
    register_people_tools,
    register_basic_prompts,
)

# Tools that change data on the Trakt account. Dropped unless TRAKT_READ_ONLY is turned off.
WRITE_TOOLS: Final[tuple[str, ...]] = (
    "add_to_history",
    "remove_from_history",
    "add_user_ratings",
    "remove_user_ratings",
    "add_user_watchlist",
    "remove_user_watchlist",
    "checkin_to_show",
    "remove_playback_item",
    "hide_movie_recommendation",
    "hide_show_recommendation",
    "unhide_movie_recommendation",
    "unhide_show_recommendation",
)


def _read_only() -> bool:
    return os.getenv("TRAKT_READ_ONLY", "1").strip().lower() not in ("0", "false", "no", "off")


@asynccontextmanager
async def _lifespan(_mcp: FastMCP) -> AsyncGenerator[None]:
    """Close pooled HTTP clients when the server stops."""
    try:
        yield
    finally:
        await shutdown_clients()


def create_server() -> FastMCP:
    """Create and configure the Trakt MCP server with all modules.

    Returns:
        Configured FastMCP server instance
    """
    try:
        version = _pkg_version("trakt-mcp")
    except PackageNotFoundError:
        version = "0.0.0+dev"
    logger.info("Starting trakt-mcp v%s", version)
    # Host/port only matter for the HTTP transports (MCP_TRANSPORT); the host must be set
    # here because FastMCP derives its DNS-rebinding protection from it at construction.
    mcp = FastMCP(
        name="trakt-mcp",
        lifespan=_lifespan,
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_PORT", "8000")),
    )
    for register in REGISTRATIONS:
        register(mcp)
    if _read_only():
        for name in WRITE_TOOLS:
            mcp.remove_tool(name)
        logger.info("Read-only mode: %d write tools disabled", len(WRITE_TOOLS))
    logger.info("All Trakt MCP modules registered successfully")
    return mcp


# Create the server instance
mcp = create_server()


def run() -> None:
    """Console-script entry point (used by `[project.scripts]` and uvx)."""
    # Print to stderr to avoid polluting stdout (required for stdio transport)
    print("Starting Trakt MCP server...", file=sys.stderr)
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport not in ("stdio", "sse", "streamable-http"):
        raise SystemExit(f"Unsupported MCP_TRANSPORT: {transport}")
    mcp.run(transport=transport)


if __name__ == "__main__":
    run()
