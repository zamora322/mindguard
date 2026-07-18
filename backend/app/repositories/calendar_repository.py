from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List

class CalendarRepository(ABC):
    @abstractmethod
    async def save_calendar_events(self, user_id: str, events_list: List[Dict[str, Any]]) -> int:
        """
        Inserts or updates fetched calendar events into the database. Returns count of saved records.
        """
        pass
