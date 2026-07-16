import httpx
from urllib.parse import urlencode
from app.core.config import settings
from app.services.oauth_provider import OAuthProvider

class GoogleOAuthProvider(OAuthProvider):
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self, scopes: str = "openid email profile") -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": scopes,
            "access_type": "offline",
            "prompt": "select_account",
            "include_granted_scopes": "true" # Enforce Google incremental authorization
        }
        return f"{self.auth_url}?{urlencode(params)}"

    async def fetch_user_info(self, code: str) -> dict:
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            # 1. Exchange authorization code for access token
            token_response = await client.post(self.token_url, data=data)
            if token_response.status_code != 200:
                raise Exception(f"Failed to fetch token from Google: {token_response.text}")
            
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            # Google returns the space-separated list of scopes approved by the user
            granted_scopes = tokens.get("scope", "")
            
            # 2. Fetch user profile using the access token
            headers = {"Authorization": f"Bearer {access_token}"}
            user_response = await client.get(self.user_info_url, headers=headers)
            if user_response.status_code != 200:
                raise Exception(f"Failed to fetch user info from Google: {user_response.text}")
                
            user_data = user_response.json()
            # Append the granted scopes to the profile info
            user_data["granted_scopes"] = granted_scopes
            return user_data
