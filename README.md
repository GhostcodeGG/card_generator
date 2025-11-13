# Card Generator

This project creates randomized Magic: The Gathering–style cards with deterministic seeds and a simple rendering pipeline. It includes:

- Data models for card attributes such as color identity, mana cost, type line, abilities, and power/toughness.
- A factory that assembles balanced cards while respecting color-specific ability pools.
- Rendering helpers powered by Pillow that combine text and artwork into a printable layout.
- A command-line interface to export generated cards as PNG or PDF files.

## Project structure

```
card_generator/
├── README.md
├── src/
│   └── card_generator/
│       ├── __init__.py
│       ├── cli.py
│       ├── data_models.py
│       ├── generator.py
│       └── renderer.py
└── tests/
    ├── test_generation.py
    └── test_rendering.py
```

## Installation

Create a virtual environment and install the dependencies:

```
python -m venv .venv
source .venv/bin/activate
pip install pillow pytest
```

## Usage

Generate a single card and export it as a PNG:

```
python -m card_generator.cli --output output
```

Generate three deterministic cards in PDF format:

```
python -m card_generator.cli --seed 10 --count 3 --format pdf --output output
```

Each invocation prints the card description and saves the rendered artwork in the chosen directory. Art
assets are generated dynamically so the repository contains no binary templates.

## Tests

Run the automated test suite with:

```
pytest
```

The rendering tests require Pillow. If Pillow is not available the rendering suite is skipped with a helpful message.
