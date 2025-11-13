from card_generator.generator import CardFactory


def test_generate_card_contains_required_fields(tmp_path):
    factory = CardFactory()
    card = factory.create_card(seed=123)

    assert card.name
    assert card.mana_cost
    assert card.color_identity
    assert card.type_line
    assert card.abilities
    card.validate()


def test_seed_reproducibility():
    factory = CardFactory()
    card1 = factory.create_card(seed=42)
    card2 = factory.create_card(seed=42)

    assert card1.describe() == card2.describe()
    assert card1.mana_cost == card2.mana_cost
