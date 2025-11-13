"""Command-line interface for generating cards."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

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
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)
    factory = CardFactory()
    renderer = CardRenderer()

    args.output.mkdir(parents=True, exist_ok=True)

    for index in range(args.count):
        seed = args.seed + index if args.seed is not None else None
        card = factory.create_card(seed=seed)
        suffix = f"_{index + 1}" if args.count > 1 else ""
        output_path = args.output / f"{card.name.replace(' ', '_')}{suffix}.{args.format}"
        renderer.export(card, output_path, fmt=args.format)
        print(f"Generated {card.describe()} -> {output_path}")


if __name__ == "__main__":
    main()
