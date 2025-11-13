"""Data models for card generation."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set


class CardColor(str, Enum):
    """Enumeration of Magic color identities."""

    WHITE = "W"
    BLUE = "U"
    BLACK = "B"
    RED = "R"
    GREEN = "G"
    COLORLESS = "C"

    @property
    def display_name(self) -> str:
        return {
            CardColor.WHITE: "White",
            CardColor.BLUE: "Blue",
            CardColor.BLACK: "Black",
            CardColor.RED: "Red",
            CardColor.GREEN: "Green",
            CardColor.COLORLESS: "Colorless",
        }[self]


@dataclass(frozen=True)
class ManaCost:
    """Mana cost model supporting colored and generic mana."""

    generic: int = 0
    colors: Sequence[CardColor] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.generic < 0:
            raise ValueError("Generic mana cost cannot be negative")

    def symbols(self) -> str:
        """Return the mana symbols in a readable format."""

        symbols = []
        if self.generic:
            symbols.append(str(self.generic))
        symbols.extend(color.value for color in self.colors)
        return "{" + "}{".join(symbols) + "}" if symbols else "{0}"


@dataclass
class Card:
    """Complete card definition used for rendering."""

    name: str
    mana_cost: ManaCost
    color_identity: Set[CardColor]
    type_line: str
    power: Optional[int]
    toughness: Optional[int]
    abilities: List[str]
    art_path: Path

    def validate(self) -> None:
        """Validate the card fields."""

        if not self.name:
            raise ValueError("Card name cannot be empty")
        if not isinstance(self.mana_cost, ManaCost):
            raise TypeError("mana_cost must be a ManaCost instance")
        if not isinstance(self.color_identity, set):
            raise TypeError("color_identity must be a set")
        if not self.type_line:
            raise ValueError("type_line cannot be empty")
        if bool(self.power is None) != bool(self.toughness is None):
            raise ValueError("Power and toughness must both be set or both be None")
        if any(not ability for ability in self.abilities):
            raise ValueError("Abilities cannot contain empty strings")
        if not self.art_path.exists():
            raise FileNotFoundError(f"Art asset not found at {self.art_path}")

    @property
    def is_creature(self) -> bool:
        return "Creature" in self.type_line

    def describe(self) -> str:
        pt = f"{self.power}/{self.toughness}" if self.power is not None else ""
        abilities = "; ".join(self.abilities)
        colors = ",".join(color.display_name for color in sorted(self.color_identity, key=lambda c: c.value))
        return f"{self.name} [{colors}] {self.type_line} {pt} :: {abilities}"


def normalize_color_identity(colors: Iterable[CardColor]) -> Set[CardColor]:
    """Utility to normalize color identity inputs."""

    identity = {CardColor(color) for color in colors}
    if CardColor.COLORLESS in identity and len(identity) > 1:
        identity.remove(CardColor.COLORLESS)
    return identity
