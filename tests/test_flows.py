import dataclasses
import datetime
import importlib
import json
import pathlib
from typing import Callable

import pytest

from pywa import WhatsApp, handlers, utils, filters
from pywa.handlers import FlowCompletionHandler
from pywa.types.flows import (
    FlowJSON,
    Screen,
    Layout,
    Form,
    TextInput,
    InputType,
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
    NavigationItemEnd,
    NavigationItemMainContent,
    NavigationItem,
    NavigateAction,
    Next,
    FlowStr,
    FlowPreview,
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
                    assert obj_dict["version"] == version.name.replace("_", ".")
                    assert example_dict["version"] == version.name.replace("_", ".")
                    assert obj_dict == example_dict, (
                        f"Flow {version.name=} {flow_name=} does not match example"
                    )


def test_min_version():
    with pytest.raises(ValueError):
        FlowJSON(version="1.0", screens=[])


def test_empty_form():
    with pytest.raises(ValueError):
        Form(name="form", children=[])


def test_component_ref():
    assert ComponentRef("test").to_str() == "${form.test}"
    assert ComponentRef("test", screen="START").to_str() == "${screen.START.form.test}"
    assert TextInput(name="test", label="Test").ref.to_str() == "${form.test}"
    assert (
        TextInput(name="test", label="Test").ref_in(screen="START").to_str()
        == "${screen.START.form.test}"
    )
    in_ref = (
        Screen(id="START", layout=Layout(children=[]))
        / TextInput(name="test", label="Test").ref
    )
    assert in_ref.to_str() == "${screen.START.form.test}"
    assert isinstance(in_ref, ComponentRef)


def test_screen_data_ref():
    assert ScreenDataRef("test").to_str() == "${data.test}"
    assert ScreenDataRef("test", screen="START").to_str() == "${screen.START.data.test}"
    assert ScreenData(key="test", example="Example").ref.to_str() == "${data.test}"
    assert (
        ScreenData(key="test", example="Example").ref_in(screen="START").to_str()
        == "${screen.START.data.test}"
    )
    in_ref = (
        Screen(id="START", layout=Layout(children=[]))
        / ScreenData(key="test", example="Example").ref
    )
    assert in_ref.to_str() == "${screen.START.data.test}"
    assert isinstance(in_ref, ScreenDataRef)


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


def test_ref_addition():
    ref = Ref(prefix="data", field="age")
    math_op = ref + 21
    assert math_op.to_str() == "(${data.age} + 21)"


def test_ref_right_addition():
    ref = Ref(prefix="data", field="age")
    math_op = 21 + ref
    assert math_op.to_str() == "(21 + ${data.age})"


def test_ref_subtraction():
    ref = Ref(prefix="data", field="age")
    math_op = ref - 21
    assert math_op.to_str() == "(${data.age} - 21)"


def test_ref_right_subtraction():
    ref = Ref(prefix="data", field="age")
    math_op = 21 - ref
    assert math_op.to_str() == "(21 - ${data.age})"


def test_ref_multiplication():
    ref = Ref(prefix="data", field="age")
    math_op = ref * 21
    assert math_op.to_str() == "(${data.age} * 21)"


def test_ref_right_multiplication():
    ref = Ref(prefix="data", field="age")
    math_op = 21 * ref
    assert math_op.to_str() == "(21 * ${data.age})"


def test_ref_division():
    ref = Ref(prefix="data", field="age")
    math_op = ref / 21
    assert math_op.to_str() == "(${data.age} / 21)"


def test_ref_right_division():
    ref = Ref(prefix="data", field="age")
    math_op = 21 / ref
    assert math_op.to_str() == "(21 / ${data.age})"


def test_ref_modulus():
    ref = Ref(prefix="data", field="age")
    math_op = ref % 21
    assert math_op.to_str() == "(${data.age} % 21)"


def test_ref_right_modulus():
    ref = Ref(prefix="data", field="age")
    math_op = 21 % ref
    assert math_op.to_str() == "(21 % ${data.age})"


def test_math_ref_with_ref():
    ref_one = Ref(prefix="data", field="age")
    ref_two = Ref(prefix="data", field="height")
    math_op = ref_one + ref_two
    assert math_op.to_str() == "(${data.age} + ${data.height})"


def test_ref_with_math_op():
    ref = Ref(prefix="data", field="age")
    math_op = 21 + ref
    ref_with_math_op = ref + math_op
    assert ref_with_math_op.to_str() == "(${data.age} + (21 + ${data.age}))"


def test_math_op_with_ref():
    ref = Ref(prefix="data", field="age")
    math_op = 21 + ref
    math_op_with_ref = math_op + ref
    assert math_op_with_ref.to_str() == "((21 + ${data.age}) + ${data.age})"


def test_math_op_with_math_op():
    ref = Ref(prefix="data", field="age")
    math_op_1 = 21 + ref
    math_op_2 = 21 + ref
    assert (
        math_op_1 + math_op_2
    ).to_str() == "((21 + ${data.age}) + (21 + ${data.age}))"


def test_math_op_with_number():
    ref = Ref(prefix="data", field="age")
    math_op = 21 + ref
    math_op_with_number = math_op + 21
    assert math_op_with_number.to_str() == "((21 + ${data.age}) + 21)"


def test_ref_with_math_op_and_ref():
    ref = Ref(prefix="data", field="age")
    math_op = 21 + ref
    math_op_with_ref = ref + math_op + ref
    assert (
        math_op_with_ref.to_str()
        == "((${data.age} + (21 + ${data.age})) + ${data.age})"
    )


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


def test_condition_with_backticks():
    ref = Ref(prefix="data", field="age")
    condition = ref > 18
    assert condition.to_str() == "(${data.age} > 18)"
    condition.wrap_with_backticks = True
    assert condition.to_str() == "`(${data.age} > 18)`"


def visible_conditions_wrapped_with_backticks():
    text = TextInput(name="test", label="Test", visible=Ref("data", "age") > 18)
    assert text.visible.to_str() == "`(${data.age} > 18)`"


def test_flow_str():
    assert (
        FlowStr(string="This is an example for Ana`s house.").to_str()
        == r"` 'This is an example for Ana\\`s house.' `"
    )

    assert (
        FlowStr(string="This is an example for Ana's house.").to_str()
        == r"` 'This is an example for Ana\\'s house.' `"
    )

    assert (
        FlowStr(
            string=r"This is an example with already escaped backticks \\`."
        ).to_str()
        == r"` 'This is an example with already escaped backticks \\`.' `"
    )

    assert (
        FlowStr(
            string="This is an example with vars {var1} and {var2}.",
            var1=ComponentRef("age"),
            var2=ComponentRef("height"),
        ).to_str()
        == r"` 'This is an example with vars ' ${form.age} ' and ' ${form.height} '.' `"
    )

    assert (
        FlowStr(
            string="This is an example with `{var1}` wrapped in backticks and '{var2}' with single quotes.",
            var1=ComponentRef("age"),
            var2=ComponentRef("height"),
        ).to_str()
        == r"` 'This is an example with \\`' ${form.age} '\\` wrapped in backticks and \\'' ${form.height} '\\' with single quotes.' `"
    )

    assert (
        FlowStr(
            string="This is an example with math expression {var1_plus_var2} and {var1_minus_var2}.",
            var1_plus_var2=ComponentRef("age") + ComponentRef("height"),
            var1_minus_var2=ComponentRef("age") - ComponentRef("height"),
        ).to_str()
        == r"` 'This is an example with math expression ' (${form.age} + ${form.height}) ' and ' (${form.age} - ${form.height}) '.' `"
    )


def test_init_values():
    text_entry = TextInput(name="test", label="Test", init_value="Example")
    form = Form(name="form", children=[text_entry])
    assert form.init_values == {"test": "Example"}

    # check for duplicate init_values (in the form level and in the children level)
    # with pytest.raises(ValueError):
    #     TextInput(
    #         name="test", label="Test", init_value="Example", input_type=InputType.NUMBER
    #     )
    #     Form(name="form", init_values={"test": "Example"}, children=[text_entry])

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
    # with pytest.raises(ValueError):
    #     TextInput(name="test", label="Test", error_message="Example")
    #     Form(name="form", error_messages={"test": "Example"}, children=[text_entry])

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


def test_encoder_navigation_item():
    encoder = _FlowJSONEncoder()
    assert encoder._get_json_type(
        [
            NavigationItem(
                id="1",
                main_content=NavigationItemMainContent(
                    title="First item",
                    description="first item",
                    metadata="metadata",
                ),
                end=NavigationItemEnd(
                    title="End",
                    description="the end",
                ),
                on_click_action=NavigateAction(next=Next(name="SECOND_SCREEN")),
            )
        ]
    ) == {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "main-content": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "metadata": {"type": "string"},
                    },
                },
            },
        },
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


@pytest.fixture
def flow_request():
    return FlowRequest(
        version=...,
        action=FlowRequestActionType.DATA_EXCHANGE,
        flow_token="xyz",
        screen="START",
        data={},
        raw=...,
        raw_encrypted=...,
    )


def get_flow_callback_wrapper(callback: Callable):
    wa = WhatsApp(
        token="xxx", server=None, business_private_key="xxx", verify_token="fdfd"
    )
    wrapper = wa.get_flow_request_handler(
        endpoint="/flow",
        callback=callback,
        request_decryptor=...,
        response_encryptor=...,
    )
    return wrapper


def test_flow_callback_wrapper_main_handler(flow_request):
    def main_handler(_, __): ...

    wrapper = get_flow_callback_wrapper(main_handler)
    assert wrapper._get_callback(flow_request) is main_handler


def test_flow_callback_wrapper_screen(flow_request):
    def data_exchange_start_screen_callback(_, __): ...

    wrapper = get_flow_callback_wrapper(lambda _, __: ...)
    wrapper.add_handler(
        callback=data_exchange_start_screen_callback,
        action=FlowRequestActionType.DATA_EXCHANGE,
        screen="START",
    )
    req = dataclasses.replace(flow_request, screen="START")
    assert wrapper._get_callback(req) is data_exchange_start_screen_callback

    def data_exchange_callback_without_screen(_, __): ...

    wrapper.add_handler(
        callback=data_exchange_callback_without_screen,
        action=FlowRequestActionType.DATA_EXCHANGE,
        screen=None,
    )
    assert wrapper._get_callback(req) is data_exchange_callback_without_screen


def test_flow_callback_wrapper_filters(flow_request):
    def init_with_data_filter(_, __): ...

    wrapper = get_flow_callback_wrapper(lambda _, __: ...)
    wrapper.add_handler(
        callback=init_with_data_filter,
        action=FlowRequestActionType.INIT,
        screen=None,
        filters=filters.new(lambda _, r: r.data.get("age") >= 20),
    )
    req = dataclasses.replace(
        flow_request, action=FlowRequestActionType.INIT, data={"age": 20}
    )
    assert wrapper._get_callback(req) is init_with_data_filter


def test_flow_callback_wrapper_on_error(flow_request):
    wrapper = get_flow_callback_wrapper(lambda _, __: ...)

    @wrapper.on_data_exchange(call_on_error=False)
    def not_on_error(_, __): ...

    @wrapper.on_data_exchange(call_on_error=True)
    def on_error(_, __): ...

    req = dataclasses.replace(
        flow_request,
        action=FlowRequestActionType.DATA_EXCHANGE,
        data={"error_message": "Example"},
    )
    assert wrapper._get_callback(req) is on_error


def test_flow_callback_wrapper_on_completion():
    wrapper = get_flow_callback_wrapper(lambda _, __: ...)

    @wrapper.on_completion
    def on_completion(_, __): ...

    assert wrapper._wa._handlers[FlowCompletionHandler][0]._callback is on_completion


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


def test_flow_preview_with_params():
    preview = FlowPreview(
        url="https://business.facebook.com/wa/manage/flows/1460367762010364/preview/?token=fihsufcisd-09ad-4b88-b6aa-hdiewfcw",
        expires_at=datetime.datetime.now(),
    )
    assert (
        preview.with_params(
            interactive=True,
            flow_token="flow_token_example",
            flow_action=FlowRequestActionType.NAVIGATE,
            flow_action_payload={
                "screen": "START",
                "is_new_user": True,
                "welcome_msg": "Welcome to our service!",
            },
            phone_number="1234567890",
            debug=True,
        )
        == "https://business.facebook.com/wa/manage/flows/1460367762010364/preview/?token=fihsufcisd-09ad-4b88-b6aa-hdiewfcw&flow_token=flow_token_example&interactive=true&flow_action=navigate&flow_action_payload=%7B%22screen%22%3A%22START%22%2C%22is_new_user%22%3Atrue%2C%22welcome_msg%22%3A%22Welcome+to+our+service%21%22%7D&phone_number=1234567890&debug=true"
    )
