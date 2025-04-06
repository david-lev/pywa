import pytest
from unittest.mock import MagicMock

from pywa import WhatsApp, types

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


def test_get_templates(api, wa, mocker):
    # Mock the parse_template_data helper function
    mock_parsed_template = {
        "id": "594425479261596",
        "name": "example_template",
        "language": "en_US",
        "status": "APPROVED",
        "category": types.NewTemplate.Category.MARKETING,
        "parameter_format": "POSITIONAL",
        "components": [
            types.NewTemplate.Body(text="Welcome and congratulations!!")
        ]
    }
    mock_parse = mocker.patch("pywa._helpers.parse_template_data", return_value=mock_parsed_template)

    # Mock response data
    mock_response = {
        "data": [
            {
                "id": "594425479261596",
                "category": "MARKETING",
                "components": [
                    {
                        "type": "BODY",
                        "text": "Welcome and congratulations!!"
                    }
                ],
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

    template = result[0]
    assert template["id"] == "594425479261596"
    assert template["name"] == "example_template"
    assert template["language"] == "en_US"
    assert template["status"] == "APPROVED"
    assert template["category"] == types.NewTemplate.Category.MARKETING
    assert isinstance(template["components"][0], types.NewTemplate.Body)
    assert template["components"][0].text == "Welcome and congratulations!!"

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

    # Verify the helper function was called
    mock_parse.assert_called_once_with(mock_response["data"][0])


def test_parse_template_data():
    from pywa import _helpers as helpers
    from pywa import types

    # Test data
    template_data = {
        "id": "594425479261596",
        "name": "example_template",
        "language": "en_US",
        "status": "APPROVED",
        "category": "MARKETING",
        "parameter_format": "POSITIONAL",
        "components": [
            {
                "type": "HEADER",
                "format": "TEXT",
                "text": "Hello World"
            },
            {
                "type": "BODY",
                "text": "Welcome and congratulations!!"
            },
            {
                "type": "FOOTER",
                "text": "WhatsApp Business Platform sample message"
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {
                        "type": "URL",
                        "text": "Visit Website",
                        "url": "https://example.com"
                    }
                ]
            }
        ]
    }

    # Parse the template
    result = helpers.parse_template_data(template_data)

    # Verify the result
    assert result["id"] == "594425479261596"
    assert result["name"] == "example_template"
    assert result["language"] == "en_US"
    assert result["status"] == "APPROVED"
    assert result["category"] == types.NewTemplate.Category.MARKETING
    assert result["parameter_format"] == "POSITIONAL"

    # Verify components
    components = result["components"]
    assert len(components) == 4

    # Header
    assert isinstance(components[0], types.NewTemplate.Text)
    assert components[0].text == "Hello World"

    # Body
    assert isinstance(components[1], types.NewTemplate.Body)
    assert components[1].text == "Welcome and congratulations!!"

    # Footer
    assert isinstance(components[2], types.NewTemplate.Footer)
    assert components[2].text == "WhatsApp Business Platform sample message"

    # Buttons
    buttons_component = components[3]
    assert buttons_component["type"] == "BUTTONS"
    assert len(buttons_component["buttons"]) == 1

    button = buttons_component["buttons"][0]
    assert isinstance(button, types.NewTemplate.UrlButton)
    assert button.title == "Visit Website"
    assert button.url == "https://example.com"

    # Test error handling for unknown category
    template_with_bad_category = {
        "category": "UNKNOWN_CATEGORY",
        "components": []
    }
    with pytest.raises(ValueError, match="Unknown template category"):
        helpers.parse_template_data(template_with_bad_category)