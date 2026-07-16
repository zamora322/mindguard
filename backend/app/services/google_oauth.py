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

    def get_authorization_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account"
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
            
            # 2. Fetch user profile using the access token
            headers = {"Authorization": f"Bearer {access_token}"}
            user_response = await client.get(self.user_info_url, headers=headers)
            if user_response.status_code != 200:
                raise Exception(f"Failed to fetch user info from Google: {user_response.text}")
                
            return user_response.json()
