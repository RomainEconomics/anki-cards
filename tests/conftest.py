import pathlib
import tempfile
from typing import Generator

import pytest

from anki_cards.model_from_yaml import AnkiModelDefinition


@pytest.fixture
def temp_dir() -> Generator[pathlib.Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield pathlib.Path(tmp_dir)


@pytest.fixture
def sample_model_definition() -> AnkiModelDefinition:
    """Sample valid Anki model definition for testing."""
    return AnkiModelDefinition(
        id=1234567890,
        name="Test Model",
        fields=[
            {"name": "Question"},
            {"name": "Answer"},
            {"name": "SourceFile"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Question}}",
                "afmt": "{{Question}}<hr>{{Answer}}",
            }
        ],
        yaml_field_map={"q": "Question", "a": "Answer"},
    )


@pytest.fixture
def sample_model_yaml() -> str:
    """Sample YAML content for model definition."""
    return """
id: 1234567890
name: "Test Model"
fields:
  - name: "Question"
  - name: "Answer"
  - name: "SourceFile"
templates:
  - name: "Card 1"
    qfmt: "{{Question}}"
    afmt: "{{Question}}<hr>{{Answer}}"
yaml_field_map:
  q: "Question"
  a: "Answer"
css: |
  .card { font-family: arial; }
"""


@pytest.fixture
def sample_markdown_with_cards() -> str:
    """Sample markdown content with anki blocks."""
    return """# Test Notes

Some text before cards.

```anki
q: What is Python?
a: A programming language
tags: [python, programming]
```

More text.

```anki
q: What is Flask?
a: A web framework for Python
deck: Web::Frameworks
```

End of file.
"""


@pytest.fixture
def sample_markdown_with_images() -> str:
    """Sample markdown with image references."""
    return """# Visual Notes

```anki
q: What does this diagram show?
a: It shows <img src="diagram.png" alt="diagram"> the process flow
tags: [visual]
```
"""


@pytest.fixture
def create_test_files(temp_dir: pathlib.Path):
    """Factory fixture to create test files in temp directory."""

    def _create_files(files: dict[str, str]) -> pathlib.Path:
        """Create files with given content in temp directory.

        Args:
            files: Dict mapping relative paths to file contents

        Returns:
            Path to the temp directory
        """
        for file_path, content in files.items():
            full_path = temp_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
        return temp_dir

    return _create_files

