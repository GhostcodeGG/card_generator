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
INNER_MARGIN = 48
SECTION_SPACING = 18
HEADER_RATIO = 0.13
ART_RATIO = 0.43
TYPE_RATIO = 0.07
RULES_RATIO = 0.25
TITLE_FONT_SIZE = 52
BODY_FONT_SIZE = 30
ABILITY_FONT_SIZE = 24


@dataclass(frozen=True)
class Palette:
    """Color palette defining the Draftforge-style frame."""

    faction: str
    gradient_top: Tuple[int, int, int]
    gradient_bottom: Tuple[int, int, int]
    accent: Tuple[int, int, int]
    paper: Tuple[int, int, int]
    frame: Tuple[int, int, int]
    header_text: Tuple[int, int, int]
    body_text: Tuple[int, int, int]


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


EMBER = Palette(
    faction="Ember",
    gradient_top=(214, 105, 64),
    gradient_bottom=(129, 45, 26),
    accent=(255, 184, 120),
    paper=(244, 232, 220),
    frame=(126, 82, 54),
    header_text=(255, 245, 232),
    body_text=(44, 28, 20),
)
FROST = Palette(
    faction="Frost",
    gradient_top=(100, 160, 198),
    gradient_bottom=(32, 72, 120),
    accent=(168, 210, 240),
    paper=(232, 238, 246),
    frame=(70, 92, 126),
    header_text=(240, 249, 255),
    body_text=(26, 40, 56),
)
VERDANT = Palette(
    faction="Verdant",
    gradient_top=(130, 176, 92),
    gradient_bottom=(46, 94, 52),
    accent=(176, 220, 152),
    paper=(234, 242, 230),
    frame=(72, 108, 66),
    header_text=(246, 254, 240),
    body_text=(26, 46, 28),
)
VOID = Palette(
    faction="Void",
    gradient_top=(132, 92, 168),
    gradient_bottom=(52, 32, 96),
    accent=(192, 156, 228),
    paper=(236, 230, 244),
    frame=(84, 62, 112),
    header_text=(246, 242, 255),
    body_text=(38, 24, 52),
)
RADIANT = Palette(
    faction="Radiant",
    gradient_top=(234, 206, 138),
    gradient_bottom=(176, 130, 60),
    accent=(242, 220, 170),
    paper=(248, 242, 228),
    frame=(170, 138, 88),
    header_text=(74, 50, 26),
    body_text=(60, 42, 24),
)
MACHINE = Palette(
    faction="Machine",
    gradient_top=(164, 172, 182),
    gradient_bottom=(86, 92, 104),
    accent=(210, 216, 222),
    paper=(236, 238, 240),
    frame=(112, 116, 124),
    header_text=(240, 243, 246),
    body_text=(36, 38, 44),
)
NEUTRAL = Palette(
    faction="Neutral",
    gradient_top=(182, 182, 182),
    gradient_bottom=(110, 110, 110),
    accent=(212, 212, 212),
    paper=(238, 238, 236),
    frame=(120, 120, 120),
    header_text=(245, 245, 245),
    body_text=(40, 40, 40),
)

_PALETTE_LOOKUP: Dict[str, Palette] = {
    palette.faction.lower(): palette
    for palette in (EMBER, FROST, VERDANT, VOID, RADIANT, MACHINE, NEUTRAL)
}


def get_palette_for_faction(faction: str) -> Palette:
    """Return a palette matching the requested faction name."""

    return _PALETTE_LOOKUP.get(faction.lower(), NEUTRAL)


def _determine_faction(card: Card) -> str:
    if not card.color_identity:
        return NEUTRAL.faction
    primary_color = sorted(card.color_identity, key=lambda color: color.value)[0]
    mapping = {
        CardColor.RED: EMBER.faction,
        CardColor.BLUE: FROST.faction,
        CardColor.GREEN: VERDANT.faction,
        CardColor.BLACK: VOID.faction,
        CardColor.WHITE: RADIANT.faction,
        CardColor.COLORLESS: MACHINE.faction,
    }
    return mapping.get(primary_color, NEUTRAL.faction)


@dataclass
class RenderSettings:
    background_color: Tuple[int, int, int, int] = (240, 235, 226, 255)
    border_color: Tuple[int, int, int, int] = (58, 40, 28, 255)
    title_font_size: int = TITLE_FONT_SIZE
    body_font_size: int = BODY_FONT_SIZE
    ability_font_size: int = ABILITY_FONT_SIZE


class CardRenderer:
    """Render a :class:`Card` into an image or PDF."""

    def __init__(self, settings: Optional[RenderSettings] = None) -> None:
        self.settings = settings or RenderSettings()
        self.title_font = load_font(self.settings.title_font_size)
        self.body_font = load_font(self.settings.body_font_size)
        self.ability_font = load_font(self.settings.ability_font_size)

    def _create_base_canvas(self, palette: Palette) -> Image.Image:
        base = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), self.settings.background_color)
        draw = ImageDraw.Draw(base)
        outer_radius = 46
        draw.rounded_rectangle(
            (8, 8, CARD_WIDTH - 8, CARD_HEIGHT - 8),
            radius=outer_radius,
            outline=self.settings.border_color,
            width=8,
            fill=_to_rgba(palette.paper),
        )
        inner_radius = outer_radius - 10
        inner_frame_color = _lighten(palette.frame, 0.35)
        draw.rounded_rectangle(
            (INNER_MARGIN - 22, INNER_MARGIN - 26, CARD_WIDTH - INNER_MARGIN + 22, CARD_HEIGHT - INNER_MARGIN + 26),
            radius=inner_radius,
            outline=_to_rgba(palette.frame),
            width=6,
            fill=_to_rgba(inner_frame_color),
        )
        return base

    def _calculate_layout(self) -> Dict[str, Tuple[int, int, int, int]]:
        available_height = CARD_HEIGHT - 2 * INNER_MARGIN - SECTION_SPACING * 4
        header_height = int(available_height * HEADER_RATIO)
        art_height = int(available_height * ART_RATIO)
        type_height = int(available_height * TYPE_RATIO)
        rules_height = int(available_height * RULES_RATIO)
        footer_height = available_height - (header_height + art_height + type_height + rules_height)
        minimum_footer = 96
        if footer_height < minimum_footer:
            adjustment = minimum_footer - footer_height
            art_height = max(art_height - adjustment, 180)
            footer_height = minimum_footer
        y = INNER_MARGIN
        layout: Dict[str, Tuple[int, int, int, int]] = {}
        layout["header"] = (INNER_MARGIN, y, CARD_WIDTH - INNER_MARGIN, y + header_height)
        y = layout["header"][3] + SECTION_SPACING
        art_inset = 24
        layout["art"] = (
            INNER_MARGIN + art_inset,
            y,
            CARD_WIDTH - INNER_MARGIN - art_inset,
            y + art_height,
        )
        y = layout["art"][3] + SECTION_SPACING
        layout["type"] = (INNER_MARGIN, y, CARD_WIDTH - INNER_MARGIN, y + type_height)
        y = layout["type"][3] + SECTION_SPACING
        layout["rules"] = (INNER_MARGIN, y, CARD_WIDTH - INNER_MARGIN, y + rules_height)
        y = layout["rules"][3] + SECTION_SPACING
        layout["footer"] = (INNER_MARGIN, y, CARD_WIDTH - INNER_MARGIN, CARD_HEIGHT - INNER_MARGIN)
        return layout

    def render(self, card: Card) -> Image.Image:
        palette = get_palette_for_faction(_determine_faction(card))
        base = self._create_base_canvas(palette)
        draw = ImageDraw.Draw(base)
        layout = self._calculate_layout()

        self._draw_header(base, draw, card, layout["header"], palette)
        self._draw_art(base, layout["art"], palette)
        self._draw_type_line(draw, card, layout["type"], palette)
        self._draw_rules_text(draw, card, layout["rules"], palette)
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
        palette: Palette,
    ) -> None:
        radius = 28
        header_width = box[2] - box[0]
        header_height = box[3] - box[1]
        gradient = _create_vertical_gradient((header_width, header_height), palette.gradient_top, palette.gradient_bottom)
        mask = Image.new("L", gradient.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, header_width, header_height), radius=radius, fill=255)
        base.paste(gradient, box[:2], mask)
        outline_color = _to_rgba(_darken(palette.frame, 0.15))
        draw.rounded_rectangle(box, radius=radius, outline=outline_color, width=4)

        padding = 28
        text_y_offset = (header_height - _measure_text(draw, card.name, self.title_font)[1]) // 2
        draw.text(
            (box[0] + padding, box[1] + text_y_offset),
            card.name,
            font=self.title_font,
            fill=palette.header_text,
        )

        mana_text = card.mana_cost.symbols()
        if mana_text:
            text_width, text_height = _measure_text(draw, mana_text, self.body_font)
            pill_padding_x = 22
            pill_padding_y = 12
            pill_box = (
                box[2] - padding - text_width - pill_padding_x * 2,
                box[1] + (header_height - text_height - pill_padding_y * 2) // 2,
                box[2] - padding,
                box[1] + (header_height - text_height - pill_padding_y * 2) // 2 + text_height + pill_padding_y * 2,
            )
            pill_radius = (pill_box[3] - pill_box[1]) // 2
            pill_color = _to_rgba(_darken(palette.accent, 0.15))
            draw.rounded_rectangle(pill_box, radius=pill_radius, fill=pill_color, outline=outline_color, width=3)
            text_position = (
                pill_box[0] + pill_padding_x,
                pill_box[1] + (pill_box[3] - pill_box[1] - text_height) // 2,
            )
            draw.text(text_position, mana_text, font=self.body_font, fill=_to_rgba((255, 255, 255)))

    def _draw_art(self, base: Image.Image, box: Tuple[int, int, int, int], palette: Palette) -> None:
        radius = 42
        shadow_offset = 8
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        shadow_box = (
            box[0] + shadow_offset,
            box[1] + shadow_offset,
            box[2] + shadow_offset,
            box[3] + shadow_offset,
        )
        overlay_draw.rounded_rectangle(shadow_box, radius=radius, fill=(0, 0, 0, 70))
        base.alpha_composite(overlay)

        draw = ImageDraw.Draw(base)
        frame_fill = _to_rgba(_lighten(palette.paper, 0.08))
        frame_outline = _to_rgba(_darken(palette.frame, 0.2))
        draw.rounded_rectangle(box, radius=radius, fill=frame_fill, outline=frame_outline, width=5)

        inset = 10
        art_inner = (box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset)
        inner_width = art_inner[2] - art_inner[0]
        inner_height = art_inner[3] - art_inner[1]
        art_gradient = _create_vertical_gradient(
            (inner_width, inner_height), _lighten(palette.gradient_top, 0.1), _lighten(palette.gradient_bottom, 0.1)
        )
        mask = Image.new("L", (inner_width, inner_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, inner_width, inner_height), radius=radius - inset, fill=255)
        base.paste(art_gradient, art_inner[:2], mask)

    def _draw_type_line(
        self,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Palette,
    ) -> None:
        radius = 24
        panel_fill = _to_rgba(_lighten(palette.paper, 0.18))
        panel_outline = _to_rgba(_darken(palette.frame, 0.15))
        draw.rounded_rectangle(box, radius=radius, fill=panel_fill, outline=panel_outline, width=3)
        text_width, text_height = _measure_text(draw, card.type_line, self.body_font)
        text_position = (
            box[0] + 26,
            box[1] + (box[3] - box[1] - text_height) // 2,
        )
        draw.text(text_position, card.type_line, font=self.body_font, fill=palette.body_text)

    def _draw_rules_text(
        self,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Palette,
    ) -> None:
        radius = 26
        panel_fill = _to_rgba(_lighten(palette.paper, 0.25))
        panel_outline = _to_rgba(_darken(palette.frame, 0.12))
        draw.rounded_rectangle(box, radius=radius, fill=panel_fill, outline=panel_outline, width=3)
        padding_x = 26
        padding_y = 22
        text_area_width = box[2] - box[0] - padding_x * 2
        text_y = box[1] + padding_y
        try:
            ascent, descent = self.ability_font.getmetrics()
            measured_height = ascent + descent
        except AttributeError:
            # Fallback for fonts without metric information (e.g. bitmap default font)
            measured_height = _measure_text(draw, "Ag", self.ability_font)[1]
        extra_spacing = 6
        line_height = measured_height + extra_spacing
        lines: List[str] = []
        for index, ability in enumerate(card.abilities):
            parts = ability.splitlines() or [ability]
            for part in parts:
                wrapped = _wrap_text(
                    draw,
                    part,
                    self.ability_font,
                    text_area_width,
                    prefix="• ",
                    subsequent_prefix="  ",
                )
                lines.extend(wrapped)
            if index < len(card.abilities) - 1:
                lines.append("")
        if not lines:
            placeholder = "No abilities listed."
            lines = _wrap_text(draw, placeholder, self.ability_font, text_area_width)
        for line in lines:
            if text_y + line_height > box[3] - padding_y:
                break
            if not line:
                text_y += line_height // 2
                continue
            draw.text((box[0] + padding_x, text_y), line, font=self.ability_font, fill=palette.body_text)
            text_y += line_height

    def _draw_footer(
        self,
        base: Image.Image,
        draw: ImageDraw.ImageDraw,
        card: Card,
        box: Tuple[int, int, int, int],
        palette: Palette,
    ) -> None:
        radius = 26
        panel_fill = _to_rgba(_lighten(palette.paper, 0.14))
        panel_outline = _to_rgba(_darken(palette.frame, 0.18))
        draw.rounded_rectangle(box, radius=radius, fill=panel_fill, outline=panel_outline, width=3)

        padding = 28
        faction_text = palette.faction
        text_width, text_height = _measure_text(draw, faction_text, self.body_font)
        text_y = box[1] + (box[3] - box[1] - text_height) // 2
        draw.text((box[0] + padding, text_y), faction_text, font=self.body_font, fill=palette.body_text)

        diamond_size = 18
        diamond_center = (box[0] + padding + text_width + 24, box[1] + (box[3] - box[1]) // 2)
        diamond_points = [
            (diamond_center[0], diamond_center[1] - diamond_size // 2),
            (diamond_center[0] + diamond_size // 2, diamond_center[1]),
            (diamond_center[0], diamond_center[1] + diamond_size // 2),
            (diamond_center[0] - diamond_size // 2, diamond_center[1]),
        ]
        draw.polygon(diamond_points, fill=_to_rgba(_darken(palette.accent, 0.25)), outline=_to_rgba(_darken(palette.frame, 0.1)))

        if card.power is not None and card.toughness is not None:
            stats_text = f"{card.power} / {card.toughness}"
            stats_width, stats_height = _measure_text(draw, stats_text, self.body_font)
            pill_padding_x = 24
            pill_padding_y = 10
            pill_box = (
                box[2] - padding - stats_width - pill_padding_x * 2,
                box[1] + (box[3] - box[1] - stats_height - pill_padding_y * 2) // 2,
                box[2] - padding,
                box[1] + (box[3] - box[1] - stats_height - pill_padding_y * 2) // 2 + stats_height + pill_padding_y * 2,
            )
            pill_radius = (pill_box[3] - pill_box[1]) // 2
            pill_fill = _to_rgba(_darken(palette.accent, 0.2))
            draw.rounded_rectangle(pill_box, radius=pill_radius, fill=pill_fill, outline=_to_rgba(_darken(palette.frame, 0.2)), width=3)
            text_position = (
                pill_box[0] + pill_padding_x,
                pill_box[1] + (pill_box[3] - pill_box[1] - stats_height) // 2,
            )
            draw.text(text_position, stats_text, font=self.body_font, fill=_to_rgba((255, 255, 255)))
