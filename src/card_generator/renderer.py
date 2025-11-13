"""Rendering pipeline for cards using Pillow."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise RuntimeError(
        "Pillow is required for rendering. Install it with `pip install pillow`."
    ) from exc

from .data_models import Card

CARD_WIDTH = 744
CARD_HEIGHT = 1039
BORDER_PADDING = 40
TEXT_COLOR = (20, 20, 20)
TITLE_FONT_SIZE = 48
BODY_FONT_SIZE = 32
ABILITY_FONT_SIZE = 30
FRAME_COLOR = (210, 190, 160, 255)
ART_FRAME_OUTLINE = (120, 90, 60, 255)
RULES_BOX_FILL = (255, 255, 255, 235)


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


@dataclass
class RenderSettings:
    background_color: Tuple[int, int, int, int] = (236, 226, 206, 255)
    border_color: Tuple[int, int, int, int] = (80, 60, 45, 255)
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

    def _create_base_canvas(self) -> Image.Image:
        base = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), self.settings.background_color)
        draw = ImageDraw.Draw(base)
        draw.rectangle(
            (10, 10, CARD_WIDTH - 10, CARD_HEIGHT - 10),
            outline=self.settings.border_color,
            width=8,
        )
        draw.rectangle(
            (BORDER_PADDING - 10, 210, CARD_WIDTH - BORDER_PADDING + 10, 630),
            fill=FRAME_COLOR,
            outline=ART_FRAME_OUTLINE,
            width=4,
        )
        draw.rectangle(
            (BORDER_PADDING - 5, 630, CARD_WIDTH - BORDER_PADDING + 5, CARD_HEIGHT - 140),
            fill=RULES_BOX_FILL,
            outline=self.settings.border_color,
            width=3,
        )
        return base

    def render(self, card: Card) -> Image.Image:
        base = self._create_base_canvas()
        draw = ImageDraw.Draw(base)

        self._draw_title(draw, card)
        self._draw_mana_cost(draw, card)
        self._draw_type_line(draw, card)
        self._draw_art(base, card)
        self._draw_abilities(draw, card)
        self._draw_power_toughness(draw, card)
        return base

    def export(self, card: Card, destination: Path, *, fmt: Optional[str] = None) -> Path:
        image = self.render(card)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fmt = fmt or destination.suffix.lstrip(".") or "PNG"
        image.save(destination, format=fmt.upper())
        return destination

    def _draw_title(self, draw: ImageDraw.ImageDraw, card: Card) -> None:
        title_area = (BORDER_PADDING, BORDER_PADDING, CARD_WIDTH - BORDER_PADDING, BORDER_PADDING + 80)
        draw.text((title_area[0], title_area[1]), card.name, font=self.title_font, fill=TEXT_COLOR)

    def _draw_mana_cost(self, draw: ImageDraw.ImageDraw, card: Card) -> None:
        mana_text = card.mana_cost.symbols()
        text_size = draw.textbbox((0, 0), mana_text, font=self.body_font)
        position = (CARD_WIDTH - BORDER_PADDING - (text_size[2] - text_size[0]), BORDER_PADDING)
        draw.text(position, mana_text, font=self.body_font, fill=TEXT_COLOR)

    def _draw_type_line(self, draw: ImageDraw.ImageDraw, card: Card) -> None:
        type_area_y = 200
        draw.text((BORDER_PADDING, type_area_y), card.type_line, font=self.body_font, fill=TEXT_COLOR)

    def _draw_art(self, base: Image.Image, card: Card) -> None:
        art_box = (BORDER_PADDING + 10, 220, CARD_WIDTH - BORDER_PADDING - 10, 620)
        art = Image.open(card.art_path).convert("RGBA")
        art = art.resize((art_box[2] - art_box[0], art_box[3] - art_box[1]))
        base.paste(art, art_box[:2])

    def _wrap_text(self, text: str, width: int) -> Iterable[str]:
        return textwrap.wrap(text, width=width)

    def _draw_abilities(self, draw: ImageDraw.ImageDraw, card: Card) -> None:
        ability_y = 640
        ability_area_width = CARD_WIDTH - 2 * BORDER_PADDING
        for ability in card.abilities:
            for line in self._wrap_text(ability, width=38):
                draw.text((BORDER_PADDING, ability_y), line, font=self.ability_font, fill=TEXT_COLOR)
                ability_y += self.ability_font.size + 4
            ability_y += 6

    def _draw_power_toughness(self, draw: ImageDraw.ImageDraw, card: Card) -> None:
        if card.power is None:
            return
        pt_text = f"{card.power}/{card.toughness}"
        text_size = draw.textbbox((0, 0), pt_text, font=self.body_font)
        position = (
            CARD_WIDTH - BORDER_PADDING - (text_size[2] - text_size[0]),
            CARD_HEIGHT - BORDER_PADDING - (text_size[3] - text_size[1]) - 10,
        )
        draw.text(position, pt_text, font=self.body_font, fill=TEXT_COLOR)
