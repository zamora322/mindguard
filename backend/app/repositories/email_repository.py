from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List

class EmailRepository(ABC):
    @abstractmethod
    async def save_emails(self, user_id: str, email_list: List[Dict[str, Any]]) -> int:
        """
        Inserts or updates parsed user emails into the database. Returns count of inserted records.
        """
        pass

    @abstractmethod
    async def upsert_sync_state(
        self,
        user_id: str,
        provider: str,
        status: str,
        last_message_id: Optional[str] = None,
        history_id: Optional[str] = None,
        synced_count: int = 0
    ) -> Dict[str, Any]:
        """
        Upserts the sync checkpoint state (status, last message ID, history ID, synced count).
        """
        pass

    @abstractmethod
    async def get_sync_state(self, user_id: str, provider: str = "google") -> Optional[Dict[str, Any]]:
        """
        Retrieves the sync state record for a given user and provider.
        """
        pass
