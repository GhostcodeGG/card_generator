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
OUTER_BORDER = 12
CARD_CORNER_RADIUS = 46
INNER_CORNER_RADIUS = 36
CONTENT_MARGIN = 72
SECTION_SPACING = 16
HEADER_RATIO = 0.16
ART_RATIO = 0.58
TYPE_RATIO = 0.06
RULES_RATIO = 0.15
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
        "base": (216, 90, 53),
        "base_dark": (166, 68, 34),
        "surface": (246, 241, 235),
        "surface_light": (251, 247, 242),
        "accent": (240, 150, 86),
        "accent_dark": (150, 60, 34),
        "accent_light": (250, 198, 142),
        "text_on_dark": (255, 242, 234),
        "text_on_light": (58, 38, 30),
    },
    "u": {
        "label": "Frost",
        "base": (91, 178, 204),
        "base_dark": (44, 111, 143),
        "surface": (246, 241, 235),
        "surface_light": (252, 248, 244),
        "accent": (132, 196, 220),
        "accent_dark": (48, 96, 126),
        "accent_light": (184, 222, 238),
        "text_on_dark": (236, 248, 255),
        "text_on_light": (38, 54, 70),
    },
    "g": {
        "label": "Verdant",
        "base": (101, 180, 104),
        "base_dark": (47, 122, 60),
        "surface": (246, 241, 235),
        "surface_light": (251, 247, 242),
        "accent": (152, 208, 140),
        "accent_dark": (58, 108, 64),
        "accent_light": (198, 232, 184),
        "text_on_dark": (236, 250, 236),
        "text_on_light": (38, 56, 40),
    },
    "w": {
        "label": "Radiant",
        "base": (238, 221, 175),
        "base_dark": (199, 169, 106),
        "surface": (246, 241, 235),
        "surface_light": (252, 248, 244),
        "accent": (226, 198, 136),
        "accent_dark": (140, 108, 62),
        "accent_light": (248, 226, 176),
        "text_on_dark": (64, 46, 26),
        "text_on_light": (72, 58, 34),
    },
    "b": {
        "label": "Void",
        "base": (138, 92, 168),
        "base_dark": (90, 57, 122),
        "surface": (246, 241, 235),
        "surface_light": (252, 248, 244),
        "accent": (184, 138, 210),
        "accent_dark": (82, 54, 108),
        "accent_light": (214, 176, 232),
        "text_on_dark": (244, 236, 250),
        "text_on_light": (48, 36, 68),
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

        # Outer drop shadow to lift the card from the background.
        card_shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(card_shadow)
        shadow_offset = (10, 14)
        shadow_box = (
            OUTER_BORDER + shadow_offset[0],
            OUTER_BORDER + shadow_offset[1],
            CARD_WIDTH - OUTER_BORDER + shadow_offset[0],
            CARD_HEIGHT - OUTER_BORDER + shadow_offset[1],
        )
        shadow_draw.rounded_rectangle(
            shadow_box,
            radius=CARD_CORNER_RADIUS,
            fill=(0, 0, 0, 96),
        )
        base.alpha_composite(card_shadow)

        # Dark frame around the card body.
        draw.rectangle((0, 0, CARD_WIDTH, CARD_HEIGHT), fill=self.settings.border_color)

        outer_box = (
            OUTER_BORDER,
            OUTER_BORDER,
            CARD_WIDTH - OUTER_BORDER,
            CARD_HEIGHT - OUTER_BORDER,
        )
        draw.rounded_rectangle(
            outer_box,
            radius=CARD_CORNER_RADIUS,
            fill=_to_rgba(_darken(palette["base_dark"], 0.25)),
            outline=_to_rgba(_darken(palette["base_dark"], 0.4)),
            width=3,
        )

        inner_box = (
            OUTER_BORDER + 8,
            OUTER_BORDER + 8,
            CARD_WIDTH - OUTER_BORDER - 8,
            CARD_HEIGHT - OUTER_BORDER - 8,
        )
        draw.rounded_rectangle(
            inner_box,
            radius=INNER_CORNER_RADIUS,
            fill=_to_rgba(palette["surface"]),
            outline=_to_rgba(_darken(palette["surface"], 0.18)),
            width=2,
        )

        content_box = (
            CONTENT_MARGIN - 18,
            CONTENT_MARGIN - 24,
            CARD_WIDTH - CONTENT_MARGIN + 18,
            CARD_HEIGHT - CONTENT_MARGIN + 24,
        )
        draw.rounded_rectangle(
            content_box,
            radius=INNER_CORNER_RADIUS - 4,
            fill=_to_rgba(palette["surface_light"]),
            outline=_to_rgba(_darken(palette["surface_light"], 0.22)),
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

        art_inset = 14
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
        self._draw_type_bar(base, draw, card, layout["type"], palette)
        self._draw_rules_box(base, draw, card, layout["rules"], palette)
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
        _apply_panel_shadow(base, box, radius, offset=(0, 5), opacity=60)

        gradient = _create_vertical_gradient(
            (box[2] - box[0], box[3] - box[1]),
            _darken(palette["base_dark"], 0.05),
            _lighten(palette["base"], 0.2),
        )
        mask = Image.new("L", gradient.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            (0, 0, gradient.size[0], gradient.size[1]),
            fill=255,
            radius=radius,
        )
        base.paste(gradient, box[:2], mask)

        outline_color = _to_rgba(_darken(palette["base_dark"], 0.3))
        draw.rounded_rectangle(box, radius=radius, outline=outline_color, width=2)

        # Inner highlight for depth at the top edge.
        highlight_color = _to_rgba(_lighten(palette["base"], 0.45), 160)
        draw.line(
            [(box[0] + 8, box[1] + 6), (box[2] - 8, box[1] + 6)],
            fill=highlight_color,
            width=2,
        )

        padding = 28
        name_width, name_height = _measure_text(draw, card.name, self.title_font)
        name_y = box[1] + max((box[3] - box[1] - name_height) // 2 - 2, 0)
        draw.text(
            (box[0] + padding, name_y),
            card.name,
            font=self.title_font,
            fill=palette["text_on_dark"],
        )

        mana_text = card.mana_cost.symbols()
        if mana_text:
            text_width, text_height = _measure_text(draw, mana_text, self.body_font)
            gem_padding_x = 26
            gem_padding_y = 10
            gem_box = (
                box[2] - padding - text_width - gem_padding_x * 2,
                box[1] + (box[3] - box[1] - text_height - gem_padding_y * 2) // 2,
                box[2] - padding,
                box[1]
                + (box[3] - box[1] - text_height - gem_padding_y * 2) // 2
                + text_height
                + gem_padding_y * 2,
            )
            gem_radius = (gem_box[3] - gem_box[1]) // 2

            _apply_panel_shadow(base, gem_box, gem_radius, offset=(2, 4), opacity=80)

            gem_gradient = _create_vertical_gradient(
                (gem_box[2] - gem_box[0], gem_box[3] - gem_box[1]),
                _darken(palette["accent_dark"], 0.1),
                _lighten(palette["accent_dark"], 0.25),
            )
            mask = Image.new("L", (gem_box[2] - gem_box[0], gem_box[3] - gem_box[1]), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle(
                (0, 0, gem_box[2] - gem_box[0], gem_box[3] - gem_box[1]),
                radius=gem_radius,
                fill=255,
            )
            base.paste(gem_gradient, gem_box[:2], mask)

            gem_outline = _to_rgba(_darken(palette["accent_dark"], 0.35))
            draw.rounded_rectangle(gem_box, radius=gem_radius, outline=gem_outline, width=2)

            # Inner glow ring
            inner_glow = ImageDraw.Draw(base)
            glow_radius = gem_radius - 2
            glow_box = (
                gem_box[0] + 2,
                gem_box[1] + 2,
                gem_box[2] - 2,
                gem_box[3] - 2,
            )
            inner_glow.rounded_rectangle(
                glow_box,
                radius=glow_radius,
                outline=_to_rgba(_lighten(palette["accent"], 0.4), 120),
                width=2,
            )

            text_position = (
                gem_box[0] + gem_padding_x,
                gem_box[1] + (gem_box[3] - gem_box[1] - text_height) // 2,
            )
            draw.text(
                text_position,
                mana_text,
                font=self.body_font,
                fill=palette["text_on_dark"],
            )

    def _draw_art_area(
        self,
        base: Image.Image,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        radius = 34
        shadow_offset = 5

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
            fill=_to_rgba(_darken(palette["base_dark"], 0.25), 80),
        )
        base.alpha_composite(overlay)

        draw = ImageDraw.Draw(base)
        frame_outline = _to_rgba(_darken(palette["surface_light"], 0.18))
        frame_fill = _to_rgba(_lighten(palette["surface"], 0.08))
        draw.rounded_rectangle(box, radius=radius, fill=frame_fill, outline=frame_outline, width=2)

        inset = 12
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

        glow_overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_overlay)
        glow_box = (
            art_inner[0] - 2,
            art_inner[1] - 2,
            art_inner[2] + 2,
            art_inner[3] + 2,
        )
        glow_draw.rounded_rectangle(
            glow_box,
            radius=radius - inset + 2,
            outline=_to_rgba(_lighten(palette["surface_light"], 0.4), 150),
            width=2,
        )
        base.alpha_composite(glow_overlay)

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
        base: Image.Image,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        radius = 24
        _apply_panel_shadow(base, box, radius, offset=(0, 4), opacity=56)

        bar_fill = _to_rgba(_lighten(palette["surface_light"], 0.12))
        bar_outline = _to_rgba(_darken(palette["surface_light"], 0.24))
        draw.rounded_rectangle(box, radius=radius, fill=bar_fill, outline=bar_outline, width=2)

        text_width, text_height = _measure_text(draw, card.type_line, self.body_font)
        padding_x = 22
        text_position = (
            box[0] + padding_x,
            box[1] + (box[3] - box[1] - text_height) // 2,
        )
        draw.text(
            text_position,
            card.type_line,
            font=self.body_font,
            fill=_darken(palette["text_on_light"], 0.1),
        )

    def _draw_rules_box(
        self,
        base: Image.Image,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Dict[str, Tuple[int, int, int] | str],
    ) -> None:
        radius = 26
        _apply_panel_shadow(base, box, radius, offset=(0, 6), opacity=48)

        panel_fill = _to_rgba(_darken(palette["surface_light"], 0.08))
        panel_outline = _to_rgba(_darken(palette["surface_light"], 0.25))
        draw.rounded_rectangle(box, radius=radius, fill=panel_fill, outline=panel_outline, width=2)

        padding_x = 24
        padding_y = 20
        text_area_width = box[2] - box[0] - padding_x * 2
        text_y = box[1] + padding_y

        try:
            ascent, descent = self.ability_font.getmetrics()
            line_height = int((ascent + descent) * 1.05)
        except AttributeError:
            line_height = int(_measure_text(draw, "Ag", self.ability_font)[1] * 1.05)

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
                fill=_darken(palette["text_on_light"], 0.2),
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
        radius = 28
        _apply_panel_shadow(base, box, radius, offset=(0, 6), opacity=52)

        footer_fill = _to_rgba(_lighten(palette["surface_light"], 0.14))
        footer_outline = _to_rgba(_darken(palette["surface_light"], 0.28))
        draw.rounded_rectangle(box, radius=radius, fill=footer_fill, outline=footer_outline, width=2)

        identity = "".join(sorted(color.value for color in card.color_identity)) or "C"
        color_key = _resolve_primary_color(card)
        color_name = COLOR_NAMES.get(color_key, "Neutral")
        left_text = f"{palette['label']} — {color_name} ({identity})"

        padding = 26
        text_width, text_height = _measure_text(draw, left_text, self.type_font)
        center_y = box[1] + (box[3] - box[1]) // 2

        diamond_size = 22
        diamond_center = (
            box[0] + padding + diamond_size // 2,
            center_y,
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

        text_x = diamond_center[0] + diamond_size // 2 + 12
        text_y = center_y - text_height // 2
        draw.text(
            (text_x, text_y),
            left_text,
            font=self.type_font,
            fill=_darken(palette["text_on_light"], 0.15),
        )

        if card.power is not None and card.toughness is not None:
            stats_text = f"{card.power} / {card.toughness}"
            stats_width, stats_height = _measure_text(draw, stats_text, self.body_font)
            gem_padding_x = 26
            gem_padding_y = 12
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

            _apply_panel_shadow(base, gem_box, gem_radius, offset=(2, 5), opacity=72)

            gem_gradient = _create_vertical_gradient(
                (gem_box[2] - gem_box[0], gem_box[3] - gem_box[1]),
                _darken(palette["accent_dark"], 0.2),
                _lighten(palette["accent_dark"], 0.18),
            )
            mask = Image.new("L", (gem_box[2] - gem_box[0], gem_box[3] - gem_box[1]), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle(
                (0, 0, gem_box[2] - gem_box[0], gem_box[3] - gem_box[1]),
                radius=gem_radius,
                fill=255,
            )
            base.paste(gem_gradient, gem_box[:2], mask)

            gem_outline = _to_rgba(_darken(palette["accent_dark"], 0.35))
            draw.rounded_rectangle(gem_box, radius=gem_radius, outline=gem_outline, width=2)
            draw.text(
                (
                    gem_box[0] + gem_padding_x,
                    gem_box[1] + (gem_box[3] - gem_box[1] - stats_height) // 2,
                ),
                stats_text,
                font=self.body_font,
                fill=palette["text_on_dark"],
                stroke_width=1,
                stroke_fill=_darken(palette["accent_dark"], 0.45),
            )
