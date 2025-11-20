# MTG Template Setup Guide

## Using Professional Blank Templates

To achieve 100% authentic MTG card visuals, we'll use community-created blank card templates.

### Step 1: Download Blank Templates

**Recommended Source: BANESBOX DeviantArt Templates**
- URL: https://www.deviantart.com/banesbox/art/MTG-Templates-634246660
- Resolution: 2.5" × 3.5" at 300 DPI (print-ready)
- Includes: All 5 colors + colorless/artifact frames

**Alternative Sources:**
- MTG Salvation Forums: https://www.mtgsalvation.com/forums/magic-fundamentals/custom-card-creation/340179
- Slightlymagic.net Forums: https://www.slightlymagic.net/forum/viewtopic.php?f=15&t=16896

### Step 2: Template Organization

Place downloaded templates in:
```
card_generator/
└── templates/
    ├── white_creature.png
    ├── blue_creature.png
    ├── black_creature.png
    ├── red_creature.png
    ├── green_creature.png
    ├── colorless_creature.png
    ├── white_instant.png
    ├── blue_instant.png
    ... (etc for all card types)
```

### Step 3: Template Measurement

For each template, measure pixel coordinates for:
- **Name box**: Where card name appears
- **Mana cost area**: Top right corner
- **Art box**: Central illustration area
- **Type line**: Below art box
- **Text box**: Rules text area
- **P/T box**: Power/Toughness (creatures only)
- **Footer**: Artist credit, set info

### Step 4: Usage

The `template_renderer.py` will:
1. Select appropriate blank template based on card color/type
2. Load AI-generated artwork into art box
3. Overlay card name, type, abilities (AI-generated text)
4. Add mana symbols
5. Add P/T, artist credit, set info

### Result
- ✅ 100% authentic MTG visual frame
- ✅ AI-generated unique content (art, text, name)
- ✅ Print-ready quality (300 DPI)
- ✅ Legal for personal use

## Mana Symbols

**Source: Mana Font Project**
- URL: https://mana.andrewgioia.com/
- Download SVG symbols
- Place in: `card_generator/mana_symbols/`

Available symbols:
- {W} {U} {B} {R} {G} {C} - colored mana
- {0} {1} {2} ... {20} - generic mana
- {X} {Y} {Z} - variable mana
- {T} {Q} - tap/untap symbols
- Plus hybrid mana, Phyrexian mana, etc.

## Legal Note

These community templates are for **personal, non-commercial use only**.
All Magic: The Gathering imagery is © Wizards of the Coast.
