from anki_cards.main import (
    ANKI_BLOCK_RE,
    IMG_SRC_RE,
    calculate_deck_name,
    find_anki_cards_in_file,
    process_field_for_images,
)


class TestRegexPatterns:
    def test_anki_block_regex_basic(self):
        content = """# Test
        
```anki
q: Question
a: Answer
```

More text."""
        matches = list(ANKI_BLOCK_RE.finditer(content))
        assert len(matches) == 1
        assert "q: Question\na: Answer" in matches[0].group(1)

    def test_anki_block_regex_multiple(self):
        content = """```anki
q: First question
a: First answer
```

Some text.

```anki
q: Second question  
a: Second answer
```"""
        matches = list(ANKI_BLOCK_RE.finditer(content))
        assert len(matches) == 2

    def test_anki_block_regex_case_insensitive(self):
        content = """```ANKI
q: Question
a: Answer
```"""
        matches = list(ANKI_BLOCK_RE.finditer(content))
        assert len(matches) == 1

    def test_img_src_regex_local_path(self):
        html = '<img src="diagram.png" alt="test">'
        matches = list(IMG_SRC_RE.finditer(html))
        assert len(matches) == 1
        assert matches[0].group(1) == "diagram.png"

    def test_img_src_regex_excludes_http(self):
        html = '<img src="https://example.com/image.png" alt="test">'
        matches = list(IMG_SRC_RE.finditer(html))
        assert len(matches) == 0

    def test_img_src_regex_excludes_data_uri(self):
        html = '<img src="data:image/png;base64,iVBORw0K..." alt="test">'
        matches = list(IMG_SRC_RE.finditer(html))
        assert len(matches) == 0


class TestCalculateDeckName:
    def test_calculate_deck_name_root_file(self, temp_dir):
        root_dir = temp_dir / "notes"
        root_dir.mkdir()
        filepath = root_dir / "test.md"

        deck_name = calculate_deck_name(root_dir, filepath)
        assert deck_name == "notes"

    def test_calculate_deck_name_nested_file(self, temp_dir):
        root_dir = temp_dir / "notes"
        subdir = root_dir / "programming" / "python"
        subdir.mkdir(parents=True)
        filepath = subdir / "test.md"

        deck_name = calculate_deck_name(root_dir, filepath)
        assert deck_name == "notes::programming::python"

    def test_calculate_deck_name_single_subdir(self, temp_dir):
        root_dir = temp_dir / "knowledge"
        subdir = root_dir / "math"
        subdir.mkdir(parents=True)
        filepath = subdir / "algebra.md"

        deck_name = calculate_deck_name(root_dir, filepath)
        assert deck_name == "knowledge::math"

    def test_calculate_deck_name_with_filename_root_file(self, temp_dir):
        root_dir = temp_dir / "notes"
        root_dir.mkdir()
        filepath = root_dir / "test.md"

        deck_name = calculate_deck_name(root_dir, filepath, include_filename=True)
        assert deck_name == "notes::test"

    def test_calculate_deck_name_with_filename_nested_file(self, temp_dir):
        root_dir = temp_dir / "notes"
        subdir = root_dir / "programming" / "python"
        subdir.mkdir(parents=True)
        filepath = subdir / "basics.md"

        deck_name = calculate_deck_name(root_dir, filepath, include_filename=True)
        assert deck_name == "notes::programming::python::basics"

    def test_calculate_deck_name_with_filename_complex_name(self, temp_dir):
        root_dir = temp_dir / "knowledge"
        subdir = root_dir / "math"
        subdir.mkdir(parents=True)
        filepath = subdir / "linear-algebra-fundamentals.md"

        deck_name = calculate_deck_name(root_dir, filepath, include_filename=True)
        assert deck_name == "knowledge::math::linear-algebra-fundamentals"


class TestProcessFieldForImages:
    def test_process_field_no_images(self, temp_dir):
        content = "Just some text without images"
        processed, media = process_field_for_images(content, temp_dir)

        assert processed == content
        assert media == []

    def test_process_field_with_existing_image(self, temp_dir):
        # Create test image file
        image_file = temp_dir / "test.png"
        image_file.write_text("fake image content")

        content = 'This has an <img src="test.png" alt="test"> image'
        processed, media = process_field_for_images(content, temp_dir)

        assert 'src="test.png"' in processed
        assert str(image_file) in media
        assert len(media) == 1

    def test_process_field_with_nonexistent_image(self, temp_dir):
        content = 'This has an <img src="missing.png" alt="test"> image'
        processed, media = process_field_for_images(content, temp_dir)

        # Should leave content unchanged and not add to media
        assert processed == content
        assert media == []

    def test_process_field_with_relative_path_image(self, temp_dir):
        # Create nested directory structure
        subdir = temp_dir / "images"
        subdir.mkdir()
        image_file = subdir / "diagram.png"
        image_file.write_text("fake image")

        content = 'See <img src="images/diagram.png" alt="diagram"> for details'
        processed, media = process_field_for_images(content, temp_dir)

        assert 'src="diagram.png"' in processed  # Should be just filename
        assert str(image_file) in media

    def test_process_field_multiple_images(self, temp_dir):
        # Create multiple test images
        for i in range(3):
            (temp_dir / f"image{i}.png").write_text(f"image {i}")

        content = """Multiple images: 
        <img src="image0.png" alt="first">
        <img src="image1.png" alt="second">  
        <img src="image2.png" alt="third">"""

        processed, media = process_field_for_images(content, temp_dir)

        assert len(media) == 3
        assert all('src="image' in processed for i in range(3))


class TestFindAnkiCardsInFile:
    def test_find_cards_basic(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        files = {
            "test.md": """# Test Notes

```anki
q: What is Python?
a: A programming language
tags: [python]
```
"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "test.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition
        )

        assert len(cards) == 1
        card = cards[0]
        assert card["fields"]["Question"] == "What is Python?"
        assert card["fields"]["Answer"] == "A programming language"
        assert card["tags"] == ["python"]
        assert "test.md" in card["fields"]["SourceFile"]

    def test_find_cards_multiple(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        files = {
            "notes.md": """# Multiple Cards

```anki
q: Question 1
a: Answer 1
```

Some text between cards.

```anki
q: Question 2
a: Answer 2
deck: Custom::Deck
```
"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "notes.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition
        )

        assert len(cards) == 2
        assert cards[0]["fields"]["Question"] == "Question 1"
        assert cards[1]["fields"]["Question"] == "Question 2"
        assert cards[1]["deck"] == "Custom::Deck"

    def test_find_cards_with_missing_required_field(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        files = {
            "incomplete.md": """# Incomplete Card

```anki
q: Question without answer
tags: [incomplete]
```
"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "incomplete.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition
        )

        # Should skip incomplete cards
        assert len(cards) == 0

    def test_find_cards_invalid_yaml(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        files = {
            "invalid.md": """# Invalid YAML

```anki
q: Valid question
a: Valid answer
invalid: yaml: structure: [
```
"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "invalid.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition
        )

        # Should skip invalid YAML blocks
        assert len(cards) == 0

    def test_find_cards_non_dict_yaml(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        files = {
            "non_dict.md": """# Non-dict YAML

```anki
- q: This is a list
- a: Not a dict
```
"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "non_dict.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition
        )

        # Should skip non-dict blocks
        assert len(cards) == 0

    def test_find_cards_with_images(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        # Create test image
        (temp_dir / "diagram.png").write_text("fake image")

        files = {
            "visual.md": """# Visual Notes

```anki
q: What does this show?
a: It shows <img src="diagram.png" alt="diagram"> the process
```
"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "visual.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition
        )

        assert len(cards) == 1
        assert len(media) == 1
        assert str(temp_dir / "diagram.png") in media
        # Image src should be updated to just filename
        assert 'src="diagram.png"' in cards[0]["fields"]["Answer"]

    def test_find_cards_deck_hierarchy(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        # Create nested directory structure
        nested_dir = temp_dir / "knowledge" / "programming" / "python"
        nested_dir.mkdir(parents=True)

        files = {
            "knowledge/programming/python/basics.md": """```anki
q: What is a variable?
a: A storage location
```"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "knowledge" / "programming" / "python" / "basics.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition
        )

        # Should use directory hierarchy as default deck name
        expected_deck = f"{temp_dir.name}::knowledge::programming::python"
        assert cards[0]["deck"] == expected_deck

    def test_find_cards_file_not_found(self, temp_dir, sample_model_definition):
        nonexistent_file = temp_dir / "nonexistent.md"

        cards, media = find_anki_cards_in_file(
            nonexistent_file, temp_dir, sample_model_definition
        )

        # Should handle gracefully and return empty results
        assert cards == []
        assert media == []

    def test_find_cards_deck_hierarchy_with_filename(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        # Create nested directory structure
        nested_dir = temp_dir / "knowledge" / "programming" / "python"
        nested_dir.mkdir(parents=True)

        files = {
            "knowledge/programming/python/basics.md": """```anki
q: What is a variable?
a: A storage location
```"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "knowledge" / "programming" / "python" / "basics.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition, include_filename_in_deck=True
        )

        # Should include filename in the deck hierarchy
        expected_deck = f"{temp_dir.name}::knowledge::programming::python::basics"
        assert cards[0]["deck"] == expected_deck

    def test_find_cards_deck_hierarchy_with_filename_root_file(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        files = {
            "notes.md": """```anki
q: Root level question
a: Root level answer
```"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "notes.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition, include_filename_in_deck=True
        )

        # Should include filename even for root level file
        expected_deck = f"{temp_dir.name}::notes"
        assert cards[0]["deck"] == expected_deck

    def test_find_cards_deck_hierarchy_with_filename_custom_deck(
        self, temp_dir, sample_model_definition, create_test_files
    ):
        files = {
            "notes.md": """```anki
q: Custom deck question
a: Custom deck answer
deck: MyCustom::Deck::Name
```"""
        }
        test_dir = create_test_files(files)
        test_file = test_dir / "notes.md"

        cards, media = find_anki_cards_in_file(
            test_file, test_dir, sample_model_definition, include_filename_in_deck=True
        )

        # Custom deck should override the filename hierarchy
        assert cards[0]["deck"] == "MyCustom::Deck::Name"

