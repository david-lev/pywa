from pywa.utils import *  # noqa MUST BE IMPORTED FIRST
import httpx
from pywa.utils import _flow_request_media_decryptor


async def flow_request_media_decryptor(
    encrypted_media: dict[str, str | dict[str, str]],
    dl_session: httpx.AsyncClient | None = None,
) -> FlowRequestDecryptedMedia:
    """
    Decrypt the encrypted media file from the flow request.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components/media_upload#endpoint>`_.
    - Use the .decrypt_media() shorthand method of the :class:`FlowRequest` class instead.
    - This implementation requires ``cryptography`` to be installed. To install it, run ``pip3 install 'pywa[cryptography]'`` or ``pip3 install cryptography``.

    Example:

        >>> from pywa_async import WhatsApp, types
        >>> wa = WhatsApp(...)
        >>> @wa.on_flow_request("/media-upload")
        ... async def on_media_upload_request(_: WhatsApp, req: types.FlowRequest) -> types.FlowResponse | None:
        ...     dec = await req.decrypt_media(key="driver_license", index=0)
        ...     with open(dec.filename, "wb") as file:
        ...         file.write(dec.data)
        ...     return req.respond(...)

    Args:
        encrypted_media (dict): encrypted media data from the flow request (see example above).
        dl_session (httpx.AsyncClient): download session. Optional.

    Returns:
        tuple[str, str, bytes]
        - media_id (str): media ID
        - filename (str): media filename
        - decrypted_data (bytes): decrypted media file

    Raises:
        HTTPStatusError: If the request to the CDN URL fails.
        ValueError: If any of the hash verifications fail.
    """
    res = await (dl_session or httpx.AsyncClient()).get(encrypted_media["cdn_url"])
    res.raise_for_status()
    return FlowRequestDecryptedMedia(
        media_id=encrypted_media["media_id"],
        filename=encrypted_media["file_name"],
        data=_flow_request_media_decryptor(
            res.content, encrypted_media["encryption_metadata"]
        ),
    )
