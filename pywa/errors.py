
class WhatsAppError(Exception):
    def __init__(
        self,
        status_code: int,
        error: dict
    ) -> None:
        self.status_code = status_code
        self.error_code = error["code"]
        self.message = error["message"]
        self.details = error["error_data"]["details"]
        self.fbtrace_id = error["fbtrace_id"]

    def __str__(self) -> str:
        return f"WhatsAppError(status_code={self.status_code}, error_code={self.error_code}, details={self.details})"
