import pytest

from pywa import errors


exceptions: dict[type[errors.WhatsAppError], dict] = {
    errors.MediaUploadError: {
        "code": 131053,
        "title": "Media upload error",
        "message": "Media upload error",
        "error_data": {
            "details": "Downloading media from weblink failed with http code 429, status message Too Many Requests"
        },
    },
    errors.ExpiredAccessToken: {
        "message": "Error validating access token: Session has expired on Friday, 26-Apr-24 06:00:00 PDT. The current time is Sunday, 28-Apr-24 03:40:10 PDT.",
        "type": "OAuthException",
        "code": 190,
        "error_subcode": 463,
        "fbtrace_id": "ACEyrTehk6IAd0lm05Ixogh",
    },
    errors.ReEngagementMessage: {
        "code": 131047,
        "title": "Re-engagement message",
        "message": "Re-engagement message",
        "error_data": {
            "details": "Message failed to send because more than 24 hours have passed since the customer last replied to this number."
        },
        "href": "https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes/",
    },
}


def test_error_codes_uniqueness():
    all_error_codes = [
        tuple(e.__error_codes__) for e in errors.WhatsAppError._all_exceptions()
    ]
    assert len(all_error_codes) == len(set(all_error_codes))


def test_error_codes():
    for exc_typ, data in exceptions.items():
        exc = exc_typ.from_dict(data)
        try:
            assert isinstance(exc, exc_typ)
            assert exc.error_code == data["code"]
            assert exc.error_subcode == data.get("error_subcode")
            assert exc.type == data.get("type")
            assert exc.message == data["message"]
            assert exc.details == data.get("error_data", {}).get("details")
            assert exc.fbtrace_id == data.get("fbtrace_id")
            assert exc.href == data.get("href")
        except AssertionError:
            raise AssertionError(f"Failed to assert exc={exc!r}, data={data!r}")
