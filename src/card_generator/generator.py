"""Randomized card generation logic."""
from __future__ import annotations

import base64
import random
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:  # pragma: no cover - optional dependency for prettier placeholder art
    from PIL import Image, ImageDraw
except ModuleNotFoundError:  # pragma: no cover - gracefully fall back to static placeholder
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]

from .data_models import Card, CardColor, ManaCost, normalize_color_identity

# Pools of abilities keyed by color identity
ABILITY_POOLS: Dict[CardColor, Sequence[str]] = {
    CardColor.WHITE: (
        "Vigilance",
        "Lifelink",
        "Create a 1/1 white Soldier token",
        "Tap target creature",
    ),
    CardColor.BLUE: (
        "Flying",
        "Draw a card",
        "Return target creature to its owner's hand",
        "Scry 2",
    ),
    CardColor.BLACK: (
        "Deathtouch",
        "Each opponent loses 2 life",
        "Return target creature from your graveyard to your hand",
        "Target creature gets -2/-2 until end of turn",
    ),
    CardColor.RED: (
        "Haste",
        "Deal 3 damage to any target",
        "Discard a card, then draw a card",
        "Create a Treasure token",
    ),
    CardColor.GREEN: (
        "Trample",
        "Put a +1/+1 counter on target creature",
        "Search your library for a basic land card",
        "Gain 3 life",
    ),
    CardColor.COLORLESS: (
        "This spell costs 1 less to cast for each artifact you control",
        "Create a 1/1 colorless Thopter artifact creature token with flying",
        "Scry 1",
    ),
}

CREATURE_TYPES: Sequence[Tuple[str, str]] = (
    ("Human", "Wizard"),
    ("Elf", "Druid"),
    ("Goblin", "Warrior"),
    ("Zombie", "Knight"),
    ("Angel", "Cleric"),
    ("Dragon", ""),
)

NON_CREATURE_TYPES: Sequence[str] = (
    "Instant",
    "Sorcery",
    "Artifact",
    "Enchantment",
    "Planeswalker",
)

NAME_PREFIXES = [
    "Aether",
    "Grim",
    "Radiant",
    "Mystic",
    "Wild",
    "Blazing",
]

NAME_SUFFIXES = [
    "Guardian",
    "Ritual",
    "Phoenix",
    "Sage",
    "Warden",
    "Ascension",
]


PLACEHOLDER_ART_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAGQAAABMCAYAAACF8I0PAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAB"
    "UElEQVR4nO2aQQ6DMAxDv/9T54FF7KZniFVnAnQGo8nJmSBhwRoXVdOZqz9l7emL2vfwCOgIiIiI"
    "iIgrcAE2xYnwS8bR7CjSRoyZoCngW0Bdx44Czwrt0BmwMZyOlgI4E++rmABWvzNJwJ6AzcKuI8WWx"
    "NPBi6M0gg03+GXArnBsZrC3LJCQAABJ+pc0NJfLgwms0x7Fgl36nhXaSd0QeIwAW4qP7kV+Hlc80n"
    "4H7imk0Du8p3gCnp03i85VTgncQ2eY6bOtsAbeIf8Oi0zc2g8EuAWmK8fXgAAABg3u2+d3i+c/YBV"
    "t06P6vNfFPsTVnCiyjfD5//3cv4eY/H/18p/YP5Y9Z+2T1n7ZPWftk9Z+2T1n7ZPWftk9Z+2T1n7Z"
    "PWftk9Z+2T1n7ZPWftk9Z+0cgeQAIiIiIiIiIq6PfgDLRVdVvV3VKQAAAABJRU5ErkJggg=="
)


def _decode_placeholder_bytes() -> bytes:
    return base64.b64decode(PLACEHOLDER_ART_BASE64)


@dataclass
class ArtProvider:
    """Simple provider for placeholder art and hooks for AI art."""

    cache_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        base_dir = self.cache_dir or Path(tempfile.gettempdir()) / "card_generator_art"
        self.cache_path = Path(base_dir)
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def _build_target_path(self, seed: Optional[int]) -> Path:
        if seed is not None:
            identifier = f"seed_{seed}"
        else:
            identifier = uuid.uuid4().hex
        return self.cache_path / f"{identifier}.png"

    def fetch(self, seed: Optional[int] = None, hint: Optional[str] = None) -> Path:
        """Return a path to card art.

        This method can be extended to call an AI image generator. For now it
        generates a simple placeholder image. When Pillow is available the
        placeholder is tinted based on the provided seed to give deterministic
        variety without shipping binary assets in the repository.
        """

        target = self._build_target_path(seed)
        if target.exists():
            return target

        if Image is None:  # pragma: no cover - Pillow is expected in normal usage
            target.write_bytes(_decode_placeholder_bytes())
            return target

        rng = random.Random(seed)
        base_color = tuple(rng.randint(60, 200) for _ in range(3))
        accent_color = tuple(min(255, channel + 40) for channel in base_color)

        image = Image.new("RGBA", (600, 400), base_color + (255,))
        draw = ImageDraw.Draw(image)
        draw.rectangle((40, 40, 560, 360), outline=accent_color + (255,), width=6)
        draw.rectangle((60, 60, 540, 340), fill=(255, 255, 255, 30))
        if hint:
            draw.text((70, 70), hint[:18], fill=accent_color + (255,))

        image.save(target, format="PNG")
        return target

    def request_ai_art(self, prompt: str) -> Path:
        """Placeholder hook that illustrates how to integrate an AI service."""

        raise NotImplementedError(
            "Connect this method to your AI image generator and return a path to the generated asset."
        )


class CardFactory:
    """Factory that produces randomized cards respecting color constraints."""

    def __init__(self, *, art_provider: Optional[ArtProvider] = None) -> None:
        self.art_provider = art_provider or ArtProvider()

    def random_color_identity(self, rng: random.Random) -> List[CardColor]:
        colors = list(CardColor)
        colors.remove(CardColor.COLORLESS)
        choice_count = rng.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
        selected = rng.sample(colors, k=choice_count)
        return selected

    def build_mana_cost(self, colors: Iterable[CardColor], rng: random.Random) -> ManaCost:
        colors = list(colors)
        generic = rng.randint(0, 4 if colors else 10)
        return ManaCost(generic=generic, colors=tuple(colors))

    def choose_type_line(self, colors: Sequence[CardColor], rng: random.Random) -> Tuple[str, Optional[int], Optional[int]]:
        if rng.random() < 0.7:
            creature_types = rng.choice(CREATURE_TYPES)
            types = [t for t in creature_types if t]
            type_line = "Creature — " + " ".join(types)
            power = rng.randint(1, 7)
            toughness = rng.randint(1, 7)
            return type_line, power, toughness
        type_line = rng.choice(NON_CREATURE_TYPES)
        return type_line, None, None

    def choose_abilities(self, colors: Sequence[CardColor], rng: random.Random) -> List[str]:
        if not colors:
            colors = [CardColor.COLORLESS]
        ability_pool = list({ability for color in colors for ability in ABILITY_POOLS[color]})
        ability_count = rng.randint(1, min(3, len(ability_pool)))
        return rng.sample(ability_pool, k=ability_count)

    def generate_name(self, rng: random.Random) -> str:
        prefix = rng.choice(NAME_PREFIXES)
        suffix = rng.choice(NAME_SUFFIXES)
        numeral = "" if rng.random() < 0.8 else f" {rng.randint(2, 9)}"
        return f"{prefix} {suffix}{numeral}"

    def create_card(self, seed: Optional[int] = None) -> Card:
        rng = random.Random(seed)
        colors = normalize_color_identity(self.random_color_identity(rng))
        mana_cost = self.build_mana_cost(colors, rng)
        type_line, power, toughness = self.choose_type_line(list(colors), rng)
        abilities = self.choose_abilities(list(colors), rng)
        name = self.generate_name(rng)
        art_path = self.art_provider.fetch(seed=seed, hint=name)
        card = Card(
            name=name,
            mana_cost=mana_cost,
            color_identity=set(colors),
            type_line=type_line,
            power=power,
            toughness=toughness,
            abilities=abilities,
            art_path=Path(art_path),
        )
        card.validate()
        return card
