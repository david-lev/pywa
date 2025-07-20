import json
import pathlib

from pywa import WhatsApp
from pywa_async import WhatsApp as WhatsAppAsync
from pywa.types.base_update import BaseUpdate


CLIENTS: dict[WhatsApp, dict[pathlib.Path, dict[str, BaseUpdate]]] = {
    WhatsApp(phone_id="1234567890", token="xyzxyzxyz", filter_updates=False): {},
    WhatsAppAsync(phone_id="1234567890", token="xyzxyzxyz", filter_updates=False): {},
}
# {client: {update_file: {update_name: BaseUpdate, ...}, ...}, ...}

update_dir = pathlib.Path("tests/data/updates/")
json_files = [f for f in update_dir.iterdir() if f.suffix == ".json"]

for client, update_files in CLIENTS.items():
    for file in json_files:
        with open(file, "r", encoding="utf-8") as f:
            update_name_to_raw_update = json.load(f)
        update_files[file] = {
            update_name: client._handlers_to_updates[
                client._get_handler_type(raw_update)
            ].from_update(client=client, update=raw_update)
            for update_name, raw_update in update_name_to_raw_update.items()
        }
