import pathlib
import re

import structlog
import yaml
from pydantic import BaseModel, ValidationError, field_validator, model_validator

log = structlog.get_logger()


# Regex to find field references in Anki templates
TEMPLATE_FIELD_RE = re.compile(r"\{\{([#/^]?)([^}]+?)\}\}")


class AnkiField(BaseModel):
    name: str


class AnkiTemplate(BaseModel):
    name: str
    qfmt: str
    afmt: str


class AnkiModelDefinition(BaseModel):
    """Pydantic model for validating Anki model structure from YAML."""

    id: int
    name: str
    fields: list[AnkiField]
    templates: list[AnkiTemplate]
    # Optional mapping from YAML keys (like 'q', 'a') to Anki Field names
    # Defaults to mapping 'q' -> first field, 'a' -> second field
    yaml_field_map: dict[str, str] | None = None
    # Optional CSS styling
    css: str = ""

    @field_validator("fields", "templates")
    def check_not_empty(cls, v):
        if not v:
            raise ValueError("Fields and templates list cannot be empty")
        return v

    @field_validator("id")
    def check_id_positive(cls, v):
        if v <= 0:
            raise ValueError("Model ID must be a positive integer")
        return v

    @model_validator(mode="after")
    def check_template_fields_exist(self) -> "AnkiModelDefinition":
        if not self.fields:  # Avoid errors if fields validation failed
            return self
        field_names = {field.name for field in self.fields}

        for i, template in enumerate(self.templates):
            # Check qfmt
            q_fields = {
                match.group(2) for match in TEMPLATE_FIELD_RE.finditer(template.qfmt)
            }
            # Remove built-in fields like 'FrontSide', 'Tags', 'Deck', etc. if needed
            q_fields -= {
                "FrontSide",
                "Tags",
                "Type",
                "Deck",
                "Subdeck",
                "Card",
            }  # Add others if necessary
            missing_q_fields = q_fields - field_names
            if missing_q_fields:
                raise ValueError(
                    f"Template '{template.name}' (qfmt) uses undefined fields: {missing_q_fields}"
                )

            # Check afmt
            a_fields = {
                match.group(2) for match in TEMPLATE_FIELD_RE.finditer(template.afmt)
            }
            a_fields -= {"FrontSide", "Tags", "Type", "Deck", "Subdeck", "Card"}
            missing_a_fields = a_fields - field_names
            if missing_a_fields:
                raise ValueError(
                    f"Template '{template.name}' (afmt) uses undefined fields: {missing_a_fields}"
                )

        return self

    @model_validator(mode="after")
    def set_default_yaml_field_map(self) -> "AnkiModelDefinition":
        if self.yaml_field_map is None:
            if len(self.fields) >= 2:
                self.yaml_field_map = {
                    "q": self.fields[0].name,
                    "a": self.fields[1].name,
                }
                # Add mapping for 'tags' if it exists
                if any(f.name.lower() == "tags" for f in self.fields):
                    self.yaml_field_map["tags"] = next(
                        f.name for f in self.fields if f.name.lower() == "tags"
                    )
            else:
                # Cannot set default mapping if less than 2 fields
                raise ValueError(
                    "Cannot set default q/a mapping: Model must have at least two fields."
                )
        # Ensure mapped fields exist
        mapped_field_names = set(self.yaml_field_map.values())
        defined_field_names = {f.name for f in self.fields}
        missing_mapped = mapped_field_names - defined_field_names
        if missing_mapped:
            raise ValueError(
                f"yaml_field_map contains fields not defined in the model: {missing_mapped}"
            )

        return self


# --- Helper Function ---
def load_and_validate_model(model_path: pathlib.Path) -> AnkiModelDefinition:
    """Loads Anki model definition from YAML and validates it."""
    log.info("Loading Anki model definition", path=str(model_path))
    if not model_path.is_file():
        log.error("Model definition file not found.", path=str(model_path))
        raise FileNotFoundError(f"Model definition file not found: {model_path}")
    try:
        with model_path.open("r", encoding="utf-8") as f:
            model_data = yaml.safe_load(f)
        model_def = AnkiModelDefinition.model_validate(model_data)
        log.info("Model definition validated successfully.", model_name=model_def.name)
        return model_def
    except yaml.YAMLError as e:
        log.error(
            "Failed to parse model definition YAML.", path=str(model_path), error=str(e)
        )
        raise ValueError(f"Invalid YAML in model file {model_path}: {e}") from e
    except ValidationError as e:
        log.error(
            "Model definition validation failed.",
            path=str(model_path),
            errors=e.errors(),
        )
        # Pydantic provides detailed errors, log them
        # print(e) # Or log e.json() for more details
        raise ValueError(f"Invalid model definition in {model_path}:\n{e}") from e
    except Exception as e:
        log.error(
            "An unexpected error occurred loading the model.",
            path=str(model_path),
            error=str(e),
        )
        raise
