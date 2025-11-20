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
        "First strike",
        "Protection from black",
        "Create a 1/1 white Soldier creature token",
        "Exile target creature until this leaves the battlefield",
        "Tap target creature",
        "Creatures you control get +1/+1 until end of turn",
        "Destroy target attacking creature",
        "Each opponent loses 1 life and you gain 1 life",
        "Return target creature card with mana value 2 or less from your graveyard to the battlefield",
    ),
    CardColor.BLUE: (
        "Flying",
        "Flash",
        "Hexproof",
        "Draw a card",
        "Draw two cards, then discard a card",
        "Return target creature to its owner's hand",
        "Counter target spell unless its controller pays {2}",
        "Scry 2",
        "Target player mills three cards",
        "Create a 1/1 blue Faerie creature token with flying",
        "Look at the top four cards of your library, put one into your hand and the rest on the bottom",
    ),
    CardColor.BLACK: (
        "Deathtouch",
        "Menace",
        "Lifelink",
        "Each opponent loses 2 life and you gain 2 life",
        "Destroy target creature",
        "Return target creature card from your graveyard to your hand",
        "Target creature gets -3/-3 until end of turn",
        "Each player sacrifices a creature",
        "Draw a card and you lose 1 life",
        "Create a 2/2 black Zombie creature token",
        "Target opponent discards a card",
    ),
    CardColor.RED: (
        "Haste",
        "First strike",
        "Menace",
        "Trample",
        "Deal 3 damage to any target",
        "Deal 2 damage to each creature",
        "Destroy target artifact",
        "Discard a card, then draw a card",
        "Create a Treasure token",
        "Create two 1/1 red Goblin creature tokens",
        "Target creature can't block this turn",
        "Add {R}{R}{R}",
    ),
    CardColor.GREEN: (
        "Trample",
        "Reach",
        "Vigilance",
        "Hexproof",
        "Put a +1/+1 counter on target creature",
        "Put two +1/+1 counters on target creature",
        "Search your library for a basic land card, reveal it, put it into your hand, then shuffle",
        "Create a 3/3 green Beast creature token",
        "Destroy target artifact or enchantment",
        "Gain 5 life",
        "Target creature you control fights target creature you don't control",
        "Draw a card for each creature you control with power 4 or greater",
    ),
    CardColor.COLORLESS: (
        "This spell costs {1} less to cast for each artifact you control",
        "Create a 1/1 colorless Thopter artifact creature token with flying",
        "Scry 2",
        "Draw a card",
        "Tap target permanent",
        "Add two mana of any one color",
        "Sacrifice this: Draw a card",
        "You gain 3 life",
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
    ai_api_key: Optional[str] = None
    ai_provider: str = "openai"  # or "stability", "replicate", etc.

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
        """Generate art using AI image generation services."""
        import hashlib
        import os
        import urllib.request

        # Create a cache key from the prompt
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        target = self.cache_path / f"ai_{prompt_hash}.png"

        # Return cached version if it exists
        if target.exists():
            return target

        # Check for API key
        api_key = self.ai_api_key or os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise NotImplementedError(
                "AI art generation requires an API key. Set OPENAI_API_KEY environment variable "
                "or pass ai_api_key to ArtProvider constructor."
            )

        if self.ai_provider == "openai":
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)

                print(f"Generating AI art with prompt: {prompt}")
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )

                image_url = response.data[0].url

                # Download the image
                urllib.request.urlretrieve(image_url, target)
                print(f"AI art saved to: {target}")
                return target

            except ImportError:
                raise NotImplementedError(
                    "OpenAI library not installed. Install with: pip install openai"
                )
            except Exception as e:
                print(f"Error generating AI art: {e}")
                print("Falling back to placeholder art")
                raise NotImplementedError(f"AI art generation failed: {e}")
        else:
            raise NotImplementedError(
                f"AI provider '{self.ai_provider}' not implemented. Supported: 'openai'"
            )


class CardFactory:
    """Factory that produces randomized cards respecting color constraints."""

    def __init__(self, *, art_provider: Optional[ArtProvider] = None, use_ai_art: bool = False) -> None:
        self.art_provider = art_provider or ArtProvider()
        self.use_ai_art = use_ai_art

    def random_color_identity(self, rng: random.Random) -> List[CardColor]:
        colors = list(CardColor)
        colors.remove(CardColor.COLORLESS)
        choice_count = rng.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
        selected = rng.sample(colors, k=choice_count)
        return selected

    def calculate_card_value(
        self,
        power: Optional[int],
        toughness: Optional[int],
        abilities: List[str],
        type_line: str,
    ) -> int:
        """Calculate approximate mana value based on card stats and abilities."""
        value = 0

        # Base value for creatures
        if power is not None and toughness is not None:
            # Simple heuristic: (P + T) / 2 rounded down
            value += (power + toughness) // 2

        # Value for abilities
        keyword_values = {
            "Flying": 1,
            "First strike": 1,
            "Double strike": 2,
            "Deathtouch": 1,
            "Lifelink": 1,
            "Trample": 1,
            "Vigilance": 1,
            "Haste": 1,
            "Hexproof": 2,
            "Menace": 1,
            "Reach": 1,
            "Flash": 1,
        }

        for ability in abilities:
            # Check for keyword abilities
            for keyword, ability_value in keyword_values.items():
                if keyword.lower() in ability.lower():
                    value += ability_value
                    break
            else:
                # Non-keyword abilities are worth more
                if "draw" in ability.lower():
                    value += 2
                elif "damage" in ability.lower():
                    value += 2
                elif "destroy" in ability.lower():
                    value += 3
                elif "counter" in ability.lower():
                    value += 3
                elif "create" in ability.lower() and "token" in ability.lower():
                    value += 2
                else:
                    value += 1

        # Non-creatures typically have higher value abilities
        if "Instant" in type_line or "Sorcery" in type_line:
            value += 1

        return max(value, 0)

    def build_mana_cost(
        self,
        colors: Iterable[CardColor],
        rng: random.Random,
        card_value: Optional[int] = None,
    ) -> ManaCost:
        """Build mana cost, optionally balanced based on card value."""
        colors = list(colors)

        if card_value is not None:
            # Balanced mana cost based on card value
            # Distribute cost between generic and colored mana
            colored_cost = min(len(colors), max(1, card_value // 3)) if colors else 0
            generic = max(0, card_value - colored_cost)

            # Use each color at least once if multicolor
            color_sequence = list(colors)
            if len(color_sequence) > colored_cost:
                # If we need more colored pips than our cost, sample
                color_sequence = rng.sample(color_sequence * 2, colored_cost)
            else:
                # Repeat colors to fill out cost
                while len(color_sequence) < colored_cost:
                    color_sequence.append(rng.choice(colors))

            return ManaCost(generic=generic, colors=tuple(color_sequence))
        else:
            # Random cost (legacy behavior)
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

    def generate_flavor_text(
        self,
        card_name: str,
        colors: Sequence[CardColor],
        type_line: str,
        abilities: List[str],
        use_ai: bool = False,
    ) -> str:
        """Generate flavor text based on card attributes."""
        import os

        if use_ai:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                try:
                    import openai
                    client = openai.OpenAI(api_key=api_key)

                    color_names = ", ".join(c.display_name for c in colors) if colors else "Colorless"
                    abilities_text = "; ".join(abilities[:2]) if abilities else "no special abilities"

                    prompt = f"""Generate a short, evocative flavor text (1-2 sentences, max 100 characters) for a Magic: The Gathering card with these attributes:
Name: {card_name}
Type: {type_line}
Colors: {color_names}
Key abilities: {abilities_text}

The flavor text should be atmospheric, mysterious, and capture the essence of the card. Keep it concise and poetic."""

                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a creative writer specializing in Magic: The Gathering flavor text."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=60,
                        temperature=0.8,
                    )

                    flavor = response.choices[0].message.content.strip().strip('"')
                    if len(flavor) > 120:
                        flavor = flavor[:117] + "..."
                    return flavor

                except ImportError:
                    print("OpenAI library not installed for AI flavor text generation")
                except Exception as e:
                    print(f"Error generating AI flavor text: {e}")

        # Fallback to template-based generation
        rng = random.Random(hash(card_name))
        flavor_templates = [
            f"The essence of {card_name.lower()} echoes through the ages.",
            f"Few have witnessed the true power of {card_name.lower()}.",
            f"In the heat of battle, {card_name.lower()} stands unmatched.",
            f"Ancient legends speak of {card_name.lower()}'s might.",
            f"The very air trembles at the presence of {card_name.lower()}.",
            f"When {card_name.lower()} awakens, the world takes notice.",
            f"Whispers of {card_name.lower()} haunt the battlefield.",
            f"None can stand against the fury of {card_name.lower()}.",
        ]
        return rng.choice(flavor_templates)

    def generate_art_prompt(
        self,
        name: str,
        colors: Sequence[CardColor],
        type_line: str,
        concept: Optional[str] = None,
    ) -> str:
        """Generate a detailed prompt for AI art generation."""
        if concept:
            base_prompt = concept
        else:
            base_prompt = name

        # Add color themes
        color_themes = {
            CardColor.WHITE: "holy light, angels, plains, order, justice",
            CardColor.BLUE: "water, islands, magic, knowledge, illusion",
            CardColor.BLACK: "darkness, swamps, death, decay, shadows",
            CardColor.RED: "fire, mountains, lightning, chaos, passion",
            CardColor.GREEN: "nature, forests, beasts, growth, life",
            CardColor.COLORLESS: "artifacts, metallic, mechanical, ancient ruins",
        }

        color_desc = ", ".join(color_themes.get(c, "") for c in colors if c in color_themes)

        # Add type-specific elements
        type_elements = ""
        if "Creature" in type_line:
            type_elements = "character portrait, detailed anatomy"
        elif "Instant" in type_line or "Sorcery" in type_line:
            type_elements = "magical effect, dynamic action, spell casting"
        elif "Artifact" in type_line:
            type_elements = "intricate mechanism, ancient technology"
        elif "Enchantment" in type_line:
            type_elements = "mystical aura, ethereal magic"

        prompt = f"{base_prompt}, {color_desc}, {type_elements}, Magic: The Gathering card art style, fantasy illustration, highly detailed, professional TCG artwork"
        return prompt

    def create_card(
        self,
        seed: Optional[int] = None,
        name: Optional[str] = None,
        color_identity: Optional[Sequence[CardColor]] = None,
        card_type: Optional[str] = None,
        concept: Optional[str] = None,
        abilities: Optional[Sequence[str]] = None,
        power: Optional[int] = None,
        toughness: Optional[int] = None,
    ) -> Card:
        rng = random.Random(seed)

        # Determine colors
        if color_identity:
            colors = normalize_color_identity(color_identity)
        else:
            colors = normalize_color_identity(self.random_color_identity(rng))

        # Determine type line and stats
        if card_type:
            type_line = card_type
            if "Creature" in type_line and power is None and toughness is None:
                power = rng.randint(1, 7)
                toughness = rng.randint(1, 7)
            elif "Creature" not in type_line:
                power = None
                toughness = None
        else:
            type_line, power, toughness = self.choose_type_line(list(colors), rng)

        # Apply custom power/toughness if provided
        if power is not None and toughness is not None and "Creature" in type_line:
            pass  # Use provided values
        elif "Creature" not in type_line:
            power = None
            toughness = None

        # Determine abilities
        if abilities:
            ability_list = list(abilities)
        else:
            ability_list = self.choose_abilities(list(colors), rng)

        # Determine name
        if not name:
            name = self.generate_name(rng)

        # Calculate card value for balanced mana cost
        card_value = self.calculate_card_value(power, toughness, ability_list, type_line)

        # Generate mana cost (balanced based on card value)
        mana_cost = self.build_mana_cost(colors, rng, card_value)

        # Generate art
        if self.use_ai_art:
            art_prompt = self.generate_art_prompt(name, list(colors), type_line, concept)
            try:
                art_path = self.art_provider.request_ai_art(art_prompt)
            except NotImplementedError:
                print("Warning: AI art generation not configured, using placeholder")
                art_path = self.art_provider.fetch(seed=seed, hint=name)
        else:
            art_path = self.art_provider.fetch(seed=seed, hint=name)

        # Generate flavor text
        flavor_text = self.generate_flavor_text(
            name,
            list(colors),
            type_line,
            ability_list,
            use_ai=self.use_ai_art  # Use same flag as AI art
        )

        # Generate collector number
        collector_num = f"{rng.randint(1, 999):03d}"

        card = Card(
            name=name,
            mana_cost=mana_cost,
            color_identity=set(colors),
            type_line=type_line,
            power=power,
            toughness=toughness,
            abilities=ability_list,
            art_path=Path(art_path),
            flavor_text=flavor_text,
            artist="AI Generated",
            set_code="AI1",
            collector_number=collector_num,
        )
        card.validate()
        return card
