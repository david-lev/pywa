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
