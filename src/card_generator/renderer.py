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

CARD_WIDTH = 744
CARD_HEIGHT = 1039
OUTER_BORDER = 14
CARD_CORNER_RADIUS = 48
INNER_CORNER_RADIUS = 38
CONTENT_MARGIN = 72
SECTION_SPACING = 18
HEADER_RATIO = 0.14
ART_RATIO = 0.44
TYPE_RATIO = 0.07
RULES_RATIO = 0.28
TITLE_FONT_SIZE = 58
BODY_FONT_SIZE = 34
ABILITY_FONT_SIZE = 26

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


PALETTES: Dict[str, Dict[str, Tuple[int, int, int] | str]] = {
    "r": {
        "label": "Ember",
        "base": (198, 76, 52),
        "base_dark": (86, 32, 24),
        "surface": (246, 232, 224),
        "surface_light": (253, 246, 240),
        "accent": (236, 142, 64),
        "accent_dark": (150, 60, 36),
        "accent_light": (248, 192, 132),
        "text_on_dark": (255, 244, 236),
        "text_on_light": (52, 36, 30),
    },
    "u": {
        "label": "Tide",
        "base": (64, 118, 176),
        "base_dark": (30, 54, 104),
        "surface": (232, 240, 250),
        "surface_light": (244, 248, 255),
        "accent": (100, 170, 220),
        "accent_dark": (46, 92, 142),
        "accent_light": (168, 212, 248),
        "text_on_dark": (236, 248, 255),
        "text_on_light": (36, 48, 70),
    },
    "g": {
        "label": "Verdant",
        "base": (86, 136, 72),
        "base_dark": (42, 76, 36),
        "surface": (236, 244, 232),
        "surface_light": (244, 250, 240),
        "accent": (144, 194, 110),
        "accent_dark": (68, 108, 52),
        "accent_light": (194, 230, 178),
        "text_on_dark": (240, 252, 240),
        "text_on_light": (36, 52, 34),
    },
    "w": {
        "label": "Radiant",
        "base": (216, 180, 92),
        "base_dark": (128, 96, 44),
        "surface": (248, 244, 234),
        "surface_light": (254, 248, 240),
        "accent": (226, 198, 120),
        "accent_dark": (150, 120, 52),
        "accent_light": (246, 224, 168),
        "text_on_dark": (60, 40, 24),
        "text_on_light": (64, 48, 30),
    },
    "b": {
        "label": "Nightfall",
        "base": (106, 76, 136),
        "base_dark": (46, 30, 72),
        "surface": (238, 234, 244),
        "surface_light": (246, 242, 252),
        "accent": (160, 120, 188),
        "accent_dark": (70, 48, 102),
        "accent_light": (206, 168, 228),
        "text_on_dark": (242, 236, 250),
        "text_on_light": (44, 34, 62),
    },
    "c": {
        "label": "Machina",
        "base": (132, 134, 142),
        "base_dark": (54, 58, 66),
        "surface": (238, 240, 244),
        "surface_light": (246, 248, 252),
        "accent": (180, 186, 198),
        "accent_dark": (86, 92, 104),
        "accent_light": (210, 216, 224),
        "text_on_dark": (246, 248, 252),
        "text_on_light": (42, 46, 52),
    },
    "neutral": {
        "label": "Neutral",
        "base": (120, 124, 136),
        "base_dark": (48, 52, 60),
        "surface": (238, 238, 236),
        "surface_light": (248, 248, 246),
        "accent": (176, 180, 188),
        "accent_dark": (86, 90, 96),
        "accent_light": (214, 216, 220),
        "text_on_dark": (246, 248, 252),
        "text_on_light": (46, 48, 52),
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
    background_color: Tuple[int, int, int, int] = (18, 18, 24, 255)
    border_color: Tuple[int, int, int, int] = (8, 8, 12, 255)
    title_font_size: int = TITLE_FONT_SIZE
    body_font_size: int = BODY_FONT_SIZE
    ability_font_size: int = ABILITY_FONT_SIZE


class CardRenderer:
    """Render a :class:`Card` into an image or PDF."""

    def __init__(self, settings: Optional[RenderSettings] = None) -> None:
        self.settings = settings or RenderSettings()
        self.title_font = load_font(self.settings.title_font_size)
        self.body_font = load_font(self.settings.body_font_size)
        self.type_font = load_font(max(int(self.settings.body_font_size * 0.9), 16))
        self.ability_font = load_font(self.settings.ability_font_size)

    def _create_base_canvas(self, palette: Dict[str, Tuple[int, int, int] | str]) -> Image.Image:
        base = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), self.settings.background_color)
        draw = ImageDraw.Draw(base)

        # Dark outer border
        draw.rectangle((0, 0, CARD_WIDTH, CARD_HEIGHT), fill=self.settings.border_color)

        # Main card background with layered rounded rectangles
        outer_box = (
            OUTER_BORDER,
            OUTER_BORDER,
            CARD_WIDTH - OUTER_BORDER,
            CARD_HEIGHT - OUTER_BORDER,
        )
        draw.rounded_rectangle(
            outer_box,
            radius=CARD_CORNER_RADIUS,
            fill=_to_rgba(palette["base_dark"]),
            outline=_to_rgba(_darken(palette["base_dark"], 0.1)),
            width=4,
        )

        inner_box = (
            OUTER_BORDER + 10,
            OUTER_BORDER + 10,
            CARD_WIDTH - OUTER_BORDER - 10,
            CARD_HEIGHT - OUTER_BORDER - 10,
        )
        draw.rounded_rectangle(
            inner_box,
            radius=INNER_CORNER_RADIUS,
            fill=_to_rgba(palette["surface"]),
            outline=_to_rgba(_darken(palette["surface"], 0.15)),
            width=3,
        )

        content_box = (
            CONTENT_MARGIN - 18,
            CONTENT_MARGIN - 22,
            CARD_WIDTH - CONTENT_MARGIN + 18,
            CARD_HEIGHT - CONTENT_MARGIN + 22,
        )
        draw.rounded_rectangle(
            content_box,
            radius=INNER_CORNER_RADIUS - 6,
            fill=_to_rgba(palette["surface_light"]),
            outline=_to_rgba(_darken(palette["surface"], 0.12)),
            width=2,
        )

        return base

    def _calculate_layout(self) -> Dict[str, Tuple[int, int, int, int]]:
        available_height = CARD_HEIGHT - 2 * CONTENT_MARGIN - SECTION_SPACING * 4
        header_height = int(available_height * HEADER_RATIO)
        art_height = int(available_height * ART_RATIO)
        type_height = int(available_height * TYPE_RATIO)
        rules_height = int(available_height * RULES_RATIO)
        footer_height = available_height - (
            header_height + art_height + type_height + rules_height
        )
        footer_height = max(footer_height, 86)

        layout: Dict[str, Tuple[int, int, int, int]] = {}
        left = CONTENT_MARGIN
        right = CARD_WIDTH - CONTENT_MARGIN
        y = CONTENT_MARGIN

        layout["header"] = (left, y, right, y + header_height)
        y = layout["header"][3] + SECTION_SPACING

        art_inset = 18
        layout["art"] = (
            left + art_inset,
            y,
            right - art_inset,
            y + art_height,
        )
        y = layout["art"][3] + SECTION_SPACING

        layout["type"] = (left, y, right, y + type_height)
        y = layout["type"][3] + SECTION_SPACING

        layout["rules"] = (left, y, right, y + rules_height)
        y = layout["rules"][3] + SECTION_SPACING

        layout["footer"] = (left, y, right, CARD_HEIGHT - CONTENT_MARGIN)
        return layout

    def render(self, card: Card) -> Image.Image:
        palette = get_palette(card)
        base = self._create_base_canvas(palette)
        draw = ImageDraw.Draw(base)
        layout = self._calculate_layout()

        self._draw_header(base, draw, card, layout["header"], palette)
        self._draw_art_area(base, card, layout["art"], palette)
        self._draw_type_bar(draw, card, layout["type"], palette)
        self._draw_rules_box(draw, card, layout["rules"], palette)
        self._draw_footer(base, draw, card, layout["footer"], palette)
        return base

    def export(self, card: Card, destination: Path, *, fmt: Optional[str] = None) -> Path:
        image = self.render(card)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fmt = fmt or destination.suffix.lstrip(".") or "PNG"
        image.save(destination, format=fmt.upper())
        return destination

    def _draw_header(
        self,
        base: Image.Image,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        radius = 28
        header_gradient = _create_vertical_gradient(
            (box[2] - box[0], box[3] - box[1]),
            _lighten(palette["base"], 0.05),
            _darken(palette["base"], 0.12),
        )
        mask = Image.new("L", header_gradient.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, header_gradient.size[0], header_gradient.size[1]), fill=255, radius=radius)
        base.paste(header_gradient, box[:2], mask)

        outline_color = _to_rgba(_darken(palette["base"], 0.25))
        draw.rounded_rectangle(box, radius=radius, outline=outline_color, width=3)

        padding = 26
        name_width, name_height = _measure_text(draw, card.name, self.title_font)
        name_y = box[1] + max((box[3] - box[1] - name_height) // 2 - 4, 0)
        draw.text(
            (box[0] + padding, name_y),
            card.name,
            font=self.title_font,
            fill=palette["text_on_dark"],
        )

        mana_text = card.mana_cost.symbols()
        if mana_text:
            text_width, text_height = _measure_text(draw, mana_text, self.body_font)
            pill_padding_x = 24
            pill_padding_y = 12
            pill_box = (
                box[2] - padding - text_width - pill_padding_x * 2,
                box[1] + (box[3] - box[1] - text_height - pill_padding_y * 2) // 2,
                box[2] - padding,
                box[1]
                + (box[3] - box[1] - text_height - pill_padding_y * 2) // 2
                + text_height
                + pill_padding_y * 2,
            )
            pill_radius = (pill_box[3] - pill_box[1]) // 2
            pill_fill = _to_rgba(palette["accent_dark"])
            pill_outline = _to_rgba(_darken(palette["accent_dark"], 0.2))
            draw.rounded_rectangle(pill_box, radius=pill_radius, fill=pill_fill, outline=pill_outline, width=3)
            text_position = (
                pill_box[0] + pill_padding_x,
                pill_box[1] + (pill_box[3] - pill_box[1] - text_height) // 2,
            )
            draw.text(text_position, mana_text, font=self.body_font, fill=palette["text_on_dark"])

    def _draw_art_area(
        self,
        base: Image.Image,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        radius = 38
        shadow_offset = 6

        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        shadow_box = (
            box[0] + shadow_offset,
            box[1] + shadow_offset,
            box[2] + shadow_offset,
            box[3] + shadow_offset,
        )
        overlay_draw.rounded_rectangle(
            shadow_box,
            radius=radius,
            fill=_to_rgba(_darken(palette["base_dark"], 0.1), 90),
        )
        base.alpha_composite(overlay)

        draw = ImageDraw.Draw(base)
        frame_outline = _to_rgba(_darken(palette["surface"], 0.2))
        frame_fill = _to_rgba(_lighten(palette["surface"], 0.1))
        draw.rounded_rectangle(box, radius=radius, fill=frame_fill, outline=frame_outline, width=4)

        inset = 10
        art_inner = (box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset)
        inner_width = art_inner[2] - art_inner[0]
        inner_height = art_inner[3] - art_inner[1]
        gradient = _create_vertical_gradient(
            (inner_width, inner_height),
            _lighten(palette["accent"], 0.2),
            _darken(palette["base"], 0.15),
        )
        mask = Image.new("L", (inner_width, inner_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, inner_width, inner_height), radius=radius - inset, fill=255)
        base.paste(gradient, art_inner[:2], mask)

        watermark_text = card.name.upper()
        wm_draw = ImageDraw.Draw(base)
        wm_width, wm_height = _measure_text(wm_draw, watermark_text, self.type_font)
        if wm_width and wm_height:
            watermark_overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(watermark_overlay)
            text_x = art_inner[0] + (inner_width - wm_width) // 2
            text_y = art_inner[1] + (inner_height - wm_height) // 2
            overlay_draw.text(
                (text_x, text_y),
                watermark_text,
                font=self.type_font,
                fill=_to_rgba(_lighten(palette["base_dark"], 0.3), 40),
            )
            base.alpha_composite(watermark_overlay)

    def _draw_type_bar(
        self,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        radius = 22
        bar_fill = _to_rgba(_lighten(palette["surface"], 0.22))
        bar_outline = _to_rgba(_darken(palette["surface"], 0.18))
        draw.rounded_rectangle(box, radius=radius, fill=bar_fill, outline=bar_outline, width=3)

        text_width, text_height = _measure_text(draw, card.type_line, self.body_font)
        text_position = (
            box[0] + 24,
            box[1] + (box[3] - box[1] - text_height) // 2,
        )
        draw.text(text_position, card.type_line, font=self.body_font, fill=palette["text_on_light"])

    def _draw_rules_box(
        self,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        radius = 26
        panel_fill = _to_rgba(_lighten(palette["surface_light"], 0.05))
        panel_outline = _to_rgba(_darken(palette["surface"], 0.2))
        draw.rounded_rectangle(box, radius=radius, fill=panel_fill, outline=panel_outline, width=3)

        padding_x = 28
        padding_y = 24
        text_area_width = box[2] - box[0] - padding_x * 2
        text_y = box[1] + padding_y

        try:
            ascent, descent = self.ability_font.getmetrics()
            line_height = ascent + descent + 6
        except AttributeError:
            line_height = _measure_text(draw, "Ag", self.ability_font)[1] + 6

        lines: List[str] = []
        if card.abilities:
            for index, ability in enumerate(card.abilities):
                ability = ability.strip()
                if not ability:
                    continue
                wrapped = _wrap_text(
                    draw,
                    ability,
                    self.ability_font,
                    text_area_width,
                    prefix="• ",
                    subsequent_prefix="  ",
                )
                lines.extend(wrapped)
                if index < len(card.abilities) - 1:
                    lines.append("")
        else:
            placeholder = "No abilities listed."
            lines = _wrap_text(draw, placeholder, self.ability_font, text_area_width)

        for line in lines:
            if text_y + line_height > box[3] - padding_y:
                break
            if not line:
                text_y += line_height // 2
                continue
            draw.text(
                (box[0] + padding_x, text_y),
                line,
                font=self.ability_font,
                fill=palette["text_on_light"],
            )
            text_y += line_height

    def _draw_footer(
        self,
        base: Image.Image,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        radius = 26
        footer_fill = _to_rgba(_lighten(palette["surface"], 0.16))
        footer_outline = _to_rgba(_darken(palette["surface"], 0.2))
        draw.rounded_rectangle(box, radius=radius, fill=footer_fill, outline=footer_outline, width=3)

        identity = "".join(sorted(color.value for color in card.color_identity)) or "C"
        color_key = _resolve_primary_color(card)
        color_name = COLOR_NAMES.get(color_key, "Neutral")
        left_text = f"{palette['label']} — {color_name} ({identity})"

        padding = 28
        text_width, text_height = _measure_text(draw, left_text, self.type_font)
        text_y = box[1] + (box[3] - box[1] - text_height) // 2
        draw.text(
            (box[0] + padding, text_y),
            left_text,
            font=self.type_font,
            fill=palette["text_on_light"],
        )

        diamond_size = 20
        diamond_center = (
            box[0] + padding + text_width + 28,
            box[1] + (box[3] - box[1]) // 2,
        )
        diamond_points = [
            (diamond_center[0], diamond_center[1] - diamond_size // 2),
            (diamond_center[0] + diamond_size // 2, diamond_center[1]),
            (diamond_center[0], diamond_center[1] + diamond_size // 2),
            (diamond_center[0] - diamond_size // 2, diamond_center[1]),
        ]
        draw.polygon(
            diamond_points,
            fill=_to_rgba(palette["accent"]),
            outline=_to_rgba(_darken(palette["accent"], 0.3)),
        )

        if card.power is not None and card.toughness is not None:
            stats_text = f"{card.power} / {card.toughness}"
            stats_width, stats_height = _measure_text(draw, stats_text, self.body_font)
            gem_padding_x = 28
            gem_padding_y = 14
            gem_box = (
                box[2] - padding - stats_width - gem_padding_x * 2,
                box[1] + (box[3] - box[1] - stats_height - gem_padding_y * 2) // 2,
                box[2] - padding,
                box[1]
                + (box[3] - box[1] - stats_height - gem_padding_y * 2) // 2
                + stats_height
                + gem_padding_y * 2,
            )
            gem_radius = (gem_box[3] - gem_box[1]) // 2
            gem_fill = _to_rgba(palette["accent_dark"])
            gem_outline = _to_rgba(_darken(palette["accent_dark"], 0.2))
            draw.rounded_rectangle(gem_box, radius=gem_radius, fill=gem_fill, outline=gem_outline, width=3)
            draw.text(
                (
                    gem_box[0] + gem_padding_x,
                    gem_box[1] + (gem_box[3] - gem_box[1] - stats_height) // 2,
                ),
                stats_text,
                font=self.body_font,
                fill=palette["text_on_dark"],
            )
