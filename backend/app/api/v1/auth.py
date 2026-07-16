from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.oauth_provider import OAuthProvider
from app.services.google_oauth import GoogleOAuthProvider

router = APIRouter()

# Dependency function to inject the OAuth provider
def get_oauth_provider() -> OAuthProvider:
    # Here we can switch to other OAuth providers easily if needed,
    # satisfying the Open/Closed Principle
    return GoogleOAuthProvider()

class CallbackRequest(BaseModel):
    code: str

@router.get("/login")
def get_login_url(provider: OAuthProvider = Depends(get_oauth_provider)):
    """
    Returns the URL to redirect the user to Google for OAuth authentication.
    """
    return {
        "url": provider.get_authorization_url()
    }

@router.post("/callback")
async def handle_callback(
    request_data: CallbackRequest,
    provider: OAuthProvider = Depends(get_oauth_provider)
):
    """
    Receives the OAuth code from the frontend, exchanges it for user profile information.
    """
    try:
        user_info = await provider.fetch_user_info(request_data.code)
        return {
            "status": "success",
            "user": {
                "id": user_info.get("id"),
                "email": user_info.get("email"),
                "verified_email": user_info.get("verified_email"),
                "name": user_info.get("name"),
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "picture": user_info.get("picture"),
                "locale": user_info.get("locale"),
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Authentication failed: {str(e)}"
        )
