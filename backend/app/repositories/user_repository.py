from abc import ABC, abstractmethod
from typing import Optional, Any, Dict

class UserRepository(ABC):
    @abstractmethod
    async def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a user from the database by their Google ID.
        """
        pass

    @abstractmethod
    async def create_user(
        self,
        google_id: str,
        email: str,
        name: str,
        picture: Optional[str]
    ) -> Dict[str, Any]:
        """
        Creates a new user record in the database.
        """
        pass

    @abstractmethod
    async def update_user(
        self,
        google_id: str,
        name: str,
        picture: Optional[str]
    ) -> Dict[str, Any]:
        """
        Updates the profile (name and avatar) of an existing user.
        """
        pass

    @abstractmethod
    async def save_integration(
        self,
        user_id: str,
        provider: str,
        status: str,
        scopes: str
    ) -> Dict[str, Any]:
        """
        Saves or updates a user integration provider record and its authorized scopes.
        """
        pass

    @abstractmethod
    async def get_integrations(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves active integrations and scopes for a given user.
        """
        pass
