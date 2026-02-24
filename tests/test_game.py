import random

from game.engine import CARD_COUNTS, CardGame
from game.models import Role


def test_deal_counts_are_correct():
    game = CardGame(random.Random(1))
    game.setup_game()

    assert sum(CARD_COUNTS.values()) == 29
    assert all(len(p.hand) == 9 for p in game.state.players)
    assert len(game.state.bottom_cards) == 2
    assert len(game.state.deck) == 0


def test_bottom_cards_are_open_information():
    game = CardGame(random.Random(2))
    game.setup_game()

    names = game.bottom_card_names()
    assert len(names) == 2
    assert all(isinstance(name, str) and name for name in names)


def test_play_order_and_support_visibility():
    game = CardGame(random.Random(3))
    game.setup_game()

    ordered_roles = []

    def chooser(player):
        ordered_roles.append(player.role)
        return 0

    placed = game.play_phase(chooser)

    assert ordered_roles == [Role.ATTACKER, Role.PRESSURE, Role.SUPPORT]
    pressure = game.get_player_by_role(Role.PRESSURE)
    support = game.get_player_by_role(Role.SUPPORT)
    pressure_placed = next(c for c in placed if c.owner_id == pressure.player_id)
    assert support.player_id in pressure_placed.visible_to


def test_round_end_recovery_rules_with_and_without_flip():
    game = CardGame(random.Random(4))
    game.setup_game()
    starting_hand_sizes = {p.player_id: len(p.hand) for p in game.state.players}
    game.play_phase(lambda _player: 0)

    # 无人翻面 -> 全弃置
    result = game.end_round()
    assert result.no_flip_all_discarded is True
    assert len(result.discarded) == 3
    assert len(result.returned_to_hand) == 0
    assert all(len(p.hand) == starting_hand_sizes[p.player_id] - 1 for p in game.state.players)

    # 再打一轮，仅进攻方翻面 -> 其余回手
    game.play_phase(lambda _player: 0)
    attacker = game.get_player_by_role(Role.ATTACKER)
    game.startup_phase(lambda owner, _placed: owner.player_id == attacker.player_id)
    result2 = game.end_round()
    assert result2.no_flip_all_discarded is False
    assert len(result2.discarded) == 1
    assert len(result2.returned_to_hand) == 2


def test_victory_condition_when_defenders_cannot_play():
    game = CardGame(random.Random(5))
    game.setup_game()

    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)
    support = game.get_player_by_role(Role.SUPPORT)

    pressure.hand.clear()
    support.hand.clear()
    assert attacker.can_play()

    failed = game.check_faction_failure()
    assert failed == "防守方"
    assert game.state.winner == "进攻方"
