import pytest


from pywa import WhatsApp

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
                "status": "APPROVED"
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
    assert result == mock_response

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