import genanki
import structlog

from anki_cards.model_from_yaml import AnkiModelDefinition

log = structlog.get_logger()


def create_genanki_model(model_def: AnkiModelDefinition) -> genanki.Model:
    """Creates a genanki.Model object from the validated Pydantic model."""
    log.debug("Creating genanki.Model", model_name=model_def.name)
    return genanki.Model(
        model_id=model_def.id,
        name=model_def.name,
        fields=[{"name": f.name} for f in model_def.fields],
        templates=[
            {
                "name": t.name,
                "qfmt": t.qfmt,
                "afmt": t.afmt,
            }
            for t in model_def.templates
        ],
        css=model_def.css,
    )
