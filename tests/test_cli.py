import pathlib

import pytest

from anki_cards.cli import CliArgs


class TestCliArgs:
    def test_cli_args_defaults(self):
        """Test that CliArgs has correct default values."""
        args = CliArgs(notes_directory=pathlib.Path("/test"))
        
        assert args.notes_directory == pathlib.Path("/test")
        assert args.output_file == pathlib.Path("notes_deck.apkg")
        assert args.model_definition == pathlib.Path("default_anki_model.yaml")
        assert args.verbose is False
        assert args.include_filename_in_deck is False

    def test_cli_args_all_parameters(self):
        """Test CliArgs with all parameters specified."""
        args = CliArgs(
            notes_directory=pathlib.Path("/my/notes"),
            output_file=pathlib.Path("/output/my_deck.apkg"),
            model_definition=pathlib.Path("/models/custom_model.yaml"),
            verbose=True,
            include_filename_in_deck=True
        )
        
        assert args.notes_directory == pathlib.Path("/my/notes")
        assert args.output_file == pathlib.Path("/output/my_deck.apkg")
        assert args.model_definition == pathlib.Path("/models/custom_model.yaml")
        assert args.verbose is True
        assert args.include_filename_in_deck is True

    def test_cli_args_pathlib_conversion(self):
        """Test that string paths are properly converted to pathlib.Path objects."""
        args = CliArgs(
            notes_directory=pathlib.Path("./notes"),
            output_file=pathlib.Path("deck.apkg"),
            model_definition=pathlib.Path("model.yaml")
        )
        
        assert isinstance(args.notes_directory, pathlib.Path)
        assert isinstance(args.output_file, pathlib.Path)
        assert isinstance(args.model_definition, pathlib.Path)

    def test_cli_args_include_filename_in_deck_option(self):
        """Test the include_filename_in_deck option works correctly."""
        # Test with default (False)
        args_default = CliArgs(notes_directory=pathlib.Path("/test"))
        assert args_default.include_filename_in_deck is False
        
        # Test with explicit True
        args_enabled = CliArgs(
            notes_directory=pathlib.Path("/test"),
            include_filename_in_deck=True
        )
        assert args_enabled.include_filename_in_deck is True
        
        # Test with explicit False
        args_disabled = CliArgs(
            notes_directory=pathlib.Path("/test"),
            include_filename_in_deck=False
        )
        assert args_disabled.include_filename_in_deck is False