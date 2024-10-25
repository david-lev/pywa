import json
import pathlib
from typing import TypeVar

from pywa import WhatsApp
from pywa_async import WhatsApp as WhatsAppAsync
from pywa.types.base_update import BaseUpdate

_T = TypeVar("_T", bound=BaseUpdate)


API_VERSIONS: list[float] = [18.0]

CLIENTS = {
    WhatsApp(phone_id="1234567890", token="xyzxyzxyz", filter_updates=False): {},
    WhatsAppAsync(phone_id="1234567890", token="xyzxyzxyz", filter_updates=False): {},
}

for client, updates in CLIENTS.items():
    for version in API_VERSIONS:
        updates[version] = {
            update_filename.replace(".json", ""): [
                {
                    test_name: client._handlers_to_update_constractor[
                        client._get_handler(update_obj)
                    ](client, update_obj)
                }  # noqa
                for test_name, update_obj in update_data.items()
            ]
            for update_filename, update_data in {
                pathlib.Path(update_filename).name: json.load(
                    open(update_filename, "r", encoding="utf-8")
                )
                for update_filename in pathlib.Path(
                    f"tests/data/updates/{version}"
                ).iterdir()
                if update_filename.name.endswith(".json")
            }.items()
        }
