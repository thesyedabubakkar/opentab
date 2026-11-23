from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseChannel(ABC):
    @abstractmethod
    async def start(self):
        """Starts the channel listener."""
        pass

    @abstractmethod
    async def stop(self):
        """Stops the channel listener."""
        pass

    @abstractmethod
    async def send_message(self, session_id: str, text: str, **kwargs):
        """Sends a message back to the user."""
        pass
