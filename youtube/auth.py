"""
BEYOND UNKNOWN - YouTube OAuth Authentication
Manages OAuth2 token refresh and builds authenticated YouTube Data API v3 service.
Includes helper to initiate desktop authentication flow for obtaining initial refresh token.
"""

import logging
from typing import Optional
from config import settings

logger = logging.getLogger("beyond_unknown.youtube.auth")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

class YouTubeAuth:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        self.client_id = client_id or settings.YOUTUBE_CLIENT_ID
        self.client_secret = client_secret or settings.YOUTUBE_CLIENT_SECRET
        self.refresh_token = refresh_token or settings.YOUTUBE_REFRESH_TOKEN

    def is_configured(self) -> bool:
        """Verifies if all 3 required OAuth environment variables are present."""
        return bool(
            self.client_id and len(self.client_id) > 10 and
            self.client_secret and len(self.client_secret) > 5 and
            self.refresh_token and len(self.refresh_token) > 10
        )

    def get_authenticated_service(self):
        """
        Creates an authorized YouTube Data API v3 service client using refresh token.
        """
        if not self.is_configured():
            logger.warning("YouTube OAuth credentials not fully configured in environment.")
            return None

        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        try:
            creds = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )

            # Force token refresh to verify credentials validity
            creds.refresh(Request())
            logger.info("Successfully refreshed YouTube OAuth access token.")

            service = build("youtube", "v3", credentials=creds)
            return service

        except Exception as e:
            logger.error(f"Failed to authenticate with YouTube Data API: {e}")
            raise RuntimeError(f"YouTube authentication error: {e}")

    @staticmethod
    def run_local_oauth_flow(client_secrets_json_path: str):
        """
        Helper method to run a one-time desktop browser OAuth flow
        and print the YOUTUBE_REFRESH_TOKEN for copying to .env or GitHub Secrets.
        """
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_json_path,
            scopes=SCOPES
        )
        creds = flow.run_local_server(port=8080)
        print("\n=======================================================")
        print("YOUTUBE OAUTH REFRESH TOKEN GENERATED SUCCESSFULLY:")
        print(f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}")
        print("=======================================================\n")
        return creds.refresh_token
