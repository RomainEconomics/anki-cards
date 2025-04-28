import logging
import pathlib
import re
import sys
from typing import Any

import genanki
import structlog
import tyro
import yaml
from pydantic import ValidationError

from anki_cards.cli import CliArgs
from anki_cards.model import create_genanki_model
from anki_cards.model_from_yaml import AnkiModelDefinition, load_and_validate_model

log = structlog.get_logger()


# --- Regexes ---
# Regex to find ```anki ... ``` blocks
ANKI_BLOCK_RE = re.compile(r"```anki\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
# Regex to find img tags and capture src. Added negative lookahead for http/https/data:
IMG_SRC_RE = re.compile(
    r'<img\s+[^>]*src="(?!https?://|data:)([^"]+)"[^>]*>', re.IGNORECASE
)


def calculate_deck_name(root_dir: pathlib.Path, filepath: pathlib.Path) -> str:
    """Calculates the default Anki deck name from the file path."""
    relative_path = filepath.relative_to(root_dir)
    # Use parent directories for deck hierarchy, joined by ::
    # Use root directory name as the top-level deck
    parts = [root_dir.name] + list(relative_path.parts[:-1])
    return "::".join(parts) if parts else root_dir.name


def process_field_for_images(
    field_content: str, md_file_dir: pathlib.Path
) -> tuple[str, list[str]]:
    """
    Finds local image tags, resolves paths, modifies src to filename,
    and collects absolute paths of found images.

    Returns:
        tuple[str, list[str]]: (modified_field_content, list_of_absolute_image_paths)
    """
    media_files: list[str] = []
    processed_content = field_content
    found_media_in_field: list[str] = []

    def replace_src(match: re.Match) -> str:
        original_src = match.group(1)
        img_path = pathlib.Path(original_src)

        # Resolve path relative to the markdown file's directory
        absolute_img_path = (md_file_dir / img_path).resolve()

        if absolute_img_path.is_file():
            filename = absolute_img_path.name
            # Add the absolute path for genanki to find the file
            found_media_in_field.append(str(absolute_img_path))
            # Replace the original src attribute value with just the filename
            tag = match.group(0)
            # Ensure we replace the correct attribute value
            new_tag = tag.replace(f'src="{original_src}"', f'src="{filename}"', 1)
            return new_tag
        else:
            log.warning(
                "Image file not found",
                src=original_src,
                resolved_path=str(absolute_img_path),
                markdown_dir=str(md_file_dir),
            )
            return match.group(0)  # Return the original tag if file not found

    processed_content = IMG_SRC_RE.sub(replace_src, field_content)
    # Return unique paths found in this specific field processing run
    media_files = list(set(found_media_in_field))
    return processed_content, media_files


def find_anki_cards_in_file(
    filepath: pathlib.Path, root_dir: pathlib.Path, model_def: AnkiModelDefinition
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Extracts Anki card data and referenced media files from a Markdown file,
    using the provided model definition for field mapping.
    """
    cards: list[dict[str, Any]] = []
    all_media_for_file: set[str] = set()
    default_deck_name = calculate_deck_name(root_dir, filepath)
    md_dir = filepath.parent
    relative_filepath = str(filepath.relative_to(root_dir))
    log.debug("Processing file", file=relative_filepath)

    # Determine which field should store the source file path
    source_file_field_name = next(
        (f.name for f in model_def.fields if f.name.lower() == "sourcefile"), None
    )
    tags_field_name = (
        model_def.yaml_field_map.get("tags") if model_def.yaml_field_map else None
    )

    try:
        content = filepath.read_text(encoding="utf-8")
        for match_num, match in enumerate(ANKI_BLOCK_RE.finditer(content)):
            yaml_content = match.group(1)
            log.debug(
                "Found anki block", file=relative_filepath, block_num=match_num + 1
            )
            try:
                raw_card_data = yaml.safe_load(yaml_content)
                if not isinstance(raw_card_data, dict):
                    log.warning(
                        "Skipping non-dict anki block",
                        file=relative_filepath,
                        block_num=match_num + 1,
                        content_start=f"{yaml_content[:50]}...",
                    )
                    continue

                # Prepare the fields dictionary based on model_def.yaml_field_map
                card_fields: dict[str, Any] = {}
                card_media: list[str] = []
                card_tags = raw_card_data.get("tags", [])
                processed_ok = True

                for yaml_key, field_name in model_def.yaml_field_map.items():
                    if yaml_key == "tags":
                        continue  # Tags are handled separately

                    field_content_raw = raw_card_data.get(yaml_key)
                    if field_content_raw is None:
                        log.warning(
                            "Missing expected key in anki block",
                            key=yaml_key,
                            field=field_name,
                            file=relative_filepath,
                            block_num=match_num + 1,
                        )
                        processed_ok = False
                        break  # Skip this card if mandatory field is missing

                    # Process content for images
                    field_content_str = str(field_content_raw)
                    processed_content, media = process_field_for_images(
                        field_content_str, md_dir
                    )
                    card_fields[field_name] = processed_content
                    card_media.extend(media)

                if not processed_ok:
                    continue  # Skip card due to missing fields

                # Add source file if the field exists in the model
                if source_file_field_name:
                    card_fields[source_file_field_name] = relative_filepath

                # Add tags if the field exists in the model and yaml_field_map links it
                if tags_field_name and card_tags:
                    # Genanki expects tags as a list, not in fields. Store separately.
                    # If you wanted tags *in a field*, you'd do:
                    # card_fields[tags_field_name] = " ".join(map(str, card_tags))
                    pass  # Tags handled separately by genanki Note

                # Construct the final card dictionary for generate_anki_package
                card_dict = {
                    "fields": card_fields,
                    "tags": card_tags,
                    "deck": raw_card_data.get("deck", default_deck_name),
                    # Include raw q/a for GUID generation consistency if needed, or use fields
                    "guid_basis": f"{card_fields.get(model_def.yaml_field_map.get('q', ''))}|{card_fields.get(model_def.yaml_field_map.get('a', ''))}|{raw_card_data.get('deck', default_deck_name)}|{relative_filepath}",
                }

                cards.append(card_dict)
                all_media_for_file.update(card_media)

            except yaml.YAMLError as e:
                log.warning(
                    "Could not parse YAML in anki block",
                    file=relative_filepath,
                    error=str(e),
                    block_num=match_num + 1,
                    content_start=f"{yaml_content[:50]}...",
                )
            except Exception as e:
                log.warning(
                    "Error processing anki block",
                    file=relative_filepath,
                    error=str(e),
                    block_num=match_num + 1,
                    content_start=f"{yaml_content[:50]}...",
                )

    except Exception as e:
        log.error("Error reading file", file=str(filepath), error=str(e))

    return cards, list(all_media_for_file)


def generate_anki_package(
    card_data_list: list[dict[str, Any]],
    media_files: list[str],
    anki_model: genanki.Model,
    output_filename: str = "output_from_notes.apkg",
) -> None:
    """Generates an .apkg file from extracted card data and media files."""
    decks: dict[str, genanki.Deck] = {}
    # Use a hash of the model name/id for deck ID base to avoid collisions across different models
    deck_id_base = 2000000000 + abs(hash(anki_model.name)) % 500000000

    log.info("Generating Anki package", output_file=output_filename)

    model_field_names = [f["name"] for f in anki_model.fields]

    for card_data in card_data_list:
        deck_name = card_data.get("deck", "Default")
        if deck_name not in decks:
            # Generate stable deck ID based on name
            deck_id = deck_id_base + abs(hash(deck_name)) % 100000000
            decks[deck_name] = genanki.Deck(deck_id, deck_name)
            log.debug("Created deck", name=deck_name, id=deck_id)

        # Ensure fields are in the order defined by the model
        ordered_fields = [
            str(card_data["fields"].get(name, "")) for name in model_field_names
        ]

        # Use a stable note GUID based on content + deck + source file for robustness
        # Use the precalculated guid_basis
        note_guid = genanki.guid_for(card_data["guid_basis"])

        try:
            note = genanki.Note(
                model=anki_model,
                fields=ordered_fields,
                guid=note_guid,
                tags=card_data.get("tags", []),
            )
            decks[deck_name].add_note(note)
        except Exception as e:
            log.error(
                "Failed to create Anki Note",
                guid=note_guid,
                fields=ordered_fields,
                tags=card_data.get("tags"),
                error=str(e),
            )

    if not decks:
        log.warning("No cards found to generate package.")
        return

    # Pass collected *unique* absolute media file paths to genanki.Package
    unique_media_files = sorted(list(set(media_files)))  # Sort for deterministic output
    log.info(f"Found {len(unique_media_files)} unique media files.")
    if unique_media_files:
        log.debug("Media files to include", files=unique_media_files)

    try:
        package = genanki.Package(decks.values(), media_files=unique_media_files)
        package.write_to_file(output_filename)
        log.info(
            "Generated Anki package",
            filename=output_filename,
            card_count=len(card_data_list),
            deck_count=len(decks),
            media_count=len(unique_media_files),
        )
    except Exception as e:
        log.error(
            "Failed to write Anki package", filename=output_filename, error=str(e)
        )
        # Consider re-raising or exiting based on desired behavior


# --- Main Execution ---
def _main(args: CliArgs) -> None:
    """Main script execution function."""

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        log.info("Verbose logging enabled.")

    # --- Load Model ---
    try:
        model_def = load_and_validate_model(args.model_definition.resolve())
        anki_model = create_genanki_model(model_def)
    except (FileNotFoundError, ValueError, ValidationError) as e:
        # Errors already logged by load_and_validate_model
        # Optional: print a final error message before exiting
        print(f"\nError loading model definition: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        log.exception("Unexpected error during model loading.")
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Scan and Process Files ---
    root_path = args.notes_directory.resolve()
    if not root_path.is_dir():
        log.error("Input path is not a valid directory.", path=str(root_path))
        print(
            f"Error: Input path '{root_path}' is not a valid directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    all_cards: list[dict[str, Any]] = []
    all_media: set[str] = set()

    log.info("Scanning for markdown files", directory=str(root_path))
    md_files = list(root_path.rglob("*.md"))
    log.info(f"Found {len(md_files)} markdown files to process.")

    for file_path in md_files:
        resolved_file_path = file_path.resolve()
        try:
            # Pass the validated model definition for field mapping
            file_cards, file_media = find_anki_cards_in_file(
                resolved_file_path, root_path, model_def
            )
            if file_cards:
                log.debug(
                    f"Found {len(file_cards)} cards in file",
                    file=resolved_file_path.relative_to(root_path),
                )
            all_cards.extend(file_cards)
            all_media.update(file_media)
        except Exception as e:
            # Log exception traceback for unexpected errors during file processing
            log.exception(
                "Error processing file", file=str(resolved_file_path), error=str(e)
            )

    # --- Generate Package ---
    if all_cards:
        generate_anki_package(
            all_cards, list(all_media), anki_model, str(args.output_file)
        )
    else:
        log.warning(
            "No valid Anki card definitions found in scanned files.",
            directory=str(root_path),
        )
        print("No valid Anki card definitions found.")


def build_cards():
    # Use tyro.cli to parse arguments and run the main function
    args = tyro.cli(CliArgs)
    _main(args)
