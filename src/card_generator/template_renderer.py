"""Template-based renderer using authentic MTG card frames."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import urllib.request
import hashlib

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Pillow is required for rendering. Install it with `pip install pillow`."
    ) from exc

from .data_models import Card, CardColor


# Template URLs - using blank MTG card frames from Scryfall
TEMPLATE_URLS = {
    "W": "https://cards.scryfall.io/large/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg",  # Placeholder
    "U": "https://cards.scryfall.io/large/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg",  # Placeholder
    "B": "https://cards.scryfall.io/large/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg",  # Placeholder
    "R": "https://cards.scryfall.io/large/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg",  # Red card
    "G": "https://cards.scryfall.io/large/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg",  # Placeholder
    "C": "https://cards.scryfall.io/large/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg",  # Placeholder
}

# Exact positions measured from real MTG cards (at Scryfall's large image resolution)
# These will need to be measured precisely from actual card scans
CARD_LAYOUT = {
    "name_box": (50, 50, 600, 100),      # (x1, y1, x2, y2) - to be measured
    "mana_cost": (610, 55, 710, 95),     # to be measured
    "art_box": (50, 110, 710, 530),      # to be measured
    "type_box": (50, 540, 710, 580),     # to be measured
    "text_box": (50, 590, 710, 900),     # to be measured
    "pt_box": (650, 870, 710, 920),      # to be measured
    "artist": (60, 930, 400, 950),       # to be measured
    "set_info": (500, 930, 700, 950),    # to be measured
}


@dataclass
class TemplateRenderer:
    """Renders cards by overlaying AI content on authentic MTG templates."""

    template_cache_dir: Path = Path("templates")

    def __post_init__(self):
        self.template_cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_template(self, color: CardColor) -> Path:
        """Download and cache template for the given color."""
        color_key = color.value if color != CardColor.COLORLESS else "C"
        template_url = TEMPLATE_URLS.get(color_key)

        if not template_url:
            # Fallback to colorless
            template_url = TEMPLATE_URLS["C"]

        # Create cache filename
        url_hash = hashlib.md5(template_url.encode()).hexdigest()[:8]
        cache_file = self.template_cache_dir / f"template_{color_key}_{url_hash}.jpg"

        # Download if not cached
        if not cache_file.exists():
            print(f"Downloading template for {color.display_name}...")
            urllib.request.urlretrieve(template_url, cache_file)
            print(f"Cached to {cache_file}")

        return cache_file

    def _load_font(self, size: int) -> ImageFont.ImageFont:
        """Load font for text rendering."""
        try:
            # Try to load a nice font
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

    def render(self, card: Card) -> Image.Image:
        """Render card by overlaying AI content on authentic template."""

        # Get primary color for template
        if card.color_identity:
            primary_color = sorted(card.color_identity)[0]
        else:
            primary_color = CardColor.COLORLESS

        # Load template
        template_path = self._get_template(primary_color)
        base = Image.open(template_path).convert("RGBA")
        draw = ImageDraw.Draw(base)

        # Overlay card name
        name_font = self._load_font(36)
        name_box = CARD_LAYOUT["name_box"]
        draw.text(
            (name_box[0] + 10, name_box[1] + 10),
            card.name,
            font=name_font,
            fill=(0, 0, 0)
        )

        # Overlay AI-generated art
        art_box = CARD_LAYOUT["art_box"]
        try:
            art_img = Image.open(card.art_path).convert("RGB")

            # Resize to fit art box
            art_width = art_box[2] - art_box[0]
            art_height = art_box[3] - art_box[1]

            # Crop to fill
            art_ratio = art_img.width / art_img.height
            box_ratio = art_width / art_height

            if art_ratio > box_ratio:
                new_width = int(art_img.height * box_ratio)
                left = (art_img.width - new_width) // 2
                art_img = art_img.crop((left, 0, left + new_width, art_img.height))
            else:
                new_height = int(art_img.width / box_ratio)
                top = (art_img.height - new_height) // 2
                art_img = art_img.crop((0, top, art_img.width, top + new_height))

            art_img = art_img.resize((art_width, art_height), Image.Resampling.LANCZOS)
            base.paste(art_img, (art_box[0], art_box[1]))

        except Exception as e:
            print(f"Warning: Could not load art: {e}")

        # Overlay type line
        type_font = self._load_font(28)
        type_box = CARD_LAYOUT["type_box"]
        draw.text(
            (type_box[0] + 10, type_box[1] + 10),
            card.type_line,
            font=type_font,
            fill=(0, 0, 0)
        )

        # Overlay rules text
        text_font = self._load_font(22)
        text_box = CARD_LAYOUT["text_box"]
        text_y = text_box[1] + 10

        for ability in card.abilities:
            draw.text(
                (text_box[0] + 10, text_y),
                ability,
                font=text_font,
                fill=(0, 0, 0)
            )
            text_y += 30

        # Overlay P/T if creature
        if card.power is not None and card.toughness is not None:
            pt_font = self._load_font(32)
            pt_box = CARD_LAYOUT["pt_box"]
            pt_text = f"{card.power}/{card.toughness}"
            draw.text(
                (pt_box[0] + 10, pt_box[1] + 5),
                pt_text,
                font=pt_font,
                fill=(0, 0, 0)
            )

        # Overlay artist
        legal_font = self._load_font(14)
        artist_box = CARD_LAYOUT["artist"]
        draw.text(
            (artist_box[0], artist_box[1]),
            f"Illus. {card.artist}",
            font=legal_font,
            fill=(100, 100, 100)
        )

        # Overlay set info
        set_box = CARD_LAYOUT["set_info"]
        draw.text(
            (set_box[0], set_box[1]),
            f"{card.set_code} • {card.collector_number}",
            font=legal_font,
            fill=(100, 100, 100)
        )

        return base

    def export(self, card: Card, destination: Path, *, fmt: Optional[str] = None) -> Path:
        """Export rendered card to file."""
        image = self.render(card)
        destination.parent.mkdir(parents=True, exist_ok=True)

        fmt = fmt or destination.suffix.lstrip(".") or "PNG"
        image.save(destination, format=fmt.upper())
        return destination
