import json
import pathlib
from typing import TypeVar

from pywa import WhatsApp
from pywa.types.base_update import BaseUpdate

_T = TypeVar("_T", bound=BaseUpdate)


API_VERSIONS: list[float] = [18.0]

WA_NO_FILTERS = WhatsApp(phone_id="1234567890", token="xyzxyzxyz", filter_updates=False)

# noinspection PyCallingNonCallable,PyProtectedMember
UPDATES: dict[
    float, dict[str, list[dict[str, _T]]]
] = {  # {version: {file_name: [{test_name: update}]}}
    version: {
        update_filename.replace(".json", ""): [
            {
                test_name: WA_NO_FILTERS._handlers_to_update_constractor[
                    WA_NO_FILTERS._get_handler(update_obj)
                ](WA_NO_FILTERS, update_obj)
            }  # noqa
            for test_name, update_obj in update_data.items()
        ]
        for update_filename, update_data in {
            pathlib.Path(update_filename).name: json.load(open(update_filename, "r"))
            for update_filename in pathlib.Path(
                f"tests/data/updates/{version}"
            ).iterdir()
            if update_filename.name.endswith(".json")
        }.items()
    }
    for version in API_VERSIONS
}
