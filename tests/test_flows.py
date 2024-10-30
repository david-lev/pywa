import dataclasses
import importlib
import json
import pathlib

import pytest

from pywa import WhatsApp, handlers, utils, filters
from pywa.types.flows import (
    FlowJSON,
    Screen,
    Layout,
    Form,
    TextInput,
    InputType,
    Action,
    FlowActionType,
    DataSource,
    ScreenDataRef,
    ComponentRef,
    ScreenData,
    FlowResponse,
    FlowRequest,
    FlowRequestActionType,
    _FlowJSONEncoder,
    Ref,
)
from pywa.utils import Version


def test_flows_to_json():
    for version in pathlib.Path("tests/data/flows").iterdir():
        if version.is_dir():
            with open(
                pathlib.Path(version, "examples.json"), "r", encoding="utf-8"
            ) as f:
                json_examples = json.load(f)
                obj_examples = importlib.import_module(
                    f"tests.data.flows.{version.name}.examples"
                )
                for flow_name, flow_json in json_examples.items():
                    obj_dict = json.loads(getattr(obj_examples, flow_name).to_json())
                    example_dict = json_examples[flow_name]
                    assert obj_dict["version"] == version.name.replace(
                        "_", "."
                    ) and example_dict["version"] == version.name.replace("_", ".")
                    try:
                        assert obj_dict == example_dict
                    except AssertionError:
                        raise AssertionError(
                            f"Flow {version.name=} {flow_name=} does not match example\nFlow: {obj_dict}\nJSON: {example_dict}"
                        )


def test_min_version():
    with pytest.raises(ValueError):
        FlowJSON(version="1.0", screens=[])


def test_empty_form():
    with pytest.raises(ValueError):
        Form(name="form", children=[])


def test_action():
    with pytest.raises(ValueError):
        Action(name=FlowActionType.NAVIGATE)

    with pytest.raises(ValueError):
        Action(name=FlowActionType.COMPLETE)


def test_component_ref():
    assert ComponentRef("test").to_str() == "${form.test}"
    assert ComponentRef("test", screen="START").to_str() == "${screen.START.form.test}"
    assert TextInput(name="test", label="Test").ref.to_str() == "${form.test}"
    assert (
        TextInput(name="test", label="Test").ref_in(screen="START").to_str()
        == "${screen.START.form.test}"
    )


def test_screen_data_key():
    assert ScreenDataRef("test").to_str() == "${data.test}"
    assert ScreenDataRef("test", screen="START").to_str() == "${screen.START.data.test}"
    assert ScreenData(key="test", example="Example").ref.to_str() == "${data.test}"
    assert (
        ScreenData(key="test", example="Example").ref_in(screen="START").to_str()
        == "${screen.START.data.test}"
    )


def test_ref_to_str_without_screen():
    ref = Ref(prefix="data", field="age")
    assert ref.to_str() == "${data.age}"


def test_ref_to_str_with_screen_id():
    ref = Ref(prefix="data", field="age", screen="START")
    assert ref.to_str() == "${screen.START.data.age}"


def test_ref_to_str_with_screen():
    screen = Screen(id="START", layout=Layout(children=[]))
    ref = Ref(prefix="data", field="age", screen=screen)
    assert ref.to_str() == "${screen.START.data.age}"


def test_ref_equality():
    ref = Ref(prefix="data", field="age")
    condition = ref == 21
    assert condition.to_str() == "(${data.age} == 21)"


def test_ref_inequality():
    ref = Ref(prefix="data", field="age")
    condition = ref != 18
    assert condition.to_str() == "(${data.age} != 18)"


def test_ref_greater_than():
    ref = Ref(prefix="data", field="age")
    condition = ref > 21
    assert condition.to_str() == "(${data.age} > 21)"


def test_ref_greater_than_or_equal():
    ref = Ref(prefix="data", field="age")
    condition = ref >= 21
    assert condition.to_str() == "(${data.age} >= 21)"


def test_ref_less_than():
    ref = Ref(prefix="data", field="age")
    condition = ref < 21
    assert condition.to_str() == "(${data.age} < 21)"


def test_ref_less_than_or_equal():
    ref = Ref(prefix="data", field="age")
    condition = ref <= 21
    assert condition.to_str() == "(${data.age} <= 21)"


def test_logical_and_with_ref():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition = ref1 & ref2
    assert condition.to_str() == "(${data.age} && ${form.is_verified})"


def test_logical_or_with_ref():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition = ref1 | ref2
    assert condition.to_str() == "(${data.age} || ${form.is_verified})"


def test_logical_and_with_condition():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition1 = ref1 > 21
    condition2 = ref2 == True  # noqa: E712
    combined_condition = condition1 & condition2
    assert (
        combined_condition.to_str()
        == "((${data.age} > 21) && (${form.is_verified} == true))"
    )


def test_logical_or_with_condition():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition1 = ref1 < 18
    condition2 = ref2 == False  # noqa:  E712
    combined_condition = condition1 | condition2
    assert (
        combined_condition.to_str()
        == "((${data.age} < 18) || (${form.is_verified} == false))"
    )


def test_invert_condition():
    ref = Ref(prefix="data", field="age")
    condition = ~ref
    assert condition.to_str() == "!${data.age}"


def test_combined_conditions_with_invert():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition = ~(ref1 > 18) & (ref2 == True)  # noqa: E712
    assert (
        condition.to_str() == "(!(${data.age} > 18) && (${form.is_verified} == true))"
    )


def test_combined_conditions_with_literal_before():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition = ref2 & (ref1 > 18)
    assert condition.to_str() == "(${form.is_verified} && (${data.age} > 18))"


def test_combined_conditions_with_literal_after():
    ref1 = Ref(prefix="form", field="is_verified")
    ref2 = Ref(prefix="data", field="age")
    condition = (ref2 > 18) & ref1
    assert condition.to_str() == "((${data.age} > 18) && ${form.is_verified})"


def test_init_values():
    text_entry = TextInput(name="test", label="Test", init_value="Example")
    form = Form(name="form", children=[text_entry])
    assert form.init_values == {"test": "Example"}

    # check for duplicate init_values (in the form level and in the children level)
    with pytest.raises(ValueError):
        TextInput(
            name="test", label="Test", init_value="Example", input_type=InputType.NUMBER
        )
        Form(name="form", init_values={"test": "Example"}, children=[text_entry])

    # test that if form has init_values referred to a ref,
    # the init_values does not fill up from the .children init_value's
    form_with_init_values_as_data_key = Screen(
        id="test",
        title="Test",
        data=[
            init_vals := ScreenData(key="init_vals", example={"test": "Example"}),
        ],
        layout=Layout(
            children=[
                Form(name="form", init_values=init_vals.ref, children=[text_entry])
            ]
        ),
    )
    assert isinstance(
        form_with_init_values_as_data_key.layout.children[0].init_values, Ref
    )


#
#
def test_error_messages():
    text_entry = TextInput(name="test", label="Test", error_message="Example")
    form = Form(name="form", children=[text_entry])
    assert form.error_messages == {"test": "Example"}

    # check for duplicate error_messages (in the form level and in the children level)
    with pytest.raises(ValueError):
        TextInput(name="test", label="Test", error_message="Example")
        Form(name="form", error_messages={"test": "Example"}, children=[text_entry])

    # test that if form has error_messages referred to a ref,
    # the error_messages does not fill up from the .children error_message's
    form_with_error_messages_as_data_key = Screen(
        id="test",
        title="Test",
        data=[
            error_msgs := ScreenData(key="error_msgs", example={"test": "Example"}),
        ],
        layout=Layout(
            children=[
                Form(
                    name="form",
                    error_messages=error_msgs.ref,
                    children=[text_entry],
                )
            ]
        ),
    )

    assert isinstance(
        form_with_error_messages_as_data_key.layout.children[0].error_messages, Ref
    )


def test_encoder_py_to_json_types():
    encoder = _FlowJSONEncoder()
    assert encoder._get_json_type("Example") == {"type": "string"}
    assert encoder._get_json_type(example=1) == {"type": "number"}
    assert encoder._get_json_type(1.0) == {"type": "number"}
    assert encoder._get_json_type(True) == {"type": "boolean"}


def test_encoder_single_data_source():
    encoder = _FlowJSONEncoder()
    assert encoder._get_json_type(DataSource(id="1", title="Example")) == {
        "type": "object",
        "properties": {"id": {"type": "string"}, "title": {"type": "string"}},
    }


def test_encoder_multiple_data_sources():
    encoder = _FlowJSONEncoder()
    assert encoder._get_json_type(
        [
            DataSource(id="1", title="Example"),
            DataSource(id="2", title="Example2"),
        ]
    ) == {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
            },
        },
    }


def test_screen_data_empty_example():
    with pytest.raises(ValueError):
        FlowJSON(
            screens=[
                Screen(
                    id="test",
                    title="Test",
                    data=[ScreenData(key="test", example=[])],
                    layout=Layout(children=[]),
                )
            ],
            version="2.1",
        ).to_json()


def test_screen_data_invalid_type():
    with pytest.raises(ValueError):
        FlowJSON(
            screens=[
                Screen(
                    id="test",
                    title="Test",
                    data=[ScreenData(key="test", example=ValueError)],
                    layout=Layout(children=[]),
                )
            ],
            version="2.1",
        ).to_json()


def test_flow_response_with_error_msg():
    assert (
        "error_message"
        in FlowResponse(
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            screen="TEST",
            error_message="Example",
        ).to_dict()["data"]
    )


def test_flow_response_with_close_flow():
    assert (
        FlowResponse(  # closing flow make screen `SUCCESS`
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            close_flow=True,
            flow_token="test",
        ).to_dict()["screen"]
        == "SUCCESS"
    )

    with pytest.raises(ValueError):  # not closing flow without screen
        FlowResponse(
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            flow_token="test",
            close_flow=False,
        )

    with pytest.raises(ValueError):  # closing flow without flow_token
        FlowResponse(
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            close_flow=True,
        )

    with pytest.raises(ValueError):  # closing flow with error_message
        FlowResponse(
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            close_flow=True,
            flow_token="fdf",
            error_message="Example",
        )


def test_flow_response_with_data_sources():
    assert FlowResponse(
        version=Version.FLOW_MSG.value,
        data={"data_source": DataSource(id="1", title="Example")},
        screen="TEST",
    ).to_dict()["data"]["data_source"] == {"id": "1", "title": "Example"}

    assert FlowResponse(
        version=Version.FLOW_MSG.value,
        data={"data_source": [DataSource(id="1", title="Example")]},
        screen="TEST",
    ).to_dict()["data"]["data_source"] == [{"id": "1", "title": "Example"}]


def test_flow_callback_wrapper():
    wa = WhatsApp(
        token="xxx", server=None, business_private_key="xxx", verify_token="fdfd"
    )

    def main_handler(_, __): ...

    req = FlowRequest(
        version=...,
        action=FlowRequestActionType.DATA_EXCHANGE,
        flow_token="xyz",
        screen="START",
        data={},
        raw=...,
        raw_encrypted=...,
    )
    wrapper = wa.get_flow_request_handler(
        endpoint="/flow",
        callback=main_handler,
        request_decryptor=...,
        response_encryptor=...,
    )
    assert wrapper._get_callback(req) is main_handler

    def data_exchange_start_screen_callback(_, __): ...

    wrapper.add_handler(
        callback=data_exchange_start_screen_callback,
        action=FlowRequestActionType.DATA_EXCHANGE,
        screen="START",
    )
    req = dataclasses.replace(req, screen="START")
    assert wrapper._get_callback(req) is data_exchange_start_screen_callback

    def data_exchange_callback_without_screen(_, __): ...

    wrapper.add_handler(
        callback=data_exchange_callback_without_screen,
        action=FlowRequestActionType.DATA_EXCHANGE,
        screen=None,
    )
    assert wrapper._get_callback(req) is data_exchange_callback_without_screen

    def init_with_data_filter(_, __): ...

    wrapper._on_callbacks.clear()
    wrapper.add_handler(
        callback=init_with_data_filter,
        action=FlowRequestActionType.INIT,
        screen=None,
        filters=filters.new(lambda _, r: r.data.get("age") >= 20),
    )
    req = dataclasses.replace(req, action=FlowRequestActionType.INIT, data={"age": 20})
    assert wrapper._get_callback(req) is init_with_data_filter


def test_flows_server():
    with pytest.raises(ValueError, match="^When using a custom server.*"):
        wa = WhatsApp(token=..., server=None, verify_token=...)
        wa.add_flow_request_handler(
            handlers.FlowRequestHandler(
                callback=...,
                endpoint=...,
            )
        )

    with pytest.raises(ValueError, match="^You must initialize the WhatsApp client.*"):
        wa = WhatsApp(token=..., server=utils.MISSING)
        wa.add_flow_request_handler(
            handlers.FlowRequestHandler(
                callback=...,
                endpoint=...,
            )
        )
