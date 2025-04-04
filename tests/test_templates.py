import pytest
from unittest.mock import MagicMock

from pywa import WhatsApp
from pywa.types.template import RetrievedTemplate

PHONE_ID = "123456789"
TOKEN = "xyz"
WABA_ID = "987654321"


@pytest.fixture
def api(mocker):
    # Use the correct attribute name
    return mocker.patch("pywa.api.WhatsAppCloudApi.get_templates")


@pytest.fixture
def wa():
    return WhatsApp(phone_id=PHONE_ID, token=TOKEN, business_account_id=WABA_ID)


def test_get_templates(api, wa):
    # Mock response data
    mock_response = {
        "data": [
            {
                "id": "594425479261596",
                "category": "MARKETING",
                "components": [],
                "language": "en_US",
                "name": "example_template",
                "status": "APPROVED",
                "parameter_format": "POSITIONAL"
            }
        ],
        "paging": {
            "cursors": {
                "before": "xyz",
                "after": "abc"
            }
        }
    }

    # Set up the mock response
    api.return_value = mock_response

    # Test the get_templates method
    result = wa.get_templates(
        system_user_token="test_token",
        category="MARKETING"
    )

    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], RetrievedTemplate)

    # Check template fields
    template = result[0]
    assert template.id == "594425479261596"
    assert template.name == "example_template"
    assert template.language == "en_US"
    assert template.status == "APPROVED"
    assert template.category == "MARKETING"
    assert template.parameter_format == "POSITIONAL"
    assert template.components == []

    # Verify the API was called with correct parameters
    api.assert_called_once_with(
        waba_id=WABA_ID,
        system_user_token="test_token",
        category="MARKETING",
        content=None,
        language=None,
        name=None,
        name_or_content=None,
        quality_score=None,
        status=None,
        limit=None,
    )