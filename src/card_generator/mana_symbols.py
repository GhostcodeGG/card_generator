"""Mana symbol generation and rendering."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple
import tempfile

try:
    from PIL import Image, ImageDraw
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Pillow is required for rendering. Install it with `pip install pillow`."
    ) from exc

from .data_models import CardColor


class ManaSymbolGenerator:
    """Generates mana symbol images for rendering on cards."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path(tempfile.gettempdir()) / "card_generator_mana"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.symbol_size = 100  # Size in pixels

    def _get_symbol_colors(self, symbol: str) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """Get primary and secondary colors for a mana symbol."""
        color_map: Dict[str, Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = {
            "W": ((248, 242, 220), (255, 255, 255)),  # White
            "U": ((50, 150, 220), (120, 200, 255)),   # Blue
            "B": ((60, 50, 70), (120, 100, 130)),     # Black
            "R": ((220, 70, 50), (255, 140, 100)),    # Red
            "G": ((80, 160, 90), (140, 210, 140)),    # Green
            "C": ((180, 185, 195), (220, 225, 230)),  # Colorless
        }

        # For generic mana (numbers), use gray
        if symbol.isdigit():
            return ((180, 180, 190), (220, 220, 230))

        return color_map.get(symbol, ((180, 180, 190), (220, 220, 230)))

    def generate_symbol(self, symbol: str) -> Path:
        """Generate a mana symbol image and return the path."""
        cache_path = self.cache_dir / f"mana_{symbol}.png"

        if cache_path.exists():
            return cache_path

        size = self.symbol_size
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw circle background
        primary_color, secondary_color = self._get_symbol_colors(symbol)

        # Outer circle (border)
        draw.ellipse([2, 2, size-2, size-2], fill=primary_color, outline=(40, 40, 50), width=4)

        # Inner highlight circle
        highlight_size = int(size * 0.85)
        offset = (size - highlight_size) // 2
        draw.ellipse(
            [offset, offset, offset + highlight_size, offset + highlight_size],
            fill=None,
            outline=secondary_color + (180,),
            width=3
        )

        # Draw symbol text
        from PIL import ImageFont
        try:
            font_size = int(size * 0.6)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Center the text
        text = symbol if not symbol.isdigit() else symbol
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size - text_width) // 2
        text_y = (size - text_height) // 2 - 4

        # Text shadow
        shadow_offset = 2
        draw.text(
            (text_x + shadow_offset, text_y + shadow_offset),
            text,
            fill=(0, 0, 0, 120),
            font=font
        )

        # Main text
        draw.text((text_x, text_y), text, fill=(40, 40, 50), font=font)

        img.save(cache_path, "PNG")
        return cache_path

    def get_mana_symbols(self, mana_string: str) -> list[Path]:
        """Parse a mana cost string and return paths to symbol images."""
        # Parse {1}{R}{R} format
        symbols = []
        i = 0
        while i < len(mana_string):
            if mana_string[i] == '{':
                end = mana_string.find('}', i)
                if end != -1:
                    symbol = mana_string[i+1:end]
                    symbols.append(self.generate_symbol(symbol))
                    i = end + 1
                else:
                    i += 1
            else:
                i += 1

        return symbols
