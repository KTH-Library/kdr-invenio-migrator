from typing import Any, Dict, Optional

from inveniordm_py.client import InvenioAPI
from inveniordm_py.records.metadata import DraftMetadata
from requests import Session

from ..config import CONFIG
from ..utils.logger import logger


class TargetClient:
    """Client for interacting with InvenioRDM instance using inveniordm-py."""

    def __init__(self):
        session = Session()
        session.verify = False  # Only for testing!
        self.client = InvenioAPI(
            base_url=CONFIG["TARGET_BASE_URL"],
            access_token=CONFIG["TARGET_API_TOKEN"],
            session=session,
        )
        self.records = self.client.records  # Access RecordList resource

    def create_draft(self, record_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new draft record using proper inveniordm-py workflow."""
        try:
            # Use RecordList.create() with DraftMetadata as per client design
            draft_resource = self.records.create(data=DraftMetadata(**record_data))
            logger.info(f"Created draft ID: {draft_resource._data['id']}")
            return draft_resource
        except Exception as e:
            logger.error(f"Bad Draft: {str(draft_resource)}")
            logger.error(f"Draft creation failed: {str(e)}")
            raise
