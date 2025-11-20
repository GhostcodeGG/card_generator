# Quick Start Guide

Get started creating AI-generated Magic: The Gathering cards in 3 steps!

## Step 1: Install

```bash
# Clone or navigate to the project
cd card_generator

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Set API Key (Optional)

For AI-generated artwork and flavor text, you'll need an OpenAI API key.

**Get an API key:** https://platform.openai.com/api-keys

**Set it:**
```bash
# Windows
set OPENAI_API_KEY=sk-your-key-here

# macOS/Linux
export OPENAI_API_KEY=sk-your-key-here
```

## Step 3: Generate Cards!

Navigate to the `src` directory:
```bash
cd src
```

### Simple Random Card
```bash
python -m card_generator.cli --output ../output
```

### Custom Card (No AI)
```bash
python -m card_generator.cli --output ../output \
  --name "Lightning Bolt" \
  --colors R \
  --type Instant
```

### Full AI Card
```bash
python -m card_generator.cli --output ../output \
  --name "Celestial Dragon" \
  --colors W \
  --type "Creature — Dragon Angel" \
  --concept "majestic white dragon with glowing wings flying through clouds" \
  --power 4 \
  --toughness 5 \
  --use-ai-art
```

### Batch Generate
```bash
python -m card_generator.cli --output ../output \
  --seed 42 \
  --count 10 \
  --colors RG \
  --use-ai-art
```

## Common Patterns

### Mono-Color Creature
```bash
python -m card_generator.cli --output ../output \
  --name "Goblin Berserker" \
  --colors R \
  --type "Creature — Goblin Warrior" \
  --power 3 \
  --toughness 2 \
  --use-ai-art
```

### Multicolor Spell
```bash
python -m card_generator.cli --output ../output \
  --name "Supreme Verdict" \
  --colors WU \
  --type Sorcery \
  --abilities "Destroy all creatures" "This spell can't be countered" \
  --use-ai-art
```

### Themed Set
```bash
# Generate 5 cards with similar theme
python -m card_generator.cli --output ../output \
  --seed 100 \
  --count 5 \
  --colors B \
  --concept "dark vampire castle at night" \
  --use-ai-art
```

## Tips

- **Without `--use-ai-art`**: Cards use placeholder gradient art (no API key needed)
- **With `--use-ai-art`**: Real AI-generated artwork (requires OpenAI API key)
- **Use `--seed`**: Same seed = same card (great for testing)
- **Mix random & custom**: Specify some params, let others randomize
- **Check `../output`**: All cards save there by default

## What Gets Generated?

Each card includes:
- ✅ Professional MTG-style layout
- ✅ Color-accurate card borders and palette
- ✅ Mana symbol graphics (not text)
- ✅ Balanced mana costs
- ✅ Varied abilities from color-specific pools
- ✅ Flavor text
- ✅ Artist credit ("AI Generated")
- ✅ Set code and collector number
- ✅ Legal footer

**With `--use-ai-art`:**
- ✅ DALL-E 3 generated artwork
- ✅ GPT-3.5 generated flavor text

## Troubleshooting

**Error: "No module named 'card_generator'"**
- Make sure you're in the `src/` directory

**Cards have placeholder art**
- Either add `--use-ai-art` flag or set `OPENAI_API_KEY`

**AI art generation fails**
- Check your API key is valid
- Ensure you have credits in your OpenAI account
- Falls back to placeholder art automatically

## Next Steps

- Read full [README.md](README.md) for all options
- Check [CLAUDE.md](CLAUDE.md) for architecture details
- Explore color combinations and card types
- Create complete custom sets!

Happy card crafting! 🎴✨
