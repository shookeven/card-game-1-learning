import random

from game.cards import CARD_CONFIGS, CARD_COUNTS, STARTUP_BATCH_ORDER, TOTAL_CARDS
from game.engine import CardGame
from game.models import Card, PlacedCard, Role


def test_card_definition_matches_official_pool():
    expected = {
        "天引": 1,
        "快手杰克": 1,
        "收割": 1,
        "圣言巴特": 1,
        "末日布道者": 1,
        "女巫扫帚": 2,
        "铁臂祭司": 2,
        "拨钟": 2,
        "逻各斯": 2,
        "死手": 2,
        "夜鸦": 2,
        "女巫": 2,
        "哈伯克拉底": 2,
        "铁手巴特": 4,
        "神佑者": 4,
    }
    assert CARD_COUNTS == expected
    assert sum(CARD_COUNTS.values()) == TOTAL_CARDS == 29


def test_activation_batch_mapping_minimum_spec():
    assert CARD_CONFIGS["天引"].activation_batch == 2
    assert CARD_CONFIGS["快手杰克"].activation_batch == 2
    assert CARD_CONFIGS["哈伯克拉底"].activation_batch == 3
    assert CARD_CONFIGS["夜鸦"].activation_batch == 3
    assert CARD_CONFIGS["女巫扫帚"].activation_batch == 3
    assert CARD_CONFIGS["铁臂祭司"].activation_batch == 4
    assert CARD_CONFIGS["收割"].activation_batch == 4
    assert CARD_CONFIGS["铁手巴特"].activation_batch == 4
    assert CARD_CONFIGS["圣言巴特"].activation_batch == 4
    assert CARD_CONFIGS["女巫"].activation_batch == 5
    assert CARD_CONFIGS["逻各斯"].activation_batch == 5
    assert CARD_CONFIGS["拨钟"].activation_batch == 5
    assert CARD_CONFIGS["神佑者"].activation_batch == 5
    assert CARD_CONFIGS["末日布道者"].activation_batch == 5


def test_attacker_claims_bottom_cards_after_role_assignment():
    game = CardGame(random.Random(11))
    game.setup_game()

    attacker = game.get_player_by_role(Role.ATTACKER)
    assert len(attacker.hand) == 11
    assert all(len(p.hand) == 9 for p in game.state.players if p.role != Role.ATTACKER)
    assert len(game.state.claimed_bottom_cards) == 2
    assert game.state.bottom_cards_claimed is True
    assert len(game.state.bottom_cards) == 0


def test_deal_counts_are_correct_after_bottom_claim():
    game = CardGame(random.Random(1))
    game.setup_game()

    assert sum(CARD_COUNTS.values()) == 29
    assert len(game.state.deck) == 0
    assert sum(len(p.hand) for p in game.state.players) == 29


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


def test_startup_phase_batch_progression_and_turn_order():
    game = CardGame(random.Random(21))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)
    support = game.get_player_by_role(Role.SUPPORT)

    game.state.battlefield = [
        PlacedCard(
            owner_id=attacker.player_id,
            card=Card(name="天引", activation_batch=2, has_active_flip_effect=True),
            visible_to={attacker.player_id},
        ),
        PlacedCard(
            owner_id=pressure.player_id,
            card=Card(name="夜鸦", activation_batch=3, has_active_flip_effect=True),
            visible_to={pressure.player_id, support.player_id},
        ),
        PlacedCard(
            owner_id=support.player_id,
            card=Card(name="铁手巴特", activation_batch=4, has_active_flip_effect=True),
            visible_to={support.player_id},
        ),
    ]

    seen_batches = []
    asked = []

    def decider(player, placed):
        asked.append((player.role, placed.card.activation_batch, placed.card.name))
        return False

    game.startup_phase(decider, on_batch_start=seen_batches.append)

    assert seen_batches == STARTUP_BATCH_ORDER
    assert asked == [
        (Role.ATTACKER, 2, "天引"),
        (Role.PRESSURE, 3, "夜鸦"),
        (Role.SUPPORT, 4, "铁手巴特"),
    ]


def test_startup_phase_skips_players_without_current_batch_cards():
    game = CardGame(random.Random(22))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    support = game.get_player_by_role(Role.SUPPORT)

    game.state.battlefield = [
        PlacedCard(
            owner_id=attacker.player_id,
            card=Card(name="快手杰克", activation_batch=2, has_active_flip_effect=True),
            visible_to={attacker.player_id},
        ),
        PlacedCard(
            owner_id=support.player_id,
            card=Card(name="神佑者", activation_batch=5, has_active_flip_effect=False),
            visible_to={support.player_id},
        ),
    ]

    asked_roles = []

    def decider(player, _placed):
        asked_roles.append(player.role)
        return False

    game.startup_phase(decider)

    assert asked_roles == [Role.ATTACKER, Role.SUPPORT]


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


def test_draw_when_all_players_cannot_play():
    game = CardGame(random.Random(6))
    game.setup_game()

    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)
    support = game.get_player_by_role(Role.SUPPORT)

    attacker.hand.clear()
    pressure.hand.clear()
    support.hand.clear()

    failed = game.check_faction_failure()
    assert failed == "平局"
    assert game.state.winner == "平局"
