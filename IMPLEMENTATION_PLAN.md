# 100% Authentic MTG Card Implementation Plan

## Current Status
The card generator has solid AI integration and card generation logic, but the visual rendering needs to match real MTG cards exactly.

## Approach: Professional Template-Based Rendering

### Phase 1: Get Exact Reference Data ✅
**Source:** Real MTG card scans from Scryfall (highest quality available)
- Lightning Bolt (Red): https://cards.scryfall.io/png/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.png
- Reference card: Modern frame (M15+), standard red creature

**What to Extract:**
1. Exact RGB values for red frame gradient (top, middle, bottom)
2. Exact dimensions of each section in pixels
3. Border widths and colors
4. Pinline positions and colors
5. Text box background color
6. Font sizes and positions

### Phase 2: Professional Mana Symbols
**Source:** Mana Font Project (https://mana.andrewgioia.com/)
- SVG-based, official-looking symbols
- Licensed for community use (SIL OFL 1.1)

**Implementation:**
- Download SVG mana symbols
- Render at proper size (matching real cards)
- Use exact MTG colors for each symbol

### Phase 3: Exact Frame Specifications

**Postmodern MTG Card (2015+):**
- Overall: 2.5" × 3.5" (750×1050px at 300 DPI)
- Black border: 2mm top/sides, 6mm bottom
- Art box: 53×39mm (626×461px)
- Text box: 59×32.5mm (697×384px)
- Corner radius: 3mm (35px)

**Color Frames (to be measured from actual cards):**
- Red: Gradient from bright orange-red to deep crimson
- Blue: Gradient from sky blue to deep navy
- Green: Gradient from bright green to forest green
- White: Gradient from ivory to golden cream
- Black: Gradient from purple-gray to dark violet

### Phase 4: Implementation Strategy

**Option A: Pure Template Approach (RECOMMENDED)**
1. Use high-res MTG card scan as base template
2. Replace only the dynamic elements (name, cost, art, text, P/T)
3. Keep all frame elements from template
4. Pros: 100% accurate immediately
5. Cons: Less flexible, template dependency

**Option B: Programmatic Recreation**
1. Measure every pixel of a real card
2. Recreate frame programmatically with exact values
3. Pros: Fully controllable, no template files
4. Cons: Extremely time-consuming, hard to get perfect

**Option C: Hybrid (BEST)**
1. Extract exact color values and dimensions from real cards
2. Use programmatic rendering with these exact values
3. Use SVG mana symbols from Mana font
4. Add pinlines, borders, and effects to match template
5. Pros: Flexible + accurate
6. Cons: Requires careful measurement and testing

## Recommended Next Steps

1. **Download reference card** from Scryfall in PNG
2. **Color pick exact RGB values** from the reference
3. **Measure exact dimensions** of each frame element
4. **Download mana symbol SVGs** from Mana font project
5. **Update renderer.py** with exact measurements
6. **Test side-by-side** with real card until pixel-perfect

## Success Criteria
- [ ] Side-by-side comparison shows no visible difference
- [ ] Colors match exactly (measured with color picker)
- [ ] Dimensions match exactly (measured in pixels)
- [ ] Mana symbols look identical
- [ ] Text positioning is exact
- [ ] Pinlines and borders are present and correct
- [ ] Overall "feel" is indistinguishable from real MTG card

## Estimated Time
- Measurement and color extraction: 1-2 hours
- Implementation: 3-4 hours
- Testing and refinement: 2-3 hours
- **Total: 6-9 hours of focused work**

This is the realistic timeline to reach "100% identical."
