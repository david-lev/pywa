"""Parse Flow JSON dicts/strings into typed :class:`~pywa.types.flows.FlowJSON` objects."""

from __future__ import annotations

import dataclasses
import json
import re
from typing import Any

from . import flows as _f

_REF_RE = re.compile(
    r"^\$\{(?:screen\.(?P<screen>[^.]+)\.)?(?P<prefix>form|data)\.(?P<field>[^}]+)\}$"
)
_UNDERSCORE_JSON_KEYS = _f._UNDERSCORE_FIELDS

_COMPONENT_TYPES: dict[str, type] = {
    "Form": _f.Form,
    "TextHeading": _f.TextHeading,
    "TextSubheading": _f.TextSubheading,
    "TextBody": _f.TextBody,
    "TextCaption": _f.TextCaption,
    "RichText": _f.RichText,
    "TextInput": _f.TextInput,
    "TextArea": _f.TextArea,
    "CheckboxGroup": _f.CheckboxGroup,
    "RadioButtonsGroup": _f.RadioButtonsGroup,
    "Dropdown": _f.Dropdown,
    "ChipsSelector": _f.ChipsSelector,
    "Footer": _f.Footer,
    "OptIn": _f.OptIn,
    "EmbeddedLink": _f.EmbeddedLink,
    "NavigationList": _f.NavigationList,
    "DatePicker": _f.DatePicker,
    "CalendarPicker": _f.CalendarPicker,
    "Image": _f.Image,
    "ImageCarousel": _f.ImageCarousel,
    "PhotoPicker": _f.PhotoPicker,
    "DocumentPicker": _f.DocumentPicker,
    "If": _f.If,
    "Switch": _f.Switch,
}

_ACTION_TYPES: dict[str, type] = {
    "data_exchange": _f.DataExchangeAction,
    "navigate": _f.NavigateAction,
    "open_url": _f.OpenURLAction,
    "update_data": _f.UpdateDataAction,
    "complete": _f.CompleteAction,
}

_CHILDREN_FIELDS = frozenset({"children", "then", "else_"})
_ACTION_FIELDS = frozenset(
    {
        "on_click_action",
        "on_select_action",
        "on_unselect_action",
    }
)
_DATA_SOURCE_FIELDS = frozenset({"data_source"})
_LIST_ITEMS_FIELDS = frozenset({"list_items"})
_IMAGES_FIELDS = frozenset({"images"})
_CONDITION_FIELDS = frozenset({"condition"})
_CASES_FIELDS = frozenset({"cases"})
_DYNAMIC_VALUE_FIELDS = frozenset(
    {
        "text",
        "label",
        "description",
        "helper_text",
        "title",
        "src",
        "alt_text",
        "metadata",
        "color",
        "image",
        "pattern",
        "input_type",
        "label_variant",
        "font_weight",
        "scale_type",
        "photo_source",
        "media_size",
        "mode",
        "value",
        "visible",
        "enabled",
        "required",
        "init_value",
        "error_message",
        "init_values",
        "error_messages",
        "min_date",
        "max_date",
        "unavailable_dates",
        "include_days",
        "left_caption",
        "center_caption",
        "right_caption",
        "aspect_ratio",
    }
)


def parse_flow_json(data: dict[str, Any]) -> _f.FlowJSON:
    """Parse a Flow JSON object dict into a :class:`FlowJSON`."""
    return _f.FlowJSON(
        version=data["version"],
        data_api_version=data.get("data_api_version"),
        routing_model=data.get("routing_model"),
        data_channel_uri=data.get("data_channel_uri"),
        screens=[_parse_screen(screen) for screen in data["screens"]],
    )


def parse_flow_json_str(json_str: str | bytes) -> _f.FlowJSON:
    """Parse a Flow JSON string into a :class:`FlowJSON`."""
    return parse_flow_json(json.loads(json_str))


def _parse_screen(data: dict[str, Any]) -> _f.Screen:
    return _f.Screen(
        id=data["id"],
        title=data.get("title"),
        data=_parse_screen_data(data.get("data")),
        terminal=data.get("terminal"),
        success=data.get("success"),
        refresh_on_back=data.get("refresh_on_back"),
        sensitive=data.get("sensitive"),
        layout=_parse_layout(data["layout"]),
    )


def _parse_layout(data: dict[str, Any]) -> _f.Layout:
    return _f.Layout(
        type=_f.LayoutType(data.get("type", _f.LayoutType.SINGLE_COLUMN)),
        children=[_parse_component(child) for child in data.get("children", [])],
    )


def _parse_screen_data(
    data: dict[str, Any] | None,
) -> list[_f.ScreenData] | dict[str, dict] | None:
    if data is None:
        return None
    if data == {}:
        return {}
    return [
        _f.ScreenData(key=key, example=_parse_screen_data_example(entry))
        for key, entry in data.items()
    ]


def _parse_screen_data_example(entry: dict[str, Any]) -> Any:
    example = entry.get("__example__")
    return _hydrate_example(example)


def _hydrate_example(example: Any) -> Any:
    if isinstance(example, list):
        return [_hydrate_example(item) for item in example]
    if isinstance(example, dict):
        if _is_data_source_dict(example):
            return _parse_data_source(example)
        if _is_navigation_item_dict(example):
            return _parse_navigation_item(example)
        return {key: _hydrate_example(value) for key, value in example.items()}
    return example


def _is_data_source_dict(data: dict[str, Any]) -> bool:
    return (
        "id" in data
        and "title" in data
        and "main-content" not in data
        and "main_content" not in data
    )


def _is_navigation_item_dict(data: dict[str, Any]) -> bool:
    return "id" in data and ("main-content" in data or "main_content" in data)


def _parse_component(data: dict[str, Any] | Any) -> Any:
    if not isinstance(data, dict):
        return data
    type_name = data.get("type")
    if type_name not in _COMPONENT_TYPES:
        return data
    cls = _COMPONENT_TYPES[type_name]
    kwargs = _parse_component_kwargs(cls, data)
    return cls(**kwargs)


def _parse_component_kwargs(cls: type, data: dict[str, Any]) -> dict[str, Any]:
    init_fields = {f.name for f in dataclasses.fields(cls) if f.init}
    kwargs: dict[str, Any] = {}
    for raw_key, raw_value in data.items():
        if raw_key == "type":
            continue
        key = _json_key_to_field(raw_key)
        if key not in init_fields:
            continue
        kwargs[key] = _parse_field_value(key, raw_value, component_cls=cls)
    return kwargs


def _json_key_to_field(key: str) -> str:
    if key in _UNDERSCORE_JSON_KEYS:
        return key
    if key == "else":
        return "else_"
    return key.replace("-", "_")


def _parse_field_value(
    field: str, value: Any, *, component_cls: type | None = None
) -> Any:
    if value is None:
        return None

    if field in _CHILDREN_FIELDS:
        return [_parse_component(child) for child in value]

    if field in _CASES_FIELDS:
        return {
            case: [_parse_component(child) for child in children]
            for case, children in value.items()
        }

    if field in _ACTION_FIELDS:
        return _parse_action_or_range(value)

    if field in _DATA_SOURCE_FIELDS:
        return _parse_data_source_value(value)

    if field in _LIST_ITEMS_FIELDS:
        return _parse_list_items_value(value)

    if field in _IMAGES_FIELDS:
        return [_parse_image_carousel_item(item) for item in value]

    if field in _CONDITION_FIELDS:
        return _parse_condition_value(value, wrap_with_backticks=False)

    if field == "include_days" and isinstance(value, list):
        return value

    if isinstance(value, dict) and _is_calendar_range(value):
        return _parse_calendar_range(value, field=field)

    if field in _DYNAMIC_VALUE_FIELDS or field in {"value"}:
        return _parse_dynamic_value(value)

    if isinstance(value, list):
        return [_parse_dynamic_value(item) for item in value]

    if isinstance(value, dict):
        return {key: _parse_dynamic_value(item) for key, item in value.items()}

    return value


def _is_calendar_range(data: dict[str, Any]) -> bool:
    keys = set(data)
    return keys <= {"start-date", "end-date", "start_date", "end_date"} and (
        "start-date" in data
        or "start_date" in data
        or "end-date" in data
        or "end_date" in data
    )


def _parse_calendar_range(
    data: dict[str, Any], *, field: str
) -> _f.CalendarRangeValues:
    start = data.get("start-date", data.get("start_date"))
    end = data.get("end-date", data.get("end_date"))
    if field in _ACTION_FIELDS or field == "on_select_action":
        return _f.CalendarRangeValues(
            start_date=_parse_action(start) if isinstance(start, dict) else start,
            end_date=_parse_action(end) if isinstance(end, dict) else end,
        )
    return _f.CalendarRangeValues(
        start_date=_parse_dynamic_value(start),
        end_date=_parse_dynamic_value(end),
    )


def _parse_action_or_range(value: Any) -> Any:
    if isinstance(value, dict) and _is_calendar_range(value):
        return _parse_calendar_range(value, field="on_select_action")
    return _parse_action(value)


def _parse_action(data: dict[str, Any] | Any) -> Any:
    if not isinstance(data, dict):
        return data
    name = data.get("name")
    if name not in _ACTION_TYPES:
        return data
    cls = _ACTION_TYPES[name]
    if cls is _f.OpenURLAction:
        return cls(url=data["url"])
    if cls is _f.NavigateAction:
        return cls(
            next=_parse_next(data["next"]),
            payload=_parse_action_payload(data.get("payload", {})),
        )
    if cls is _f.UpdateDataAction:
        return cls(payload=_parse_update_data_payload(data.get("payload", {})))
    return cls(payload=_parse_action_payload(data.get("payload", {})))


def _parse_next(data: dict[str, Any]) -> _f.Next:
    return _f.Next(name=data["name"], type=data.get("type", _f.NextType.SCREEN))


def _parse_action_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: _parse_payload_value(value) for key, value in payload.items()}


def _parse_update_data_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: _parse_payload_value(value) for key, value in payload.items()}


def _parse_payload_value(value: Any) -> Any:
    if isinstance(value, list):
        if value and all(
            isinstance(item, dict) and _is_data_source_dict(item) for item in value
        ):
            return [_parse_data_source(item) for item in value]
        return [_parse_payload_value(item) for item in value]
    if isinstance(value, dict):
        if _is_data_source_dict(value):
            return _parse_data_source(value)
        return {key: _parse_payload_value(item) for key, item in value.items()}
    return _parse_dynamic_value(value)


def _parse_data_source_value(value: Any) -> Any:
    parsed = _parse_dynamic_value(value)
    if isinstance(parsed, list):
        return [
            _parse_data_source(item) if isinstance(item, dict) else item
            for item in parsed
        ]
    if isinstance(value, list):
        return [_parse_data_source(item) for item in value]
    return parsed


def _parse_list_items_value(value: Any) -> Any:
    parsed = _parse_dynamic_value(value)
    if isinstance(parsed, _f.Ref):
        return parsed
    if isinstance(value, list):
        return [_parse_navigation_item(item) for item in value]
    return parsed


def _parse_data_source(data: dict[str, Any]) -> _f.DataSource:
    kwargs: dict[str, Any] = {}
    for raw_key, raw_value in data.items():
        key = _json_key_to_field(raw_key)
        if key in {"on_select_action", "on_unselect_action"}:
            kwargs[key] = _parse_action(raw_value)
        else:
            kwargs[key] = _parse_dynamic_value(raw_value)
    return _f.DataSource(
        **{
            key: value
            for key, value in kwargs.items()
            if key in {f.name for f in dataclasses.fields(_f.DataSource) if f.init}
        }
    )


def _parse_navigation_item(data: dict[str, Any]) -> _f.NavigationItem:
    main = data.get("main-content", data.get("main_content"))
    start = data.get("start")
    end = data.get("end")
    on_click = data.get("on-click-action", data.get("on_click_action"))
    return _f.NavigationItem(
        id=data["id"],
        main_content=_parse_navigation_main_content(main),
        start=_f.NavigationItemStart(image=start["image"]) if start else None,
        end=_parse_navigation_end(end) if end else None,
        badge=data.get("badge"),
        tags=data.get("tags"),
        on_click_action=_parse_action(on_click) if on_click else None,
    )


def _parse_navigation_main_content(
    data: dict[str, Any],
) -> _f.NavigationItemMainContent:
    return _f.NavigationItemMainContent(
        title=data["title"],
        description=data.get("description"),
        metadata=data.get("metadata"),
    )


def _parse_navigation_end(data: dict[str, Any]) -> _f.NavigationItemEnd:
    return _f.NavigationItemEnd(
        title=data.get("title"),
        description=data.get("description"),
        metadata=data.get("metadata"),
    )


def _parse_image_carousel_item(data: dict[str, Any]) -> _f.ImageCarouselItem:
    return _f.ImageCarouselItem(
        src=data["src"],
        alt_text=data.get("alt-text", data.get("alt_text")),
    )


def _parse_dynamic_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    ref = _try_parse_ref(value)
    if ref is not None:
        return ref

    if value.startswith("`") and value.endswith("`"):
        inner = value[1:-1].strip()
        if inner.startswith("(") or inner.startswith("!"):
            return _parse_condition_value(value, wrap_with_backticks=True)
        return _parse_flow_str_preserving(value)

    if value.startswith("(") or value.startswith("!"):
        try:
            return _parse_condition_value(value, wrap_with_backticks=False)
        except ValueError:
            return value

    return value


def _parse_flow_str_preserving(value: str) -> _f.FlowStr | str:
    """Parse as :class:`FlowStr` only when encoding round-trips exactly."""
    try:
        flow_str = _parse_flow_str(value)
    except (ValueError, TypeError):
        return value
    if flow_str.to_str() == value:
        return flow_str
    return value


def _try_parse_ref(value: str) -> _f.ScreenDataRef | _f.ComponentRef | None:
    match = _REF_RE.fullmatch(value)
    if not match:
        return None
    screen = match.group("screen")
    prefix = match.group("prefix")
    field = match.group("field")
    if prefix == "form":
        return _f.ComponentRef(field, screen=screen)
    return _f.ScreenDataRef(field, screen=screen)


def _parse_condition_value(value: str, *, wrap_with_backticks: bool) -> _f.Condition:
    expression = value
    if expression.startswith("`") and expression.endswith("`"):
        expression = expression[1:-1]
    condition = _ConditionParser(expression).parse()
    condition.wrap_with_backticks = wrap_with_backticks
    return condition


class _ConditionParser:
    """Recursive-descent parser for Flow condition / math expression strings."""

    def __init__(self, text: str):
        self.text = text
        self.tokens = _tokenize(text)
        self.pos = 0

    def parse(self) -> _f.Condition:
        node = self._parse_or()
        if self.pos != len(self.tokens):
            raise ValueError(
                f"Unexpected token {self.tokens[self.pos]!r} in {self.text!r}"
            )
        if not isinstance(node, _f.Condition):
            # Bare ref used as condition (e.g. ~ref / logical with refs)
            raise ValueError(f"Expected condition expression, got {node!r}")
        return node

    def parse_math(self) -> _f.MathExpression | _f.Ref | int | float:
        node = self._parse_add()
        if self.pos != len(self.tokens):
            raise ValueError(
                f"Unexpected token {self.tokens[self.pos]!r} in {self.text!r}"
            )
        return node  # type: ignore[return-value]

    def _peek(self) -> tuple[str, Any] | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def _advance(self) -> tuple[str, Any]:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _match(self, *kinds: str) -> tuple[str, Any] | None:
        token = self._peek()
        if token and token[0] in kinds:
            return self._advance()
        return None

    def _parse_or(self) -> Any:
        left = self._parse_and()
        while self._match("OR"):
            right = self._parse_and()
            left = _f.Condition(left, "||", right)
        return left

    def _parse_and(self) -> Any:
        left = self._parse_not()
        while self._match("AND"):
            right = self._parse_not()
            left = _f.Condition(left, "&&", right)
        return left

    def _parse_not(self) -> Any:
        if self._match("NOT"):
            return _f.Condition(self._parse_not(), "!")
        return self._parse_comparison()

    def _parse_comparison(self) -> Any:
        left = self._parse_add()
        token = self._match("EQ", "NE", "GE", "LE", "GT", "LT")
        if not token:
            return left
        op = {
            "EQ": "==",
            "NE": "!=",
            "GE": ">=",
            "LE": "<=",
            "GT": ">",
            "LT": "<",
        }[token[0]]
        right = self._parse_add()
        return _f.Condition(left, op, right)  # type: ignore[arg-type]

    def _parse_add(self) -> Any:
        left = self._parse_mul()
        while True:
            token = self._match("PLUS", "MINUS")
            if not token:
                return left
            op = "+" if token[0] == "PLUS" else "-"
            right = self._parse_mul()
            left = _f.MathExpression(left, op, right)  # type: ignore[arg-type]

    def _parse_mul(self) -> Any:
        left = self._parse_primary()
        while True:
            token = self._match("STAR", "SLASH", "PERCENT")
            if not token:
                return left
            op = {"STAR": "*", "SLASH": "/", "PERCENT": "%"}[token[0]]
            right = self._parse_primary()
            left = _f.MathExpression(left, op, right)  # type: ignore[arg-type]

    def _parse_primary(self) -> Any:
        token = self._peek()
        if token is None:
            raise ValueError(f"Unexpected end of expression: {self.text!r}")

        kind, value = token
        if kind == "LPAREN":
            self._advance()
            node = self._parse_or()
            if not self._match("RPAREN"):
                raise ValueError(f"Expected ')' in {self.text!r}")
            return node

        self._advance()
        if kind == "REF":
            ref = _try_parse_ref(value)
            if ref is None:
                raise ValueError(f"Invalid ref: {value!r}")
            return ref
        if kind == "STRING":
            return value
        if kind == "NUMBER":
            return value
        if kind == "BOOL":
            return value
        raise ValueError(f"Unexpected token {token!r} in {self.text!r}")


def _tokenize(text: str) -> list[tuple[str, Any]]:
    tokens: list[tuple[str, Any]] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if text.startswith("${", i):
            end = text.find("}", i)
            if end == -1:
                raise ValueError(f"Unclosed ref in {text!r}")
            tokens.append(("REF", text[i : end + 1]))
            i = end + 1
            continue
        if ch == "'":
            value, i = _read_string(text, i)
            tokens.append(("STRING", value))
            continue
        if ch.isdigit() or (ch == "." and i + 1 < n and text[i + 1].isdigit()):
            value, i = _read_number(text, i)
            tokens.append(("NUMBER", value))
            continue
        if text.startswith("true", i) and _is_word_boundary(text, i + 4):
            tokens.append(("BOOL", True))
            i += 4
            continue
        if text.startswith("false", i) and _is_word_boundary(text, i + 5):
            tokens.append(("BOOL", False))
            i += 5
            continue
        if text.startswith("&&", i):
            tokens.append(("AND", "&&"))
            i += 2
            continue
        if text.startswith("||", i):
            tokens.append(("OR", "||"))
            i += 2
            continue
        if text.startswith("==", i):
            tokens.append(("EQ", "=="))
            i += 2
            continue
        if text.startswith("!=", i):
            tokens.append(("NE", "!="))
            i += 2
            continue
        if text.startswith(">=", i):
            tokens.append(("GE", ">="))
            i += 2
            continue
        if text.startswith("<=", i):
            tokens.append(("LE", "<="))
            i += 2
            continue
        if ch == ">":
            tokens.append(("GT", ">"))
            i += 1
            continue
        if ch == "<":
            tokens.append(("LT", "<"))
            i += 1
            continue
        if ch == "!":
            tokens.append(("NOT", "!"))
            i += 1
            continue
        if ch == "+":
            tokens.append(("PLUS", "+"))
            i += 1
            continue
        if ch == "-":
            tokens.append(("MINUS", "-"))
            i += 1
            continue
        if ch == "*":
            tokens.append(("STAR", "*"))
            i += 1
            continue
        if ch == "/":
            tokens.append(("SLASH", "/"))
            i += 1
            continue
        if ch == "%":
            tokens.append(("PERCENT", "%"))
            i += 1
            continue
        if ch == "(":
            tokens.append(("LPAREN", "("))
            i += 1
            continue
        if ch == ")":
            tokens.append(("RPAREN", ")"))
            i += 1
            continue
        raise ValueError(f"Invalid character {ch!r} in expression {text!r}")
    return tokens


def _is_word_boundary(text: str, index: int) -> bool:
    return index >= len(text) or not (text[index].isalnum() or text[index] == "_")


def _read_string(text: str, start: int) -> tuple[str, int]:
    i = start + 1
    chars: list[str] = []
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            chars.append(text[i + 1])
            i += 2
            continue
        if ch == "'":
            return "".join(chars), i + 1
        chars.append(ch)
        i += 1
    raise ValueError(f"Unclosed string in {text!r}")


def _read_number(text: str, start: int) -> tuple[int | float, int]:
    i = start
    while i < len(text) and (text[i].isdigit() or text[i] == "."):
        i += 1
    raw = text[start:i]
    if "." in raw:
        return float(raw), i
    return int(raw), i


def _parse_flow_str(value: str) -> _f.FlowStr:
    if not (value.startswith("`") and value.endswith("`")):
        raise ValueError(f"Invalid FlowStr value: {value!r}")
    inner = value[1:-1]
    tokens = _tokenize_flow_str(inner)
    template_parts: list[str] = []
    variables: dict[str, _f.Ref | _f.MathExpression] = {}
    var_index = 0
    for kind, token_value in tokens:
        if kind == "lit":
            template_parts.append(token_value)
            continue
        name = f"v{var_index}"
        var_index += 1
        template_parts.append("{" + name + "}")
        if kind == "ref":
            ref = _try_parse_ref(token_value)
            if ref is None:
                raise ValueError(f"Invalid ref in FlowStr: {token_value!r}")
            variables[name] = ref
        elif kind == "math":
            variables[name] = _ConditionParser(token_value).parse_math()  # type: ignore[assignment]
        else:
            raise ValueError(f"Unknown FlowStr token {kind}")
    return _f.FlowStr("".join(template_parts), **variables)


def _tokenize_flow_str(text: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i].isspace():
            i += 1
            continue
        if text[i] == "'":
            lit, i = _read_flow_str_literal(text, i)
            tokens.append(("lit", lit))
            continue
        if text.startswith("${", i):
            end = text.find("}", i)
            if end == -1:
                raise ValueError(f"Unclosed ref in FlowStr: {text!r}")
            tokens.append(("ref", text[i : end + 1]))
            i = end + 1
            continue
        if text[i] == "(":
            end = _find_matching_paren(text, i)
            tokens.append(("math", text[i : end + 1]))
            i = end + 1
            continue
        raise ValueError(f"Invalid FlowStr segment at {text[i:]!r}")
    return tokens


def _read_flow_str_literal(text: str, start: int) -> tuple[str, int]:
    """Read a FlowStr quoted literal and unescape \\' and \\`."""
    i = start + 1
    chars: list[str] = []
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt in {"\\", "'", "`"}:
                chars.append(nxt)
                i += 2
                continue
            chars.append(ch)
            i += 1
            continue
        if ch == "'":
            return "".join(chars), i + 1
        chars.append(ch)
        i += 1
    raise ValueError(f"Unclosed FlowStr literal in {text!r}")


def _find_matching_paren(text: str, start: int) -> int:
    depth = 0
    i = start
    in_str = False
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\" and i + 1 < len(text):
                i += 2
                continue
            if ch == "'":
                in_str = False
            i += 1
            continue
        if ch == "'":
            in_str = True
            i += 1
            continue
        if text.startswith("${", i):
            end = text.find("}", i)
            if end == -1:
                raise ValueError(f"Unclosed ref in {text!r}")
            i = end + 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError(f"Unclosed '(' in {text!r}")
