import pytest

from card_generator.generator import CardFactory

try:  # pragma: no cover - skip when Pillow is missing
    from card_generator.renderer import CardRenderer
except RuntimeError as exc:  # pragma: no cover
    pytest.skip(str(exc), allow_module_level=True)


def test_renderer_exports_image(tmp_path):
    factory = CardFactory()
    renderer = CardRenderer()
    card = factory.create_card(seed=7)
    output = tmp_path / "card.png"
    path = renderer.export(card, output)

    assert path.exists()
    assert path.suffix == ".png"
