import pytest

from anki_cards.cli import CliArgs
from anki_cards.main import _main, generate_anki_package


class TestGenerateAnkiPackage:
    def test_generate_package_basic(self, temp_dir, sample_model_definition):
        """Test basic package generation with simple card data."""
        from anki_cards.model import create_genanki_model

        card_data = [
            {
                "fields": {
                    "Question": "What is Python?",
                    "Answer": "A programming language",
                    "SourceFile": "test.md",
                },
                "tags": ["python"],
                "deck": "Test Deck",
                "guid_basis": "What is Python?|A programming language|Test Deck|test.md",
            }
        ]

        anki_model = create_genanki_model(sample_model_definition)
        output_path = temp_dir / "test_output.apkg"

        generate_anki_package(card_data, [], anki_model, str(output_path))

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_generate_package_multiple_decks(self, temp_dir, sample_model_definition):
        """Test package generation with multiple decks."""
        from anki_cards.model import create_genanki_model

        card_data = [
            {
                "fields": {"Question": "Q1", "Answer": "A1", "SourceFile": "test1.md"},
                "tags": [],
                "deck": "Deck1",
                "guid_basis": "Q1|A1|Deck1|test1.md",
            },
            {
                "fields": {"Question": "Q2", "Answer": "A2", "SourceFile": "test2.md"},
                "tags": [],
                "deck": "Deck2",
                "guid_basis": "Q2|A2|Deck2|test2.md",
            },
        ]

        anki_model = create_genanki_model(sample_model_definition)
        output_path = temp_dir / "multi_deck.apkg"

        generate_anki_package(card_data, [], anki_model, str(output_path))

        assert output_path.exists()

    def test_generate_package_with_media(self, temp_dir, sample_model_definition):
        """Test package generation with media files."""
        from anki_cards.model import create_genanki_model

        # Create test media file
        media_file = temp_dir / "test_image.png"
        media_file.write_text("fake image content")

        card_data = [
            {
                "fields": {
                    "Question": "What does this show?",
                    "Answer": '<img src="test_image.png">',
                    "SourceFile": "visual.md",
                },
                "tags": [],
                "deck": "Visual Deck",
                "guid_basis": 'What does this show?|<img src="test_image.png">|Visual Deck|visual.md',
            }
        ]

        anki_model = create_genanki_model(sample_model_definition)
        output_path = temp_dir / "with_media.apkg"

        generate_anki_package(
            card_data, [str(media_file)], anki_model, str(output_path)
        )

        assert output_path.exists()

    def test_generate_package_no_cards(self, temp_dir, sample_model_definition):
        """Test package generation with no cards (should handle gracefully)."""
        from anki_cards.model import create_genanki_model

        anki_model = create_genanki_model(sample_model_definition)
        output_path = temp_dir / "empty.apkg"

        generate_anki_package([], [], anki_model, str(output_path))

        # Should not create file when no cards
        assert not output_path.exists()


class TestMainFunction:
    def test_main_function_basic_workflow(self, temp_dir, create_test_files):
        """Test the main function with a complete workflow."""
        # Create model definition file
        model_yaml = """
id: 1234567890
name: "Integration Test Model"
fields:
  - name: "Question"
  - name: "Answer"
  - name: "SourceFile"
templates:
  - name: "Card 1"
    qfmt: "{{Question}}"
    afmt: "{{Answer}}"
yaml_field_map:
  q: "Question"
  a: "Answer"
"""

        # Create test files
        files = {
            "model.yaml": model_yaml,
            "notes/python.md": """# Python Notes

```anki
q: What is Python?
a: A programming language
tags: [python, programming]
```

```anki
q: Who created Python?
a: Guido van Rossum
```
""",
            "notes/web/flask.md": """# Flask Notes

```anki
q: What is Flask?
a: A web framework
deck: Web::Frameworks
```
""",
        }

        test_dir = create_test_files(files)

        # Set up arguments
        args = CliArgs(
            notes_directory=test_dir / "notes",
            model_definition=test_dir / "model.yaml",
            output_file=test_dir / "output.apkg",
            verbose=False,
        )

        # Run main function
        _main(args)

        # Verify output file was created
        assert (test_dir / "output.apkg").exists()
        assert (test_dir / "output.apkg").stat().st_size > 0

    def test_main_function_nonexistent_directory(self, temp_dir):
        """Test main function with nonexistent notes directory."""
        # Create minimal model file
        model_file = temp_dir / "model.yaml"
        model_file.write_text("""
id: 123
name: "Test"
fields:
  - name: "Question"
  - name: "Answer"
templates:
  - name: "Card 1"
    qfmt: "{{Question}}"
    afmt: "{{Answer}}"
""")

        args = CliArgs(
            notes_directory=temp_dir / "nonexistent",
            model_definition=model_file,
            output_file=temp_dir / "output.apkg",
        )

        with pytest.raises(SystemExit):
            _main(args)

    def test_main_function_invalid_model_file(self, temp_dir, create_test_files):
        """Test main function with invalid model definition."""
        files = {
            "invalid_model.yaml": "invalid: yaml: content",
            "notes/test.md": """```anki
q: Test
a: Test
```""",
        }

        test_dir = create_test_files(files)

        args = CliArgs(
            notes_directory=test_dir / "notes",
            model_definition=test_dir / "invalid_model.yaml",
            output_file=test_dir / "output.apkg",
        )

        with pytest.raises(SystemExit):
            _main(args)

    def test_main_function_no_cards_found(self, temp_dir, create_test_files):
        """Test main function when no valid cards are found."""
        model_yaml = """
id: 123
name: "Test Model"
fields:
  - name: "Question"
  - name: "Answer"
templates:
  - name: "Card 1"
    qfmt: "{{Question}}"
    afmt: "{{Answer}}"
"""

        files = {
            "model.yaml": model_yaml,
            "notes/empty.md": "# No Cards Here\n\nJust regular markdown content.",
            "notes/invalid.md": """```anki
incomplete: card without required fields
```""",
        }

        test_dir = create_test_files(files)

        args = CliArgs(
            notes_directory=test_dir / "notes",
            model_definition=test_dir / "model.yaml",
            output_file=test_dir / "output.apkg",
        )

        # Should run without error but produce no output file
        _main(args)
        assert not (test_dir / "output.apkg").exists()

    def test_main_function_with_verbose(self, temp_dir, create_test_files):
        """Test main function with verbose logging enabled."""
        model_yaml = """
id: 123
name: "Verbose Test Model"
fields:
  - name: "Question"
  - name: "Answer"
templates:
  - name: "Card 1"
    qfmt: "{{Question}}"
    afmt: "{{Answer}}"
"""

        files = {
            "model.yaml": model_yaml,
            "notes/test.md": """```anki
q: Verbose test
a: Testing verbose mode
```""",
        }

        test_dir = create_test_files(files)

        args = CliArgs(
            notes_directory=test_dir / "notes",
            model_definition=test_dir / "model.yaml",
            output_file=test_dir / "verbose_output.apkg",
            verbose=True,
        )

        # Should run successfully with verbose logging
        _main(args)
        assert (test_dir / "verbose_output.apkg").exists()

    def test_main_function_with_filename_in_deck(self, temp_dir, create_test_files):
        """Test main function with include_filename_in_deck option enabled."""
        model_yaml = """
id: 123
name: "Filename Test Model"
fields:
  - name: "Question"
  - name: "Answer"
  - name: "SourceFile"
templates:
  - name: "Card 1"
    qfmt: "{{Question}}"
    afmt: "{{Answer}}<br><small>{{SourceFile}}</small>"
yaml_field_map:
  q: "Question"
  a: "Answer"
"""

        files = {
            "model.yaml": model_yaml,
            "notes/programming/python-basics.md": """# Python Basics

```anki
q: What is a variable in Python?
a: A storage location with a name
tags: [python, basics]
```

```anki
q: How do you create a list in Python?
a: Using square brackets: [1, 2, 3]
```
""",
            "notes/math/algebra.md": """# Algebra

```anki
q: What is the quadratic formula?
a: x = (-b ± √(b²-4ac)) / 2a
```
""",
        }

        test_dir = create_test_files(files)

        args = CliArgs(
            notes_directory=test_dir / "notes",
            model_definition=test_dir / "model.yaml", 
            output_file=test_dir / "filename_test.apkg",
            include_filename_in_deck=True,
        )

        # Run main function
        _main(args)

        # Verify output file was created
        assert (test_dir / "filename_test.apkg").exists()
        assert (test_dir / "filename_test.apkg").stat().st_size > 0

        # The test verifies the package is created; deck names would be tested
        # through the unit tests for calculate_deck_name and find_anki_cards_in_file

