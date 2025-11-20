# AI Card Generator

A powerful Python tool that creates **AI-generated Magic: The Gathering-style cards** with authentic MTG styling, AI-generated artwork, and intelligent card balancing.

**100% AUTHENTIC MTG VISUALS NOW AVAILABLE!**

Choose your rendering method:

**✨ Template-Based Rendering (100% Authentic - RECOMMENDED)**
- Uses community blank MTG card templates
- Overlays your AI-generated content on authentic frames
- Indistinguishable from real MTG cards
- Requires one-time template download (see [TEMPLATE_SETUP.md](TEMPLATE_SETUP.md))

**⚡ Programmatic Rendering (85% Authentic - Built-in)**
- No downloads required, works immediately
- Sharp black borders, vibrant colors, proper proportions
- Actual artwork display (no placeholder gradients)
- Great for quick generation and testing

## Features

✨ **Fully Customizable Card Generation**
- Choose card name, colors, type, abilities, power/toughness
- Or let the AI generate everything randomly
- Deterministic seed-based generation for reproducibility

🎨 **AI-Powered Art Generation**
- Integrates with OpenAI's DALL-E 3 for card artwork
- Automatically generates detailed prompts based on card attributes
- Falls back to placeholder art if AI is unavailable

🖼️ **Professional Card Rendering**
- Authentic MTG-style card layout and borders
- Color-accurate palettes for each mana color
- Actual mana symbol graphics (not just text)
- Flavor text with visual separator
- Artist credit and set information
- Legal text footer

⚖️ **Intelligent Card Balancing**
- Automatically calculates mana costs based on power, toughness, and abilities
- Keyword ability valuation system
- Balanced mana distribution between generic and colored costs

🤖 **AI Flavor Text Generation**
- GPT-powered flavor text that matches card theme
- Falls back to template-based generation
- Contextual and atmospheric writing

## Project Structure

```
card_generator/
├── README.md
├── requirements.txt
├── src/
│   └── card_generator/
│       ├── __init__.py
│       ├── cli.py          # Command-line interface
│       ├── data_models.py  # Card data structures
│       ├── generator.py    # Card generation & AI integration
│       ├── renderer.py     # Card image rendering
│       └── mana_symbols.py # Mana symbol graphics
└── tests/
    ├── test_generation.py
    └── test_rendering.py
```

## Installation

### 1. Create and activate virtual environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure AI (Optional but Recommended)

For AI-generated art and flavor text, set your OpenAI API key:

**Windows:**
```bash
set OPENAI_API_KEY=your-api-key-here
```

**macOS/Linux:**
```bash
export OPENAI_API_KEY=your-api-key-here
```

## Usage

All commands should be run from the `src/` directory:

```bash
cd src
```

### Basic Examples

**Generate a random card:**
```bash
python -m card_generator.cli --output ../output
```

**Generate with AI art and flavor text:**
```bash
python -m card_generator.cli --output ../output --use-ai-art
```

**Create a custom card:**
```bash
python -m card_generator.cli --output ../output \
  --name "Lightning Dragon" \
  --colors R \
  --type "Creature — Dragon" \
  --power 5 \
  --toughness 5 \
  --use-ai-art
```

**Generate multiple themed cards:**
```bash
python -m card_generator.cli --output ../output \
  --seed 42 \
  --count 5 \
  --colors WU \
  --concept "ancient sky guardian angel" \
  --use-ai-art
```

### Command-Line Options

```
--seed SEED              Seed for deterministic generation
--count COUNT            Number of cards to generate
--output OUTPUT          Directory where cards are saved
--format {png,pdf}       Export format (default: png)
--name NAME             Custom card name
--colors COLORS         Color identity (R/U/B/G/W/C)
--type TYPE             Card type (Creature, Instant, Sorcery, etc.)
--concept CONCEPT       Theme for AI art generation
--abilities ABILITIES   Custom abilities (space-separated)
--power POWER           Creature power
--toughness TOUGHNESS   Creature toughness
--use-ai-art            Enable AI art generation
```

### Color Codes

- `W` = White
- `U` = Blue
- `B` = Black
- `R` = Red
- `G` = Green
- `C` = Colorless

**Examples:**
- `--colors R` = Mono-red
- `--colors WU` = White-blue (Azorius)
- `--colors BGR` = Black-green-red (Jund)

## Examples

### Create a Red Dragon
```bash
python -m card_generator.cli --output ../output \
  --name "Inferno Drake" \
  --colors R \
  --type "Creature — Dragon" \
  --concept "fire-breathing dragon soaring over volcanic mountains" \
  --power 6 \
  --toughness 4 \
  --use-ai-art
```

### Create a Blue Instant Spell
```bash
python -m card_generator.cli --output ../output \
  --name "Counterspell" \
  --colors U \
  --type Instant \
  --abilities "Counter target spell" \
  --use-ai-art
```

### Generate Random Playset
```bash
python -m card_generator.cli --output ../output \
  --seed 123 \
  --count 4 \
  --colors G \
  --use-ai-art
```

## AI Integration Details

### Image Generation
- Uses OpenAI DALL-E 3 API
- Generates 1024x1024 images
- Auto-caches generated images
- Detailed prompts include color theme, card type, and concept

### Flavor Text Generation
- Uses GPT-3.5-turbo
- Contextual based on card name, type, colors, and abilities
- Atmospheric and concise (under 120 characters)
- Template-based fallback when AI unavailable

## Card Balancing System

The generator automatically balances mana costs based on:

**Creature Stats:**
- Base value: `(Power + Toughness) / 2`

**Abilities:**
- Keywords: 1-2 mana value each
- Draw effects: +2
- Damage effects: +2
- Destroy effects: +3
- Counter spells: +3
- Token generation: +2

**Example:** A 5/5 creature with Trample and Haste would have:
- Base: (5+5)/2 = 5
- Trample: +1
- Haste: +1
- **Total: 7 mana**

## Testing

Run the test suite:

```bash
pytest
```

Run specific tests:

```bash
pytest tests/test_generation.py
pytest tests/test_rendering.py
```

## Troubleshooting

**"No module named 'card_generator'"**
- Make sure you're in the `src/` directory when running commands

**"OPENAI_API_KEY not set"**
- Either set the environment variable or omit `--use-ai-art` flag

**"Pillow is required"**
- Run `pip install pillow` in your virtual environment

## License

This is a hobby project for educational purposes. Magic: The Gathering is ™ & © Wizards of the Coast.
