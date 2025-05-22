from typing import Any, Dict, Optional

from inveniordm_py.client import InvenioAPI
from inveniordm_py.metadata import Metadata
from inveniordm_py.records.metadata import DraftMetadata
from inveniordm_py.resources import Resource
from requests import Session

from ..config import CONFIG
from ..utils.logger import logger


class CommunitySubmissionResource(Resource):
    """Handles community submission review requests for drafts."""

    endpoint = "/records/{id_}/draft/review"

    def create(self, data: Metadata) -> Any:
        """Create a community submission review request."""
        return self._put(Metadata, data=data)


class SubmitReviewResource(Resource):
    """Handles submission of reviews for community requests."""

    endpoint = "/records/{id_}/draft/actions/submit-review"

    def submit(self, data: Metadata) -> Any:
        """Submit a review for community approval."""
        return self._post(Metadata, data=data)


class RequestActionsResource(Resource):
    """Handles actions on community requests."""

    endpoint = "/requests/{request_id}/actions/accept"

    def accept(self, data: Metadata) -> Any:
        """Accept a community submission request."""
        return self._post(Metadata, data=data)


class TargetClient:
    """Extended client with community support for InvenioRDM instance."""

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
        """Create a new draft record."""
        try:
            draft_resource = self.records.create(data=DraftMetadata(**record_data))
            return draft_resource
        except Exception as e:
            logger.error(f"Draft creation failed: {e.response.json()}")
            raise

    def create_review_request(self, draft_id: str, community_id: str) -> Dict:
        """Create a community review request for a draft."""
        try:
            resource = CommunitySubmissionResource(self.client, id_=draft_id)
            data = Metadata(
                receiver={"community": community_id}, type="community-submission"
            )
            response = resource.create(data)
            return response.data
        except Exception as e:
            logger.error(f"Review request failed: {e.response.json()}")
            raise

    def submit_review(self, draft_id: str, content: str) -> Dict:
        """Submit a draft for community review."""
        try:
            resource = SubmitReviewResource(self.client, id_=draft_id)
            data = Metadata(payload={"content": content, "format": "html"})
            response = resource.submit(data)
            return response.data
        except Exception as e:
            logger.error(f"Review submission failed: {e.response.json()}")
            raise

    def accept_request(self, request_id: str, content: str) -> Dict:
        """Accept a community submission request."""
        try:
            resource = RequestActionsResource(self.client, request_id=request_id)
            data = Metadata(payload={"content": content, "format": "html"})
            response = resource.accept(data)
            return response.data
        except Exception as e:
            logger.error(f"Request acceptance failed: {e.response.json()}")
            raise
