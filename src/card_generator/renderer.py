"""Rendering pipeline for cards using Pillow."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise RuntimeError(
        "Pillow is required for rendering. Install it with `pip install pillow`."
    ) from exc

from .data_models import Card, CardColor
from .mana_symbols import ManaSymbolGenerator

# MTG card dimensions (2.5" x 3.5" at 300 DPI)
CARD_WIDTH = 750
CARD_HEIGHT = 1050
BLACK_BORDER = 18  # MTG's distinctive black border
INNER_MARGIN = 22
NAME_BAR_HEIGHT = 65
ART_BOX_HEIGHT = 450
TYPE_BAR_HEIGHT = 58
TEXT_BOX_HEIGHT = 270
PT_BOX_SIZE = 70
FOOTER_HEIGHT = 45

TITLE_FONT_SIZE = 48
TYPE_FONT_SIZE = 32
BODY_FONT_SIZE = 28
ABILITY_FONT_SIZE = 24
FLAVOR_FONT_SIZE = 20
LEGAL_FONT_SIZE = 14
MANA_SYMBOL_SIZE = 45

PaletteDict = Dict[str, Tuple[int, int, int]]


COLOR_NAMES = {
    "w": "White",
    "u": "Blue",
    "b": "Black",
    "r": "Red",
    "g": "Green",
    "c": "Colorless",
    "neutral": "Neutral",
}


# MTG-authentic color palettes - vibrant and saturated
PALETTES: Dict[str, Dict[str, Tuple[int, int, int] | str]] = {
    "r": {
        "label": "Red",
        "frame_top": (235, 95, 55),  # Bright orange-red
        "frame_bottom": (185, 45, 25),  # Deep red
        "textbox": (252, 242, 230),  # Warm cream
        "border": (20, 10, 5),  # Very dark brown
        "text": (0, 0, 0),  # Black text
    },
    "u": {
        "label": "Blue",
        "frame_top": (25, 150, 225),  # Vibrant blue
        "frame_bottom": (5, 80, 165),  # Deep blue
        "textbox": (235, 245, 252),  # Light blue-white
        "border": (5, 15, 25),  # Very dark blue
        "text": (0, 0, 0),  # Black text
    },
    "g": {
        "label": "Green",
        "frame_top": (30, 180, 75),  # Vibrant green
        "frame_bottom": (15, 120, 45),  # Forest green
        "textbox": (240, 248, 238),  # Light green-white
        "border": (8, 18, 10),  # Very dark green
        "text": (0, 0, 0),  # Black text
    },
    "w": {
        "label": "White",
        "frame_top": (255, 250, 220),  # Warm ivory
        "frame_bottom": (240, 230, 190),  # Golden cream
        "textbox": (255, 252, 245),  # Off-white
        "border": (25, 20, 15),  # Dark brown
        "text": (0, 0, 0),  # Black text
    },
    "b": {
        "label": "Black",
        "frame_top": (90, 80, 95),  # Purple-gray
        "frame_bottom": (35, 30, 40),  # Very dark purple
        "textbox": (225, 220, 218),  # Light gray
        "border": (10, 8, 12),  # Nearly black
        "text": (0, 0, 0),  # Black text
    },
    "c": {
        "label": "Colorless",
        "frame_top": (190, 190, 195),  # Light gray
        "frame_bottom": (120, 120, 130),  # Medium gray
        "textbox": (242, 242, 244),  # Very light gray
        "border": (30, 30, 35),  # Dark gray
        "text": (0, 0, 0),  # Black text
    },
    "neutral": {
        "label": "Artifact",
        "frame_top": (195, 185, 175),  # Tan-gray
        "frame_bottom": (140, 130, 125),  # Brown-gray
        "textbox": (245, 240, 238),  # Off-white gray
        "border": (35, 30, 28),  # Dark brown
        "text": (0, 0, 0),  # Black text
    },
}


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:  # pragma: no cover - fallback for environments without the font
        return ImageFont.load_default()


def _to_rgba(color: Tuple[int, int, int], alpha: int = 255) -> Tuple[int, int, int, int]:
    return color + (alpha,)


def _mix(color: Tuple[int, int, int], other: Tuple[int, int, int], ratio: float) -> Tuple[int, int, int]:
    return tuple(int(round(color[i] + (other[i] - color[i]) * ratio)) for i in range(3))


def _lighten(color: Tuple[int, int, int], amount: float) -> Tuple[int, int, int]:
    return _mix(color, (255, 255, 255), amount)


def _darken(color: Tuple[int, int, int], amount: float) -> Tuple[int, int, int]:
    return _mix(color, (0, 0, 0), amount)


def _create_vertical_gradient(
    size: Tuple[int, int], top: Tuple[int, int, int], bottom: Tuple[int, int, int]
) -> Image.Image:
    width, height = size
    gradient = Image.new("RGBA", (1, height))
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = _mix(top, bottom, ratio)
        gradient.putpixel((0, y), color + (255,))
    return gradient.resize((width, height))


def _apply_panel_shadow(
    base: Image.Image,
    box: Tuple[int, int, int, int],
    radius: int,
    *,
    offset: Tuple[int, int] = (0, 6),
    opacity: int = 72,
) -> None:
    if opacity <= 0:
        return
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    shadow_box = (
        box[0] + offset[0],
        box[1] + offset[1],
        box[2] + offset[0],
        box[3] + offset[1],
    )
    overlay_draw.rounded_rectangle(
        shadow_box,
        radius=radius,
        fill=(0, 0, 0, max(0, min(opacity, 255))),
    )
    base.alpha_composite(overlay)


def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    prefix: str = "",
    subsequent_prefix: str = "",
) -> List[str]:
    stripped = text.strip()
    if not stripped:
        return []

    # Start with a rough width derived from character count and refine by measurement.
    wrapper = textwrap.TextWrapper(width=max(len(stripped) // 2, 20))
    tentative_lines = wrapper.wrap(stripped) or [stripped]
    lines: List[str] = []
    for index, tentative in enumerate(tentative_lines):
        words = tentative.split()
        if not words:
            continue
        current_prefix = prefix if index == 0 and not lines else subsequent_prefix
        current = current_prefix + words[0]
        for word in words[1:]:
            candidate = current + " " + word
            if _measure_text(draw, candidate, font)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = subsequent_prefix + word
        lines.append(current)
    return lines


def _resolve_primary_color(card: Card) -> str:
    if not card.color_identity:
        return "neutral"
    primary_color = sorted(card.color_identity, key=lambda color: color.value)[0]
    if isinstance(primary_color, CardColor):
        return primary_color.value.lower()
    return str(primary_color).lower()


def get_palette(card: Card) -> Dict[str, Tuple[int, int, int] | str]:
    key = _resolve_primary_color(card)
    return PALETTES.get(key, PALETTES["neutral"])


@dataclass
class RenderSettings:
    background_color: Tuple[int, int, int, int] = (20, 18, 26, 255)
    border_color: Tuple[int, int, int, int] = (6, 6, 10, 255)
    title_font_size: int = TITLE_FONT_SIZE
    body_font_size: int = BODY_FONT_SIZE
    ability_font_size: int = ABILITY_FONT_SIZE
    flavor_font_size: int = FLAVOR_FONT_SIZE
    legal_font_size: int = LEGAL_FONT_SIZE


class CardRenderer:
    """Render a :class:`Card` into an image or PDF."""

    def __init__(self, settings: Optional[RenderSettings] = None) -> None:
        self.settings = settings or RenderSettings()
        self.title_font = load_font(self.settings.title_font_size)
        self.body_font = load_font(self.settings.body_font_size)
        self.type_font = load_font(max(int(self.settings.body_font_size * 0.9), 16))
        self.ability_font = load_font(self.settings.ability_font_size)
        self.flavor_font = load_font(self.settings.flavor_font_size)
        self.legal_font = load_font(self.settings.legal_font_size)
        self.mana_generator = ManaSymbolGenerator()

    def _create_base_canvas(self, palette: Dict[str, Tuple[int, int, int] | str]) -> Image.Image:
        """Create MTG-authentic card base with black border."""
        # Start with black background (MTG's signature black border)
        base = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 255))
        draw = ImageDraw.Draw(base)

        # Inner card area (everything inside the black border)
        inner_box = (
            BLACK_BORDER,
            BLACK_BORDER,
            CARD_WIDTH - BLACK_BORDER,
            CARD_HEIGHT - BLACK_BORDER,
        )

        # Fill with cream/off-white base (typical MTG card color)
        draw.rectangle(inner_box, fill=(252, 248, 242, 255))

        return base

    def _calculate_layout(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Calculate MTG-authentic layout boxes."""
        layout: Dict[str, Tuple[int, int, int, int]] = {}

        left = BLACK_BORDER + INNER_MARGIN
        right = CARD_WIDTH - BLACK_BORDER - INNER_MARGIN
        y = BLACK_BORDER + INNER_MARGIN

        # Name bar at top
        layout["name_bar"] = (left, y, right, y + NAME_BAR_HEIGHT)
        y += NAME_BAR_HEIGHT + 8

        # Art box (biggest section)
        layout["art"] = (left, y, right, y + ART_BOX_HEIGHT)
        y += ART_BOX_HEIGHT + 8

        # Type line bar
        layout["type_bar"] = (left, y, right, y + TYPE_BAR_HEIGHT)
        y += TYPE_BAR_HEIGHT + 8

        # Text box (rules + flavor)
        layout["text_box"] = (left, y, right, y + TEXT_BOX_HEIGHT)
        y += TEXT_BOX_HEIGHT + 6

        # Footer (P/T, artist, set info)
        layout["footer"] = (left, y, right, CARD_HEIGHT - BLACK_BORDER - INNER_MARGIN)

        return layout

    def render(self, card: Card) -> Image.Image:
        palette = get_palette(card)
        base = self._create_base_canvas(palette)
        draw = ImageDraw.Draw(base)
        layout = self._calculate_layout()

        self._draw_name_bar(base, draw, card, layout["name_bar"], palette)
        self._draw_art_box(base, card, layout["art"], palette)
        self._draw_type_bar(base, draw, card, layout["type_bar"], palette)
        self._draw_text_box(base, draw, card, layout["text_box"], palette)
        self._draw_footer(base, draw, card, layout["footer"], palette)
        return base

    def export(self, card: Card, destination: Path, *, fmt: Optional[str] = None) -> Path:
        image = self.render(card)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fmt = fmt or destination.suffix.lstrip(".") or "PNG"
        image.save(destination, format=fmt.upper())
        return destination

    def _draw_name_bar(
        self,
        base: Image.Image,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        """Draw MTG-authentic name bar with vibrant gradient."""
        # Draw gradient frame (top to bottom color fade)
        gradient = _create_vertical_gradient(
            (box[2] - box[0], box[3] - box[1]),
            palette["frame_top"],
            palette["frame_bottom"],
        )
        base.paste(gradient, box[:2])

        # Draw thin border around name bar
        draw.rectangle(box, outline=palette["border"], width=2)

        # Draw card name (left side, black text)
        padding = 12
        name_width, name_height = _measure_text(draw, card.name, self.title_font)
        name_y = box[1] + (box[3] - box[1] - name_height) // 2
        draw.text(
            (box[0] + padding, name_y),
            card.name,
            font=self.title_font,
            fill=(0, 0, 0),  # Black text
        )

        # Render mana symbols (right side)
        mana_text = card.mana_cost.symbols()
        if mana_text:
            symbol_paths = self.mana_generator.get_mana_symbols(mana_text)
            if symbol_paths:
                symbol_size = MANA_SYMBOL_SIZE
                spacing = 3
                total_width = len(symbol_paths) * symbol_size + (len(symbol_paths) - 1) * spacing

                x_start = box[2] - padding - total_width
                y_start = box[1] + (box[3] - box[1] - symbol_size) // 2

                for i, symbol_path in enumerate(symbol_paths):
                    try:
                        symbol_img = Image.open(symbol_path).convert("RGBA")
                        symbol_img = symbol_img.resize((symbol_size, symbol_size), Image.Resampling.LANCZOS)
                        x_pos = x_start + i * (symbol_size + spacing)
                        base.paste(symbol_img, (x_pos, y_start), symbol_img)
                    except Exception as e:
                        print(f"Warning: Could not load mana symbol {symbol_path}: {e}")

    def _draw_art_box(
        self,
        base: Image.Image,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        """Draw MTG-authentic art box with actual card artwork - NO ROUNDED CORNERS."""
        draw = ImageDraw.Draw(base)

        # Draw simple rectangular frame (no rounded corners - MTG style)
        # Thin frame border
        frame_border = 3
        draw.rectangle(box, outline=palette["border"], width=frame_border)

        # Art area inside the frame
        art_area = (
            box[0] + frame_border,
            box[1] + frame_border,
            box[2] - frame_border,
            box[3] - frame_border,
        )
        art_width = art_area[2] - art_area[0]
        art_height = art_area[3] - art_area[1]

        # Load and display ACTUAL card art (fill entire art box)
        try:
            art_img = Image.open(card.art_path).convert("RGB")

            # Crop to fill the art box completely (no letterboxing)
            art_ratio = art_img.width / art_img.height
            box_ratio = art_width / art_height

            if art_ratio > box_ratio:
                # Image is wider - crop width
                new_width = int(art_img.height * box_ratio)
                left = (art_img.width - new_width) // 2
                art_img = art_img.crop((left, 0, left + new_width, art_img.height))
            else:
                # Image is taller - crop height
                new_height = int(art_img.width / box_ratio)
                top = (art_img.height - new_height) // 2
                art_img = art_img.crop((0, top, art_img.width, top + new_height))

            # Resize to exact dimensions
            art_img = art_img.resize((art_width, art_height), Image.Resampling.LANCZOS)

            # Paste directly (no mask, sharp edges like real MTG)
            base.paste(art_img, art_area[:2])

        except Exception as e:
            print(f"Warning: Could not load art from {card.art_path}: {e}")
            # Fallback: solid color based on card color
            draw.rectangle(art_area, fill=palette["frame_top"])

    def _draw_type_bar(
        self,
        base: Image.Image,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        """Draw MTG-authentic type bar."""
        # Draw gradient background (like name bar but subtler)
        gradient = _create_vertical_gradient(
            (box[2] - box[0], box[3] - box[1]),
            _lighten(palette["frame_top"], 0.15),
            _lighten(palette["frame_bottom"], 0.15),
        )
        base.paste(gradient, box[:2])

        # Draw border
        draw.rectangle(box, outline=palette["border"], width=2)

        # Draw type line text (left side, black)
        padding = 10
        text_width, text_height = _measure_text(draw, card.type_line, self.type_font)
        text_y = box[1] + (box[3] - box[1] - text_height) // 2
        draw.text(
            (box[0] + padding, text_y),
            card.type_line,
            font=self.type_font,
            fill=(0, 0, 0),
        )

    def _draw_text_box(
        self,
        base: Image.Image,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        """Draw MTG-authentic text box with abilities and flavor text."""
        # Draw cream/textbox background
        draw.rectangle(box, fill=palette["textbox"])
        draw.rectangle(box, outline=palette["border"], width=2)

        padding_x = 14
        padding_y = 12
        text_area_width = box[2] - box[0] - padding_x * 2
        text_y = box[1] + padding_y

        line_height = 28

        lines: List[str] = []
        flavor_line_indices = set()

        # Add abilities
        if card.abilities:
            for ability in card.abilities:
                ability = ability.strip()
                if not ability:
                    continue
                wrapped = _wrap_text(draw, ability, self.ability_font, text_area_width)
                lines.extend(wrapped)
                lines.append("")  # Space between abilities

        # Add flavor text with separator
        if card.flavor_text:
            if card.abilities:
                lines.append("---")  # Separator marker
                lines.append("")

            flavor_start = len(lines)
            flavor_wrapped = _wrap_text(draw, card.flavor_text, self.flavor_font, text_area_width)
            lines.extend(flavor_wrapped)

            # Mark flavor text line indices
            for i in range(flavor_start, len(lines)):
                flavor_line_indices.add(i)

        # Render text
        for idx, line in enumerate(lines):
            if text_y + line_height > box[3] - padding_y:
                break

            if line == "---":
                # Draw separator line
                separator_y = text_y + 10
                draw.line(
                    [(box[0] + padding_x, separator_y), (box[2] - padding_x, separator_y)],
                    fill=(120, 120, 120),
                    width=1
                )
                text_y += 20
            elif line.strip():
                # Is this flavor text?
                if idx in flavor_line_indices:
                    draw.text(
                        (box[0] + padding_x, text_y),
                        line,
                        font=self.flavor_font,
                        fill=(60, 60, 60),  # Gray italic text
                    )
                else:
                    draw.text(
                        (box[0] + padding_x, text_y),
                        line,
                        font=self.ability_font,
                        fill=(0, 0, 0),  # Black text
                    )
                text_y += line_height
            else:
                text_y += line_height // 2

    def _draw_footer(
        self,
        base: Image.Image,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        """Draw MTG-authentic footer with P/T box and artist/set info."""
        padding = 10

        # Left side: Artist credit
        artist_text = f"Illus. {card.artist}"
        text_height = _measure_text(draw, artist_text, self.legal_font)[1]
        draw.text(
            (box[0] + padding, box[1] + 4),
            artist_text,
            font=self.legal_font,
            fill=(60, 60, 60),
        )

        # Right side: Set code and collector number
        set_text = f"{card.set_code} • {card.collector_number}"
        set_width = _measure_text(draw, set_text, self.legal_font)[0]
        draw.text(
            (box[2] - padding - set_width, box[1] + 4),
            set_text,
            font=self.legal_font,
            fill=(60, 60, 60),
        )

        # Draw P/T box if creature (bottom right)
        if card.power is not None and card.toughness is not None:
            stats_text = f"{card.power}/{card.toughness}"
            stats_width, stats_height = _measure_text(draw, stats_text, self.body_font)

            # P/T box position (bottom right corner)
            pt_box_size = PT_BOX_SIZE
            pt_box = (
                box[2] - pt_box_size - 8,
                box[3] - pt_box_size - 8,
                box[2] - 8,
                box[3] - 8,
            )

            # Draw P/T background (subtle frame color)
            draw.rectangle(pt_box, fill=palette["textbox"])
            draw.rectangle(pt_box, outline=palette["border"], width=3)

            # Draw P/T text (centered in box)
            text_x = pt_box[0] + (pt_box_size - stats_width) // 2
            text_y = pt_box[1] + (pt_box_size - stats_height) // 2
            draw.text(
                (text_x, text_y),
                stats_text,
                font=self.body_font,
                fill=(0, 0, 0),
            )

