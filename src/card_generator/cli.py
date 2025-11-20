"""Command-line interface for generating cards."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .data_models import CardColor
from .generator import CardFactory
from .renderer import CardRenderer


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Magic-style cards.")
    parser.add_argument("--seed", type=int, default=None, help="Seed for deterministic generation")
    parser.add_argument("--count", type=int, default=1, help="Number of cards to generate")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory where rendered cards are saved",
    )
    parser.add_argument(
        "--format",
        choices=["png", "pdf"],
        default="png",
        help="Export format for rendered cards",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Card name (if not specified, generates random name)",
    )
    parser.add_argument(
        "--colors",
        type=str,
        default=None,
        help="Color identity (e.g., 'R' for red, 'WU' for white-blue, 'C' for colorless)",
    )
    parser.add_argument(
        "--type",
        type=str,
        default=None,
        help="Card type (e.g., 'Creature', 'Instant', 'Sorcery', 'Enchantment', 'Artifact')",
    )
    parser.add_argument(
        "--concept",
        type=str,
        default=None,
        help="Concept or theme for the card (used for AI art generation)",
    )
    parser.add_argument(
        "--abilities",
        type=str,
        nargs="*",
        default=None,
        help="Specific abilities for the card (overrides random generation)",
    )
    parser.add_argument(
        "--power",
        type=int,
        default=None,
        help="Power value for creatures",
    )
    parser.add_argument(
        "--toughness",
        type=int,
        default=None,
        help="Toughness value for creatures",
    )
    parser.add_argument(
        "--use-ai-art",
        action="store_true",
        help="Use AI to generate card artwork (requires API key configuration)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)

    # Parse color identity from string
    color_identity = None
    if args.colors:
        color_identity = []
        for char in args.colors.upper():
            try:
                color_identity.append(CardColor(char))
            except ValueError:
                print(f"Warning: Invalid color '{char}', skipping")
        if not color_identity:
            color_identity = None

    # Create factory with AI art option
    factory = CardFactory(use_ai_art=args.use_ai_art)
    renderer = CardRenderer()

    args.output.mkdir(parents=True, exist_ok=True)

    for index in range(args.count):
        seed = args.seed + index if args.seed is not None else None

        # Build card creation parameters
        creation_params = {
            "seed": seed,
            "name": args.name,
            "color_identity": color_identity,
            "card_type": args.type,
            "concept": args.concept,
            "abilities": args.abilities,
            "power": args.power,
            "toughness": args.toughness,
        }

        card = factory.create_card(**creation_params)
        suffix = f"_{index + 1}" if args.count > 1 else ""
        output_path = args.output / f"{card.name.replace(' ', '_')}{suffix}.{args.format}"
        renderer.export(card, output_path, fmt=args.format)
        print(f"Generated {card.describe()} -> {output_path}")


if __name__ == "__main__":
    main()
