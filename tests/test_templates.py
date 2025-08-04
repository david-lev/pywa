import pytest

from pywa.types.templates import *  # noqa: F403
import importlib
import json
import pathlib


def test_templates_to_json(caplog):
    for templates_dir in pathlib.Path("tests/data/templates").iterdir():
        with open(
            pathlib.Path(templates_dir, "examples.json"), "r", encoding="utf-8"
        ) as f:
            json_examples = json.load(f)
            obj_examples = importlib.import_module(
                f"tests.data.templates.{templates_dir.name}.examples"
            )
            for template_name, template_json in json_examples.items():
                example_obj: Template = getattr(obj_examples, template_name)
                example_dict: dict = json_examples[template_name]

                assert (
                    json.loads(
                        Template.from_dict(json.loads(example_obj.to_json())).to_json()
                    )
                    == example_dict
                ), (
                    f"Template {templates_dir.name=} {template_name=} does not match example JSON."
                )
                assert not caplog.records, (
                    f"Template {templates_dir.name=} {template_name=} has warnings: {' '.join(record.message for record in caplog.records)}"
                )


def test_template_text_examples_params():
    with pytest.raises(ValueError):
        HeaderText.Params("pos", named="named")


def test_template_text_examples_positionals():
    h = HeaderText(
        "Hi {{1}}, this is a text template number {{2}}",
        "David",
        1,
    )
    assert h.to_dict() == {
        "type": "HEADER",
        "format": "TEXT",
        "text": "Hi {{1}}, this is a text template number {{2}}",
        "example": {
            "header_text": ["David", "1"],
        },
    }
    assert h.text == "Hi {{1}}, this is a text template number {{2}}"
    assert h.example == ("David", 1)
    assert h.preview() == "Hi David, this is a text template number 1"
    assert h.params("John", 100).to_dict() == {
        "type": "HEADER",
        "parameters": [
            {"type": "text", "text": "John"},
            {"type": "text", "text": "100"},
        ],
    }
    assert h.param_format == ParamFormat.POSITIONAL
    with pytest.raises(
        ValueError,
        match="HeaderText does not support named parameters when text is positional.",
    ):
        h.params(named="John")
    with pytest.raises(
        ValueError,
        match="HeaderText requires 2 positional parameters, got 3.",
    ):
        h.params("John", 100, "unexpected")

    with pytest.raises(
        ValueError,
        match="HeaderText does not support parameters, as it has no example.",
    ):
        HeaderText("Hi").params("John")


def test_template_text_examples_named():
    b = BodyText(
        "Hi {{name}}, this is a text template number {{number}}",
        name="David",
        number=1,
    )
    assert b.to_dict() == {
        "type": "BODY",
        "text": "Hi {{name}}, this is a text template number {{number}}",
        "example": {
            "body_text_named_params": [
                {"param_name": "name", "example": "David"},
                {"param_name": "number", "example": "1"},
            ]
        },
    }
    assert b.text == "Hi {{name}}, this is a text template number {{number}}"
    assert b.example == {"name": "David", "number": 1}
    assert b.preview() == "Hi David, this is a text template number 1"
    assert b.params(name="John", number=100).to_dict() == {
        "type": "BODY",
        "parameters": [
            {"type": "text", "text": "John", "parameter_name": "name"},
            {"type": "text", "text": "100", "parameter_name": "number"},
        ],
    }
    assert b.param_format == ParamFormat.NAMED
    with pytest.raises(
        ValueError,
        match="BodyText does not support positional parameters when text is named.",
    ):
        b.params("John")
    with pytest.raises(
        ValueError,
        match="BodyText received unexpected parameters: unexpected",
    ):
        b.params(name="John", number=100, unexpected="unexpected")

    with pytest.raises(ValueError, match="BodyText is missing parameters: number"):
        b.params(name="John")

    with pytest.raises(
        ValueError,
        match="BodyText does not support parameters, as it has no example.",
    ):
        BodyText("Hi").params(name="John")


def test_components_that_does_not_get_params():
    with pytest.raises(ValueError):
        FooterText(
            text="This is a footer text template",
        ).params("John")


def test_media_header_handle_reset():
    media_header = HeaderImage(example="https://example.com/image.jpg")
    media_header._handle = "1:handle"
    media_header.example = "https://example2.com/image.jpg"
    assert media_header._handle is None, (
        "Handle should be reset to None after example change"
    )
