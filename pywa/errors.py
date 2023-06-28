

class WhatsAppApiError(Exception):
    """
    Represents an error that happened while making a request to the WhatsApp Cloud API or incoming error from the webhook.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes

    Attributes:
        status_code: The status code (in case of response, else None).
        error_code: The error code.
        message: The error message.
        details: The error details (optional).
        fbtrace_id: The Facebook trace ID (optional).
        href: The href to the documentation (optional).
    """
    def __init__(
            self,
            status_code: int | None,
            error_code: int,
            message: str,
            details: str | None,
            fbtrace_id: str | None,
            href: str | None
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details
        self.fbtrace_id = fbtrace_id
        self.href = href

    @classmethod
    def from_response(
            cls,
            status_code: int,
            error: dict
    ) -> "WhatsAppApiError":
        """Create an error from a response."""
        return cls(
            status_code=status_code,
            error_code=error["code"],
            message=error["message"],
            details=error.get("error_data", {}).get("details", None),
            fbtrace_id=error.get("fbtrace_id"),
            href=error.get('href')
        )

    @classmethod
    def from_incoming_error(
            cls,
            error: dict
    ) -> "WhatsAppApiError":
        """Create an error from an incoming error."""
        return cls(
            status_code=None,
            error_code=error["code"],
            message=error["message"],
            details=error.get("error_data", {}).get("details", None),
            fbtrace_id=error.get("fbtrace_id"),
            href=error.get('href')
        )

    def __str__(self) -> str:
        return f"WhatsAppApiError(status_code={self.status_code}, message={self.message!r}, details={self.details!r})"

    def __repr__(self) -> str:
        return self.__str__()
