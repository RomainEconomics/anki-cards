# Anki Cards Generator

Transform your markdown notes into Anki flashcard decks automatically! This tool scans your markdown files for special `anki` code blocks and generates `.apkg` files that you can import directly into Anki.

## ✨ Features

- **Markdown-based**: Write flashcards directly in your markdown notes
- **Automatic deck organization**: Creates deck hierarchy based on your directory structure
- **Image support**: Automatically includes images referenced in your cards
- **Customizable card templates**: Define your own Anki note types with YAML
- **Batch processing**: Process entire directories of notes at once
- **Source tracking**: Automatically tracks which file each card came from

## 🚀 Quick Start

### 1. Install the tool

```bash
# Clone the repository
git clone <repository-url>
cd anki-cards

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### 2. Create your first flashcards

Create a markdown file with `anki` blocks:

````markdown
# Python Basics

Some notes about Python programming.

```anki
q: What is Python?
a: A high-level programming language known for its simplicity and readability
tags: [python, programming, basics]
```
````

More notes here...

```anki
q: Who created Python?
a: Guido van Rossum
deck: Python::History
```

````

### 3. Generate your Anki deck

```bash
uv run build-cards --notes-directory /path/to/your/notes
````

This creates `notes_deck.apkg` that you can import into Anki!

## 📝 Writing Flashcards

### Basic Card Format

Flashcards are defined using YAML inside ````anki` code blocks:

````markdown
```anki
q: Your question here
a: Your answer here
tags: [tag1, tag2]           # Optional
deck: Custom::Deck::Name     # Optional, defaults to directory structure
```
````

````

### Advanced Features

**Include images:**
```markdown
```anki
q: What does this diagram show?
a: This shows <img src="diagram.png" alt="Process flow"> the data flow
````

````

**Multiple cards in one file:**
```markdown
# Machine Learning

```anki
q: What is supervised learning?
a: Learning with labeled training data
tags: [ml, supervised]
````

```anki
q: What is unsupervised learning?
a: Learning patterns in data without labels
tags: [ml, unsupervised]
```

````

**Custom deck organization:**
```markdown
```anki
q: What is a neural network?
a: A computing system inspired by biological neural networks
deck: AI::Deep Learning::Basics
````

```

## 🏗️ Directory Structure & Deck Organization

The tool automatically creates deck hierarchies based on your directory structure:

```

notes/
├── programming/
│ ├── python/
│ │ └── basics.md → Deck: "notes::programming::python"
│ └── javascript/
│ └── functions.md → Deck: "notes::programming::javascript"
└── science/
└── physics/
└── mechanics.md → Deck: "notes::science::physics"

````

## ⚙️ Configuration

### Custom Card Templates

Create a YAML file to define your card templates:

```yaml
# my_model.yaml
id: 1234567890
name: "My Custom Card Type"
fields:
  - name: "Question"
  - name: "Answer"
  - name: "SourceFile"
  - name: "Tags"
templates:
  - name: "Card 1"
    qfmt: "{{Question}}<br><small>Source: {{SourceFile}}</small>"
    afmt: "{{FrontSide}}<hr>{{Answer}}"
yaml_field_map:
  q: "Question"
  a: "Answer"
  tags: "Tags"
css: |
  .card {
    font-family: Arial;
    font-size: 20px;
    text-align: center;
  }
````

Use it with:

```bash
uv run build-cards --notes-directory notes --model-definition my_model.yaml
```

## 📋 Command Line Options

```bash
uv run build-cards --notes-directory DIRECTORY [OPTIONS]

Arguments:
  DIRECTORY                    Directory to scan for .md files

Options:
  --output-file FILE          Output .apkg file (default: notes_deck.apkg)
  --model-definition FILE     YAML model definition (default: default_anki_model.yaml)
  --verbose                   Enable verbose logging
  --help                      Show help message
```

## 📁 Examples

The `examples/` directory contains:

- Sample markdown files with anki blocks
- A default model definition
- Generated deck examples

Try it out:

```bash
uv run build-cards --notes-directory examples/knowledge --output-file my_first_deck.apkg
```

## 🧪 Development

### Running Tests

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=anki_cards

# Run specific test
uv run pytest tests/test_main.py -v
```

### Project Structure

```
src/anki_cards/
├── main.py              # Core processing logic
├── cli.py               # Command line interface
├── model_from_yaml.py   # YAML model validation
└── model.py             # Anki model creation

tests/                   # Comprehensive test suite
examples/                # Sample files and usage examples
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `uv run pytest`
5. Submit a pull request

## ❓ Troubleshooting

**No cards found?**

- Check that your markdown files contain valid ````anki` blocks
- Ensure YAML syntax is correct (proper indentation, colons after keys)
- Use `--verbose` flag to see detailed processing information

**Images not appearing?**

- Make sure image files exist relative to your markdown files
- Only local images are supported (not HTTP URLs)
- Supported formats: PNG, JPG, GIF, SVG

**Import issues in Anki?**

- Ensure your model definition has unique `id`
- Check that all template fields are properly defined
- Verify the `.apkg` file was generated without errors

