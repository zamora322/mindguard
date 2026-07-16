from abc import ABC, abstractmethod

class OAuthProvider(ABC):
    @abstractmethod
    def get_authorization_url(self) -> str:
        """
        Generates the authorization URL to redirect the user for authentication.
        """
        pass

    @abstractmethod
    async def fetch_user_info(self, code: str) -> dict:
        """
        Exchanges the authorization code for user info.
        """
        pass
