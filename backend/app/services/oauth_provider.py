from abc import ABC, abstractmethod

class OAuthProvider(ABC):
    @abstractmethod
    def get_authorization_url(self, scopes: str = "openid email profile") -> str:
        """
        Generates the authorization URL to redirect the user for authentication.
        Allows specifying dynamic scopes for various service levels (e.g. Gmail).
        """
        pass

    @abstractmethod
    async def fetch_user_info(self, code: str) -> dict:
        """
        Exchanges the authorization code for user info and returns profile details,
        including any granted scopes list inside a dedicated metadata field.
        """
        pass
