import logging
from typing import Any, Dict, List
from core.config import settings

logger = logging.getLogger(__name__)

class ComposioToolHub:
    def __init__(self):
        self.enabled = bool(settings.COMPOSIO_API_KEY)
        self.toolset = None
        if self.enabled:
            try:
                from composio_core import ComposioToolSet
                self.toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)
                logger.info("Composio ToolSet initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize ComposioToolSet: {e}")
                self.enabled = False

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Returns schemas for active Composio tools if configured."""
        if not self.enabled or not self.toolset:
            return []
        try:
            # Can expose standard Composio actions
            return []
        except Exception:
            return []

    async def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        if not self.enabled or not self.toolset:
            return {"error": "Composio is not enabled or API key is missing."}
        try:
            res = self.toolset.execute_action(action=action_name, params=params)
            return res
        except Exception as e:
            return {"error": str(e)}
