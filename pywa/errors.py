class WhatsAppError(Exception):
    """
    Represents an error that sent by the WhatsApp Cloud API.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes

    Attributes:
        error_code (int): The error code.
        title (str): The error title.
        message (str): The error message.
        details (str): The error details.
    """
    def __init__(self, error: dict) -> None:
        self.error_code = error["code"]
        self.title = error["title"]
        self.message = error["message"]
        self.details = error["error_data"]["details"]

    def __str__(self) -> str:
        return f"WhatsAppError(error_code={self.error_code}, details={self.details})"


class WhatsAppApiError(WhatsAppError):
    """
    Represents an error that happened while making a request to the WhatsApp Cloud API.

    - See more: https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes

    Attributes:
        status_code (int): The status code of the response.
        error_code (int): The error code.
        message (str): The error message.
        details (str): The error details (optional).
        fbtrace_id (str): The Facebook trace ID.
    """
    def __init__(
            self,
            status_code: int,
            error: dict
    ) -> None:
        self.status_code = status_code
        self.error_code = error["code"]
        self.message = error["message"]
        self.details = error.get("error_data", {}).get("details", None)
        self.fbtrace_id = error["fbtrace_id"]

    def __str__(self) -> str:
        return f"WhatsAppApiError(status_code={self.status_code}, message={self.message!r}, details={self.details!r})"
