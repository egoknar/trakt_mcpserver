"""Authentication constants for the Trakt MCP server."""

import os
from typing import Final

# Authentication constants
AUTH_POLL_INTERVAL: Final[int] = 5  # seconds
AUTH_EXPIRATION: Final[int] = 600  # seconds (10 minutes)
AUTH_VERIFICATION_URL: Final[str] = "https://trakt.tv/activate"
# Must match a redirect URI registered on the Trakt app (new portal apps only allow https://).
OAUTH_REDIRECT_URI: Final[str] = os.getenv("TRAKT_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
