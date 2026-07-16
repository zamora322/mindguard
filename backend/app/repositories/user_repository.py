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
