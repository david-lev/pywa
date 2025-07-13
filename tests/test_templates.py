import pytest

from pywa.types.template import *  # noqa: F403
import importlib
import json
import pathlib


def test_templates_to_json():
    for templates_dir in pathlib.Path("tests/data/templates").iterdir():
        with open(
            pathlib.Path(templates_dir, "examples.json"), "r", encoding="utf-8"
        ) as f:
            json_examples = json.load(f)
            obj_examples = importlib.import_module(
                f"tests.data.templates.{templates_dir.name}.examples"
            )
            for template_name, template_json in json_examples.items():
                obj_dict = json.loads(getattr(obj_examples, template_name).to_json())
                example_dict = json_examples[template_name]
                assert obj_dict == example_dict, (
                    f"Template {templates_dir.name=} {template_name=} does not match example"
                )


def test_template_text_positionals():
    positionals = TemplateText("Hi {{1}}!, How are you? Get {{2}}% OFF!", "David", 15)
    assert positionals.param_format == ParamFormat.POSITIONAL
    assert positionals.example == ("David", 15)
    positionals.param_type = "body"
    assert positionals.to_dict() == {
        "text": "Hi {{1}}!, How are you? Get {{2}}% OFF!",
        "example": {
            "body_text": [["David", "15"]],
        },
    }
    assert positionals.preview() == "Hi David!, How are you? Get 15% OFF!"

    data = {
        "text": "Hi {{1}}!, How are you? Get {{2}}% OFF!",
        "example": {
            "header_text": ["David", "15"],
        },
    }
    template = TemplateText.from_dict(data)
    template.param_type = "header"
    assert template.param_format == ParamFormat.POSITIONAL
    assert template.example == ("David", "15")
    assert template.preview() == "Hi David!, How are you? Get 15% OFF!"


def test_template_text_named():
    named = TemplateText(
        "Hi {{name}}!, How are you? Get {{discount}}% OFF!",
        name="David",
        discount=15,
    )
    assert named.param_format == ParamFormat.NAMED
    assert named.example == {"name": "David", "discount": 15}
    named.param_type = "body"
    assert named.to_dict() == {
        "text": "Hi {{name}}!, How are you? Get {{discount}}% OFF!",
        "example": {
            "body_text_named_params": [
                {"param_name": "name", "example": "David"},
                {"param_name": "discount", "example": "15"},
            ],
        },
    }
    assert named.preview() == "Hi David!, How are you? Get 15% OFF!"

    data = {
        "text": "Hi {{name}}!, How are you? Get {{discount}}% OFF!",
        "example": {
            "body_text_named_params": [
                {"param_name": "name", "example": "David"},
                {"param_name": "discount", "example": "15"},
            ],
        },
    }
    template = TemplateText.from_dict(data)
    template.param_type = "body"
    assert template.param_format == ParamFormat.NAMED
    assert template.example == {"name": "David", "discount": "15"}
    assert template.preview() == "Hi David!, How are you? Get 15% OFF!"


def test_template_text_both_positionals_and_named_args():
    with pytest.raises(ValueError):
        TemplateText("", 1, also_named="test")


def test_template_text_to_dict_without_param_type():
    with pytest.raises(ValueError):
        TemplateText("Hello {{1}}").to_dict()
