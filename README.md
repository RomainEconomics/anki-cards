# Anki Cards Generator

Transform your markdown notes into Anki flashcard decks automatically! This tool scans your markdown files for special `anki` code blocks and generates `.apkg` files that you can import directly into Anki.

## ✨ Features

- **Markdown-based**: Write flashcards directly in your markdown notes
- **Automatic deck organization**: Creates deck hierarchy based on your directory structure
- **Flexible deck naming**: Optionally include filenames in deck hierarchy
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

# Or install globally the package using uv tool
uv tool install . --compile-bytecode
# if already installed
uv tool install . --reinstall --compile-bytecode

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
```

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

### Advanced Features

**Include images:**

````markdown
```anki
q: What does this diagram show?
a: This shows <img src="diagram.png" alt="Process flow"> the data flow
```
````

**Multiple cards in one file:**

````markdown
# Machine Learning

```anki
q: What is supervised learning?
a: Learning with labeled training data
tags: [ml, supervised]
```
````

```anki
q: What is unsupervised learning?
a: Learning patterns in data without labels
tags: [ml, unsupervised]
```

`````

**Custom deck organization:**
````markdown
```anki
q: What is a neural network?
a: A computing system inspired by biological neural networks
deck: AI::Deep Learning::Basics
```
`````

## 🏗️ Directory Structure & Deck Organization

The tool automatically creates deck hierarchies based on your directory structure:

```md
notes/
├── programming/
│ ├── python/
│ │ └── basics.md → Deck: "notes::programming::python"
│ └── javascript/
│ └── functions.md → Deck: "notes::programming::javascript"
└── science/
└── physics/
└── mechanics.md → Deck: "notes::science::physics"
```

### Including Filenames in Deck Hierarchy

Use the `--include-filename-in-deck` flag to include markdown filenames in the deck hierarchy:

```bash
uv run build-cards --notes-directory notes --include-filename-in-deck
```

This changes the deck organization to include filenames:

```md
notes/
├── programming/
│ ├── python/
│ │ └── basics.md → Deck: "notes::programming::python::basics"
│ └── javascript/
│ └── functions.md → Deck: "notes::programming::javascript::functions"
└── science/
└── physics/
└── mechanics.md → Deck: "notes::science::physics::mechanics"
```

This is particularly useful when you have multiple markdown files in the same directory covering different topics.

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
```

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
  --include-filename-in-deck  Include filename in deck hierarchy (default: false)
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
# Basic usage
uv run build-cards --notes-directory examples/knowledge --output-file my_first_deck.apkg

# With filename in deck hierarchy
uv run build-cards --notes-directory examples/knowledge --include-filename-in-deck --output-file my_first_deck.apkg
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

## 🤖 AI-Assisted Card Generation

Want to quickly generate flashcards from your notes using AI? Here's a system prompt that works well with Claude, ChatGPT, or other AI assistants:

<details>
<summary>📋 Click to expand the system prompt</summary>

````
Your goal is to create a set of Anki flashcards based on the provided context.
You can create as many flashcards as you like, but they should be relevant to the context.
The user is a PHD student in Data Science and is looking to create flashcards for their studies.
Thus, the flashcards should be educational and informative, covering key concepts, formulas, or methods that would be useful for a Data Science expert (e.g., statistics, machine learning, data analysis, etc.).

Each flashcard should have a question (q) and an answer (a) section.

The format should be as follows:

<example>
Q1

```anki
q: |
    What is the formula for the area of a triangle, and what do the variables represent?
a: |
    The area is \(A = \frac{1}{2} b h\), where \(A\) is the area, \(b\) is the base, and \(h\) is the height.
```

Q2

```anki
q: |
    What is the formula for the perimeter (circumference) of a circle of radius \(r\)?
a: The perimeter is \(P = 2 \pi r\).
```

</example>

Things to note:

- never use dollar signs for the latex formulas when writing question-ansers. You must use backslashes (\( \) or \[ \]) for the latex formulas in the flashcards. This is because the Anki software does not support dollar signs for latex.
- only two questions is provided as an example, but you can create as many flashcards as you like.

````

</details>

### How to Use:

1. **Copy the system prompt** above into your AI assistant
2. **Paste your markdown notes** or lecture content as context
3. **Copy the generated flashcards** directly into your markdown files
4. **Run the tool** to generate your Anki deck

The AI will generate properly formatted `anki` blocks that work seamlessly with this tool, including proper LaTeX formatting for mathematical formulas.

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

```

```
