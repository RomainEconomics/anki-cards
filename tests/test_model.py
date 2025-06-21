import genanki

from anki_cards.model import create_genanki_model
from anki_cards.model_from_yaml import AnkiField, AnkiModelDefinition, AnkiTemplate


class TestCreateGenankiModel:
    def test_create_basic_model(self, sample_model_definition):
        genanki_model = create_genanki_model(sample_model_definition)

        assert isinstance(genanki_model, genanki.Model)
        assert genanki_model.model_id == sample_model_definition.id
        assert genanki_model.name == sample_model_definition.name

        # Check fields
        field_names = [f["name"] for f in genanki_model.fields]
        expected_field_names = [f.name for f in sample_model_definition.fields]
        assert field_names == expected_field_names

        # Check templates
        assert len(genanki_model.templates) == len(sample_model_definition.templates)
        template = genanki_model.templates[0]
        expected_template = sample_model_definition.templates[0]
        assert template["name"] == expected_template.name
        assert template["qfmt"] == expected_template.qfmt
        assert template["afmt"] == expected_template.afmt

    def test_create_model_with_css(self):
        model_def = AnkiModelDefinition(
            id=123456,
            name="Styled Model",
            fields=[AnkiField(name="Question"), AnkiField(name="Answer")],
            templates=[
                AnkiTemplate(name="Card 1", qfmt="{{Question}}", afmt="{{Answer}}")
            ],
            css=".card { background: blue; }",
        )

        genanki_model = create_genanki_model(model_def)
        assert genanki_model.css == ".card { background: blue; }"

    def test_create_model_multiple_templates(self):
        model_def = AnkiModelDefinition(
            id=789012,
            name="Multi-Template Model",
            fields=[
                AnkiField(name="Question"),
                AnkiField(name="Answer"),
                AnkiField(name="Extra"),
            ],
            templates=[
                AnkiTemplate(name="Forward", qfmt="{{Question}}", afmt="{{Answer}}"),
                AnkiTemplate(name="Reverse", qfmt="{{Answer}}", afmt="{{Question}}"),
            ],
        )

        genanki_model = create_genanki_model(model_def)
        assert len(genanki_model.templates) == 2
        assert genanki_model.templates[0]["name"] == "Forward"
        assert genanki_model.templates[1]["name"] == "Reverse"

    def test_create_model_preserves_field_order(self):
        model_def = AnkiModelDefinition(
            id=345678,
            name="Ordered Model",
            fields=[
                AnkiField(name="Third"),
                AnkiField(name="First"),
                AnkiField(name="Second"),
            ],
            templates=[
                AnkiTemplate(name="Card 1", qfmt="{{First}}", afmt="{{Second}}")
            ],
        )

        genanki_model = create_genanki_model(model_def)
        field_names = [f["name"] for f in genanki_model.fields]
        assert field_names == ["Third", "First", "Second"]

