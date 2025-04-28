import pathlib
from dataclasses import dataclass


@dataclass
class CliArgs:
    """
    Generate Anki deck (.apkg) from Markdown notes containing ```anki blocks.
    """

    notes_directory: pathlib.Path
    """Directory to scan recursively for .md files."""

    output_file: pathlib.Path = pathlib.Path("notes_deck.apkg")
    """Path where the generated Anki package will be saved."""

    model_definition: pathlib.Path = pathlib.Path("default_anki_model.yaml")
    """YAML file defining the Anki note type (fields, templates, etc.)."""

    verbose: bool = False
    """Print detailed processing information."""
