"""InvenioRDM client for creating records in target repository."""

from typing import Any, Dict, Optional

from inveniordm_py.client import InvenioAPI
from inveniordm_py.metadata import Metadata
from inveniordm_py.records.metadata import DraftMetadata
from requests import Session

from ..config import CONFIG
from ..errors import APIClientError, AuthenticationError
from ..interfaces import BaseAPIClient, RecordConsumerInterface
from ..resources.resources import (
    CommunitySubmissionResource,
    RequestActionsResource,
    SubmitReviewResource,
)
from ..utils.logger import logger


class InvenioRDMClient(BaseAPIClient, RecordConsumerInterface):
    """InvenioRDM client implementing consumer interface."""

    def __init__(self):
        super().__init__(
            base_url=CONFIG["TARGET_BASE_URL"], api_token=CONFIG["TARGET_API_TOKEN"]
        )
        self._setup_session()

    def _setup_session(self) -> None:
        """Setup the InvenioRDM client session."""
        session = Session()
        session.verify = CONFIG["SESSION"]["VERIFY_SSL"]

        if not self.api_token:
            raise AuthenticationError("TARGET_API_TOKEN is required")

        self.client = InvenioAPI(
            base_url=self.base_url,
            access_token=self.api_token,
            session=session,
        )
        self.records = self.client.records

    def make_request(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a request using the InvenioRDM client."""
        # This method is part of the interface but not used directly
        # since we use the inveniordm-py client
        raise NotImplementedError("Use specific methods for InvenioRDM operations")

    def create_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new draft record."""
        try:
            draft_resource = self.records.create(data=DraftMetadata(**record_data))
            logger.debug(f"Draft created with ID: {draft_resource.data._data['id']}")
            return draft_resource.data._data
        except Exception as e:
            logger.error(f"Draft creation failed: {e}")
            raise APIClientError(f"Failed to create record: {e}")

    def create_review_request(self, draft_id: str, community_id: str) -> Dict:
        """Create a community review request for a draft."""
        try:
            resource = CommunitySubmissionResource(self.client, id_=draft_id)
            data = Metadata(
                receiver={"community": community_id}, type="community-submission"
            )
            response = resource.create(data)
            logger.debug(
                f"Review request created: {response.data._data['links']['self']}"
            )
            return response.data._data
        except Exception as e:
            logger.error(f"Review request failed: {e}")
            raise APIClientError(f"Failed to create review request: {e}")

    def submit_review(self, draft_id: str, content: str) -> Dict:
        """Submit a draft for community review."""
        try:
            resource = SubmitReviewResource(self.client, id_=draft_id)
            data = Metadata(payload={"content": content, "format": "html"})
            response = resource.submit(data)
            logger.debug(
                f"Review submission created: {response.data._data['links']['self']}"
            )
            return response.data._data
        except Exception as e:
            logger.error(f"Review submission failed: {e}")
            raise APIClientError(f"Failed to submit review: {e}")

    def accept_request(self, request_id: str, content: str) -> Dict:
        """Accept a community submission request."""
        try:
            resource = RequestActionsResource(self.client, request_id=request_id)
            data = Metadata(payload={"content": content, "format": "html"})
            response = resource.accept(data)
            logger.debug(
                f"Request acceptance created: {response.data._data['links']['self']}"
            )
            return response.data._data
        except Exception as e:
            logger.error(f"Request acceptance failed: {e}")
            raise APIClientError(f"Failed to accept request: {e}")

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a record by ID."""
        try:
            record_resource = self.records.get(id_=record_id)
            return record_resource.data._data
        except Exception as e:
            logger.error(f"Failed to get record {record_id}: {e}")
            return None

    def validate_connection(self) -> bool:
        """Validate the connection to the InvenioRDM API."""
        try:
            # Try to fetch API information
            response = self.client.get(f"{self.base_url}/")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False
