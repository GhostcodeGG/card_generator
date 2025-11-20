# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Card Generator is a Python project that creates randomized Magic: The Gathering-style cards with deterministic seeds. The system combines data models, randomized generation logic, and a Pillow-based rendering pipeline to produce printable card images in PNG or PDF format.

## Commands

### Running the Generator

Generate a single card:
```bash
python -m card_generator.cli --output output
```

Generate multiple deterministic cards:
```bash
python -m card_generator.cli --seed 10 --count 3 --format pdf --output output
```

### Testing

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_generation.py
pytest tests/test_rendering.py
```

Run a single test:
```bash
pytest tests/test_generation.py::test_seed_reproducibility
```

### Environment Setup

Create virtual environment and install dependencies:
```bash
python -m venv .venv
```

On Windows:
```bash
.venv\Scripts\activate
```

On Unix/macOS:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install pillow pytest
```

## Architecture

### Module Organization

The codebase follows a clean separation of concerns across four main modules:

- **data_models.py**: Defines core data structures (`Card`, `ManaCost`, `CardColor`) with validation logic
- **generator.py**: Contains `CardFactory` for randomized card creation and `ArtProvider` for placeholder art generation
- **renderer.py**: Houses `CardRenderer` that converts `Card` objects into styled images using Pillow
- **cli.py**: Command-line interface that orchestrates the generation and export workflow

### Data Flow

1. CLI parses arguments and instantiates `CardFactory` and `CardRenderer`
2. `CardFactory.create_card(seed)` produces a `Card` object:
   - Selects random color identity weighted toward mono-color
   - Builds mana cost based on selected colors
   - Chooses type line (70% creature, 30% non-creature)
   - Samples abilities from color-specific ability pools
   - Generates name from prefix/suffix combinations
   - Fetches placeholder art via `ArtProvider`
3. `CardRenderer.render(card)` creates a layered Pillow image:
   - Applies color-specific palette based on primary color
   - Draws base canvas with rounded borders and shadows
   - Renders header with name and mana cost gem
   - Draws art area with gradient placeholder
   - Renders type bar, rules box with wrapped text, and footer with P/T
4. `CardRenderer.export(card, path, fmt)` saves the image as PNG or PDF

### Key Design Patterns

**Color Identity System**: Cards have a `color_identity` set that drives both mechanical choices (ability pools) and visual rendering (palette selection). The `normalize_color_identity` function ensures colorless is only used when no other colors are present.

**Deterministic Randomization**: All random choices use `random.Random(seed)` to ensure the same seed always produces identical cards, enabling reproducible generation and testing.

**Art Provider Hook**: `ArtProvider.request_ai_art()` is a placeholder method designed for future integration with AI image generation services. Currently, `fetch()` generates tinted placeholder images using the seed for deterministic variety.

**Palette-Based Rendering**: The renderer uses a palette dictionary keyed by color (`r`, `u`, `g`, `w`, `b`, `c`, `neutral`) containing named color tuples (`base`, `accent`, `surface`, `text_on_dark`, etc.). This allows consistent styling within each color while maintaining visual distinction between colors.

**Text Wrapping Algorithm**: The `_wrap_text` function in renderer.py uses a two-pass approach: first using `textwrap` for rough line breaks, then measuring actual pixel width with the font to ensure text fits within the specified max_width. It supports prefixes for bullet points with continuation indentation.

## Testing Notes

- `test_generation.py` validates card creation and deterministic behavior
- `test_rendering.py` requires Pillow and is skipped gracefully if unavailable
- Use `tmp_path` fixture for testing file outputs
- The rendering tests verify export paths and file format but don't validate visual output

## Important Conventions

- All modules use `from __future__ import annotations` for forward-compatible type hints
- Pillow imports are wrapped in try/except with graceful fallbacks or clear error messages
- Card validation happens via `Card.validate()` which should be called after construction
- Type lines for creatures must include "Creature" to trigger power/toughness rendering
- Art files are cached in `tempfile.gettempdir()/card_generator_art` by default
