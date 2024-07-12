import tempfile

import pytest
import pytest_mock

from pywa import WhatsApp, types

PHONE_ID = "123456789"
TOKEN = "xyz"
WABA_ID = "987654321"
MSG_ID = "wamid.xx=="
MEDIA_ID = "mediaid.xx=="
SENT_MESSAGE = {
    "messaging_product": "whatsapp",
    "contacts": [{"input": "1234567890", "wa_id": "1234567890"}],
    "messages": [{"id": MSG_ID}],
}

wa = WhatsApp(phone_id=PHONE_ID, token=TOKEN)


def test_wa_without_token():
    with pytest.raises(ValueError):
        WhatsApp(phone_id="123", token="")


def test_warning_when_version_lower_than_min():
    with pytest.warns(RuntimeWarning):
        WhatsApp(phone_id="123", token="123", api_version="16.0")


def test_send_text_message(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    assert (
        wa.send_message(
            to="1234567890",
            text="Hello World",
        )
        == MSG_ID
    )


def test_send_message_with_buttons(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    assert (
        wa.send_message(
            to="1234567890",
            text="Hello World",
            buttons=[types.Button(title="Button 1", callback_data="button1")],
        )
        == MSG_ID
    )

    assert (
        wa.send_message(
            to="1234567890",
            text="Hello World",
            buttons=types.ButtonUrl(
                title="PyWa Docs", url="https://pywa.readthedocs.io"
            ),
        )
        == MSG_ID
    )

    assert (
        wa.send_message(
            to="1234567890",
            text="Hello World",
            buttons=types.SectionList(
                button_title="Menu",
                sections=[
                    types.Section(
                        title="Section 1",
                        rows=[
                            types.SectionRow(
                                title="Row 1",
                                description="Description 1",
                                callback_data="row1",
                            )
                        ],
                    )
                ],
            ),
        )
        == MSG_ID
    )


def test_send_message_deprecated_keyboard_param(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    with pytest.warns(DeprecationWarning):
        assert (
            wa.send_message(
                to="1234567890",
                text="Hello World",
                keyboard=[types.Button(title="Button 1", callback_data="button1")],
            )
            == MSG_ID
        )


def test_send_media_message(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    mocker.patch.object(wa.api, "upload_media", return_value={"id": MEDIA_ID})
    assert (
        wa.send_image(
            to="1234567890",
            image="https://example.com/image.jpg",  # url
            caption="Hello World",
        )
        == MSG_ID
    )

    assert (
        wa.send_video(
            to="1234567890",
            video="1234567890",  # media_id
            caption="Hello World",
        )
        == MSG_ID
    )

    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        assert (
            wa.send_video(
                to="1234567890",
                video=f.name,  # local file
                caption="Hello World",
            )
            == MSG_ID
        )

    with pytest.raises(ValueError):
        wa.send_video(
            to="1234567890",
            video="invalid/path.mp4",  # invalid path
            caption="Hello World",
        )


def test_send_media_deprecated_body_param(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    with pytest.warns(DeprecationWarning):
        wa.send_image(
            to="1234567890",
            image="https://example.com/image.jpg",  # url
            caption="Hello World",
            body="Hello World",
        )

    with pytest.warns(DeprecationWarning):
        wa.send_video(
            to="1234567890",
            video="1234567890",  # media_id
            caption="Hello World",
            body="Hello World",
        )

    with pytest.warns(DeprecationWarning):
        wa.send_document(
            to="1234567890",
            document="1234567890",  # media_id
            caption="Hello World",
            body="Hello World",
        )


def test_sending_interactive_media_without_caption():
    with pytest.raises(ValueError):
        wa.send_image(
            to="1234567890",
            image="https://example.com/image.jpg",
            buttons=[types.Button(title="Button 1", callback_data="button1")],
        )


def test_send_reaction(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    assert (
        wa.send_reaction(to="1234567890", message_id="wamid.xx==", emoji="😊") == MSG_ID
    )
    assert wa.remove_reaction(to="1234567890", message_id="wamid.xx==") == MSG_ID


def test_send_location(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    assert (
        wa.send_location(
            to="1234567890",
            latitude=37.4847483695049,
            longitude=-122.1473373086664,
            name="WhatsApp HQ",
            address="Menlo Park, 1601 Willow Rd, United States",
        )
        == MSG_ID
    )


def test_request_location(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    assert (
        wa.request_location(
            to="1234567890",
            text="Please share your location",
        )
        == MSG_ID
    )


def test_send_contact(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    assert (
        wa.send_contact(
            to="1234567890",
            contact=types.Contact(
                name=types.Contact.Name(formatted_name="John Doe", first_name="John"),
                phones=[types.Contact.Phone(phone="1234567890", type="WORK")],
                emails=[types.Contact.Email(email="john@doe.com", type="WORK")],
                urls=[types.Contact.Url(url="https://example.com", type="WORK")],
            ),
        )
        == MSG_ID
    )


def test_send_catalog(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    assert (
        wa.send_catalog(
            to="1234567890",
            body="Hello World",
            footer="Footer",
            thumbnail_product_sku="SKU123",
        )
        == MSG_ID
    )


def test_send_product(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    assert (
        wa.send_product(
            to="1234567890",
            body="Hello World",
            footer="Footer",
            catalog_id="1234567890",
            sku="SKU123",
        )
        == MSG_ID
    )


def test_send_products(mocker: pytest_mock.MockFixture):
    mocker.patch.object(wa.api, "send_message", return_value=SENT_MESSAGE)
    assert (
        wa.send_products(
            to="1234567890",
            body="Hello World",
            footer="Footer",
            catalog_id="1234567890",
            title="Products",
            product_sections=[
                types.ProductsSection(
                    title="Section 1",
                    skus=["SKU123", "SKU456"],
                )
            ],
        )
        == MSG_ID
    )


def test_mark_message_as_read(mocker: pytest_mock.MockFixture):
    mocker.patch.object(
        wa.api,
        "mark_message_as_read",
        return_value={
            "success": True,
        },
    )
    assert wa.mark_message_as_read(message_id="wamid.xx==")
