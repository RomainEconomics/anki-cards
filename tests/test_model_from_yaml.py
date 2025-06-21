import pytest
from pydantic import ValidationError

from anki_cards.model_from_yaml import (
    AnkiField,
    AnkiModelDefinition,
    AnkiTemplate,
    load_and_validate_model,
)


class TestAnkiField:
    def test_valid_field(self):
        field = AnkiField(name="Question")
        assert field.name == "Question"

    def test_field_name_required(self):
        with pytest.raises(ValidationError):
            AnkiField()


class TestAnkiTemplate:
    def test_valid_template(self):
        template = AnkiTemplate(name="Card 1", qfmt="{{Question}}", afmt="{{Answer}}")
        assert template.name == "Card 1"
        assert template.qfmt == "{{Question}}"
        assert template.afmt == "{{Answer}}"

    def test_template_required_fields(self):
        with pytest.raises(ValidationError):
            AnkiTemplate(name="Card 1")


class TestAnkiModelDefinition:
    def test_valid_model(self, sample_model_definition):
        assert sample_model_definition.id == 1234567890
        assert sample_model_definition.name == "Test Model"
        assert len(sample_model_definition.fields) == 3
        assert len(sample_model_definition.templates) == 1

    def test_model_with_minimal_fields(self):
        model = AnkiModelDefinition(
            id=123,
            name="Minimal Model",
            fields=[AnkiField(name="Front"), AnkiField(name="Back")],
            templates=[
                AnkiTemplate(
                    name="Card 1", qfmt="{{Front}}", afmt="{{Front}}<hr>{{Back}}"
                )
            ],
        )
        # Should auto-create yaml_field_map
        assert model.yaml_field_map == {"q": "Front", "a": "Back"}

    def test_model_validation_empty_fields(self):
        with pytest.raises(
            ValidationError, match="Fields and templates list cannot be empty"
        ):
            AnkiModelDefinition(
                id=123,
                name="Invalid Model",
                fields=[],
                templates=[
                    AnkiTemplate(name="Card 1", qfmt="{{Question}}", afmt="{{Answer}}")
                ],
            )

    def test_model_validation_empty_templates(self):
        with pytest.raises(
            ValidationError, match="Fields and templates list cannot be empty"
        ):
            AnkiModelDefinition(
                id=123,
                name="Invalid Model",
                fields=[AnkiField(name="Question")],
                templates=[],
            )

    def test_model_validation_negative_id(self):
        with pytest.raises(
            ValidationError, match="Model ID must be a positive integer"
        ):
            AnkiModelDefinition(
                id=-1,
                name="Invalid Model",
                fields=[AnkiField(name="Question")],
                templates=[
                    AnkiTemplate(
                        name="Card 1", qfmt="{{Question}}", afmt="{{Question}}"
                    )
                ],
            )

    def test_model_validation_template_undefined_fields(self):
        with pytest.raises(ValidationError, match="uses undefined fields"):
            AnkiModelDefinition(
                id=123,
                name="Invalid Model",
                fields=[AnkiField(name="Question")],
                templates=[
                    AnkiTemplate(
                        name="Card 1",
                        qfmt="{{Question}}",
                        afmt="{{UndefinedField}}",  # This field doesn't exist
                    )
                ],
            )

    def test_model_validation_builtin_fields_allowed(self):
        # Should not fail with built-in fields like FrontSide, Tags, etc.
        model = AnkiModelDefinition(
            id=123,
            name="Valid Model",
            fields=[AnkiField(name="Question"), AnkiField(name="Answer")],
            templates=[
                AnkiTemplate(
                    name="Card 1",
                    qfmt="{{Question}}",
                    afmt="{{FrontSide}}<hr>{{Answer}}<br>{{Tags}}",
                )
            ],
        )
        assert model.name == "Valid Model"

    def test_model_single_field_no_default_mapping(self):
        with pytest.raises(ValidationError, match="Cannot set default q/a mapping"):
            AnkiModelDefinition(
                id=123,
                name="Single Field Model",
                fields=[AnkiField(name="OnlyField")],
                templates=[
                    AnkiTemplate(
                        name="Card 1", qfmt="{{OnlyField}}", afmt="{{OnlyField}}"
                    )
                ],
            )

    def test_model_invalid_yaml_field_map(self):
        with pytest.raises(
            ValidationError, match="yaml_field_map contains fields not defined"
        ):
            AnkiModelDefinition(
                id=123,
                name="Invalid Mapping Model",
                fields=[AnkiField(name="Question"), AnkiField(name="Answer")],
                templates=[
                    AnkiTemplate(name="Card 1", qfmt="{{Question}}", afmt="{{Answer}}")
                ],
                yaml_field_map={
                    "q": "Question",
                    "a": "NonExistentField",  # This field doesn't exist
                },
            )

    def test_model_with_tags_field(self):
        model = AnkiModelDefinition(
            id=123,
            name="Model with Tags",
            fields=[
                AnkiField(name="Question"),
                AnkiField(name="Answer"),
                AnkiField(name="Tags"),
            ],
            templates=[
                AnkiTemplate(name="Card 1", qfmt="{{Question}}", afmt="{{Answer}}")
            ],
        )
        # Should auto-include tags in yaml_field_map
        assert "tags" in model.yaml_field_map
        assert model.yaml_field_map["tags"] == "Tags"


class TestLoadAndValidateModel:
    def test_load_valid_yaml_file(self, temp_dir, sample_model_yaml):
        model_file = temp_dir / "test_model.yaml"
        model_file.write_text(sample_model_yaml)

        model = load_and_validate_model(model_file)
        assert model.name == "Test Model"
        assert model.id == 1234567890
        assert len(model.fields) == 3

    def test_load_nonexistent_file(self, temp_dir):
        nonexistent_file = temp_dir / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_and_validate_model(nonexistent_file)

    def test_load_invalid_yaml(self, temp_dir):
        invalid_yaml = temp_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError, match="Invalid YAML"):
            load_and_validate_model(invalid_yaml)

    def test_load_invalid_model_definition(self, temp_dir):
        invalid_model = temp_dir / "invalid_model.yaml"
        invalid_model.write_text("id: -1\nname: Invalid")  # Missing required fields

        with pytest.raises(ValueError, match="Invalid model definition"):
            load_and_validate_model(invalid_model)

    def test_load_model_with_template_validation_error(self, temp_dir):
        invalid_template_yaml = """
id: 123
name: "Invalid Template Model"
fields:
  - name: "Question"
templates:
  - name: "Card 1"
    qfmt: "{{Question}}"
    afmt: "{{UndefinedField}}"  # This will cause validation error
"""
        model_file = temp_dir / "invalid_template.yaml"
        model_file.write_text(invalid_template_yaml)

        with pytest.raises(ValueError, match="Invalid model definition"):
            load_and_validate_model(model_file)

