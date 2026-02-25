import random

from game.cards import CARD_CONFIGS, CARD_COUNTS, STARTUP_BATCH_ORDER, TOTAL_CARDS, get_batch_priority
from game.engine import CardGame
from game.models import Card, PlacedCard, Role


def make_card(name: str, batch: int, active: bool, priority: int | None = None) -> Card:
    return Card(name=name, activation_batch=batch, batch_priority=(get_batch_priority(name) if priority is None else priority), has_active_flip_effect=active)


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

def test_batch_priority_mapping_mvp_rule_order():
    assert CARD_CONFIGS["天引"].batch_priority < CARD_CONFIGS["快手杰克"].batch_priority
    assert CARD_CONFIGS["哈伯克拉底"].batch_priority < CARD_CONFIGS["夜鸦"].batch_priority < CARD_CONFIGS["女巫扫帚"].batch_priority
    assert CARD_CONFIGS["铁臂祭司"].batch_priority < CARD_CONFIGS["收割"].batch_priority < CARD_CONFIGS["铁手巴特"].batch_priority
    assert CARD_CONFIGS["铁手巴特"].batch_priority == CARD_CONFIGS["圣言巴特"].batch_priority
    assert CARD_CONFIGS["女巫"].batch_priority < CARD_CONFIGS["逻各斯"].batch_priority < CARD_CONFIGS["拨钟"].batch_priority
    assert CARD_CONFIGS["神佑者"].batch_priority > CARD_CONFIGS["拨钟"].batch_priority


def test_attacker_claims_bottom_cards_after_role_assignment():
    game = CardGame(random.Random(11))
    game.setup_game()

    attacker = game.get_player_by_role(Role.ATTACKER)
    assert len(attacker.hand) == 11
    assert all(len(p.hand) == 9 for p in game.state.players if p.role != Role.ATTACKER)
    assert len(game.state.claimed_bottom_cards) == 2
    assert game.state.bottom_cards_claimed is True
    assert len(game.state.bottom_cards) == 0


def test_startup_phase_batch_progression_and_turn_order():
    game = CardGame(random.Random(21))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)
    support = game.get_player_by_role(Role.SUPPORT)

    game.state.battlefield = [
        PlacedCard(owner_id=attacker.player_id, card=make_card("天引", 2, True), visible_to={attacker.player_id}),
        PlacedCard(
            owner_id=pressure.player_id,
            card=make_card("夜鸦", 3, True),
            visible_to={pressure.player_id, support.player_id},
        ),
        PlacedCard(owner_id=support.player_id, card=make_card("铁手巴特", 4, True), visible_to={support.player_id}),
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
        PlacedCard(owner_id=attacker.player_id, card=make_card("快手杰克", 2, True), visible_to={attacker.player_id}),
        PlacedCard(owner_id=support.player_id, card=make_card("神佑者", 5, False), visible_to={support.player_id}),
    ]

    asked_roles = []

    def decider(player, _placed):
        asked_roles.append(player.role)
        return False

    game.startup_phase(decider)

    assert asked_roles == [Role.ATTACKER, Role.SUPPORT]


def test_defeat_force_add_to_defeater_hand_and_remove_from_battlefield():
    game = CardGame(random.Random(1))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)

    source = PlacedCard(owner_id=attacker.player_id, card=make_card("铁手巴特", 4, True), visible_to={attacker.player_id})
    target = PlacedCard(owner_id=pressure.player_id, card=make_card("神佑者", 5, False), visible_to={pressure.player_id})
    game.state.battlefield = [source, target]

    game.startup_phase(lambda _p, _c: True, target_chooser=lambda *_args: 0)

    assert target not in game.state.battlefield
    assert target.card in attacker.hand
    assert id(target.card) in game.state.defeated_this_round


def test_target_list_excludes_owner_battlefield_cards():
    game = CardGame(random.Random(2))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)

    source = PlacedCard(owner_id=attacker.player_id, card=make_card("铁手巴特", 4, True), visible_to={attacker.player_id})
    own_other = PlacedCard(owner_id=attacker.player_id, card=make_card("神佑者", 5, False), visible_to={attacker.player_id})
    enemy = PlacedCard(owner_id=pressure.player_id, card=make_card("死手", 5, False), visible_to={pressure.player_id})
    game.state.battlefield = [source, own_other, enemy]

    captured_candidates = []

    def chooser(_owner, _source, candidates, _mode):
        captured_candidates.extend(candidates)
        return 0

    game.startup_phase(lambda _p, _c: True, target_chooser=chooser)

    assert len(captured_candidates) == 1
    assert captured_candidates[0].owner_id == pressure.player_id




def test_no_target_returns_source_card_to_owner_hand_for_kill_and_poison():
    game = CardGame(random.Random(12))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)

    killer = PlacedCard(owner_id=attacker.player_id, card=make_card("铁手巴特", 4, True), visible_to={attacker.player_id})
    witch = PlacedCard(owner_id=attacker.player_id, card=make_card("女巫", 5, True), visible_to={attacker.player_id})
    game.state.battlefield = [killer, witch]

    attacker_hand_before = len(attacker.hand)
    game.startup_phase(lambda _p, _c: True, target_chooser=lambda *_args: 0)

    assert killer.card in attacker.hand
    assert witch.card in attacker.hand
    assert killer not in game.state.battlefield
    assert witch not in game.state.battlefield
    assert len(attacker.hand) == attacker_hand_before + 2

def test_iron_priest_immune_to_kill_but_not_poison():
    game = CardGame(random.Random(3))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    support = game.get_player_by_role(Role.SUPPORT)

    killer = PlacedCard(owner_id=attacker.player_id, card=make_card("圣言巴特", 4, True), visible_to={attacker.player_id})
    priest = PlacedCard(owner_id=support.player_id, card=make_card("铁臂祭司", 4, False), visible_to={support.player_id})
    game.state.battlefield = [killer, priest]

    # 第4批圣言巴特尝试击杀铁臂祭司 -> 免疫，仍在场上
    game.startup_phase(lambda _p, _c: True, target_chooser=lambda *_args: 0)
    assert any(p.card.name == "铁臂祭司" for p in game.state.battlefield)

    # 直接验证毒杀可生效（不免疫）
    defeated = game._resolve_defeat(attacker, priest, mode="poison")
    assert defeated is True
    assert priest not in game.state.battlefield
    assert any(card.name == "铁臂祭司" for card in attacker.hand)


def test_defeated_this_round_blocks_active_skill_trigger():
    game = CardGame(random.Random(4))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)

    # 让铁手巴特先击败女巫（同为第4/5批关系，女巫在第5批前已被击败）
    killer = PlacedCard(owner_id=attacker.player_id, card=make_card("铁手巴特", 4, True), visible_to={attacker.player_id})
    witch = PlacedCard(owner_id=pressure.player_id, card=make_card("女巫", 5, True), visible_to={pressure.player_id})
    victim = PlacedCard(owner_id=pressure.player_id, card=make_card("神佑者", 5, False), visible_to={pressure.player_id})
    game.state.battlefield = [killer, witch, victim]

    def chooser(_owner, source, candidates, _mode):
        if source.card.name == "铁手巴特":
            return next(i for i, c in enumerate(candidates) if c.card.name == "女巫")
        return next(i for i, c in enumerate(candidates) if c.card.name == "神佑者")

    game.startup_phase(lambda _p, _c: True, target_chooser=chooser)

    assert id(witch.card) in game.state.defeated_this_round
    assert victim in game.state.battlefield


def test_round_end_recovery_rules_with_and_without_flip():
    game = CardGame(random.Random(5))
    game.setup_game()
    starting_hand_sizes = {p.player_id: len(p.hand) for p in game.state.players}
    game.play_phase(lambda _player: 0)

    result = game.end_round()
    assert result.no_flip_all_discarded is True
    assert len(result.discarded) == 3
    assert len(result.returned_to_hand) == 0
    assert all(len(p.hand) == starting_hand_sizes[p.player_id] - 1 for p in game.state.players)


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


def test_night_crow_discards_replenishes_and_resets_startup_phase():
    game = CardGame(random.Random(30))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)

    night_crow = PlacedCard(owner_id=attacker.player_id, card=make_card("夜鸦", 3, True), visible_to={attacker.player_id})
    other = PlacedCard(owner_id=pressure.player_id, card=make_card("神佑者", 5, False), visible_to={pressure.player_id})
    game.state.battlefield = [night_crow, other]
    attacker.hand = [make_card("死手", 5, False)]

    batch_trace = []
    reveals = []
    game.startup_phase(
        lambda _p, _c: True,
        on_batch_start=batch_trace.append,
        replenish_chooser=lambda _player: 0,
        on_reveal_battlefield=lambda _player, battlefield: reveals.append(len(battlefield)),
    )

    assert night_crow.card in game.state.discard_pile
    assert len(reveals) == 1
    assert any(p.owner_id == attacker.player_id and p.card.name == "死手" for p in game.state.battlefield)
    assert batch_trace[:4] == [2, 3, 2, 3]


def test_hippocrates_silences_target_discards_replenishes_and_resets():
    game = CardGame(random.Random(31))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    support = game.get_player_by_role(Role.SUPPORT)

    hippocrates = PlacedCard(owner_id=attacker.player_id, card=make_card("哈伯克拉底", 3, True), visible_to={attacker.player_id})
    saint = PlacedCard(owner_id=attacker.player_id, card=make_card("圣言巴特", 4, True), visible_to={attacker.player_id})
    priest = PlacedCard(owner_id=support.player_id, card=make_card("铁臂祭司", 4, False), visible_to={support.player_id})
    game.state.battlefield = [hippocrates, saint, priest]
    attacker.hand = [make_card("神佑者", 5, False)]

    batch_trace = []

    def chooser(_owner, _source, candidates, mode):
        if mode == "silence":
            return next(i for i, c in enumerate(candidates) if c.card.name == "铁臂祭司")
        if mode == "kill":
            return 0
        return None

    game.startup_phase(
        lambda _p, _c: True,
        on_batch_start=batch_trace.append,
        target_chooser=chooser,
        replenish_chooser=lambda _player: 0,
    )

    assert hippocrates.card in game.state.discard_pile
    assert batch_trace[:4] == [2, 3, 2, 3]
    assert any(p.owner_id == attacker.player_id and p.card.name == "神佑者" for p in game.state.battlefield)
    assert priest.card in attacker.hand  # 被沉默后，免疫被移除，可被圣言巴特击杀


def test_silence_cleared_after_round_end():
    game = CardGame(random.Random(32))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    support = game.get_player_by_role(Role.SUPPORT)

    silenced_target = PlacedCard(owner_id=support.player_id, card=make_card("铁臂祭司", 4, False), visible_to={support.player_id})
    game.state.battlefield = [silenced_target]
    game.state.silenced_this_round.add(id(silenced_target.card))

    game.end_round()

    assert game.state.silenced_this_round == set()


def test_fast_jack_draw_two_choose_one_to_battlefield_face_down_and_reset():
    game = CardGame(random.Random(100))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)

    fast_jack = PlacedCard(owner_id=attacker.player_id, card=make_card("快手杰克", 2, True), visible_to={attacker.player_id})
    other = PlacedCard(owner_id=pressure.player_id, card=make_card("神佑者", 5, False), visible_to={pressure.player_id})
    game.state.battlefield = [fast_jack, other]

    pressure.hand = [
        make_card("死手", 5, False),
        make_card("逻各斯", 5, True),
        make_card("女巫", 5, True),
    ]

    shown_records = []
    batches = []

    def choose_target_player(_owner, _source, players):
        return next(i for i, p in enumerate(players) if p.player_id == pressure.player_id)

    def choose_revealed(_owner, _source, _target_player, shown_cards):
        shown_records.append([c.name for c in shown_cards])
        return 0

    game.startup_phase(
        lambda _p, placed: placed.card.name == "快手杰克",
        on_batch_start=batches.append,
        target_player_chooser=choose_target_player,
        revealed_card_chooser=choose_revealed,
    )

    assert len(shown_records) == 1
    selected_name = shown_records[0][0]
    assert selected_name not in [c.name for c in pressure.hand]
    placed_selected = next(p for p in game.state.battlefield if p.owner_id == attacker.player_id and p.card.name == selected_name)
    assert placed_selected.face_up is False
    assert fast_jack.card in game.state.discard_pile
    assert batches[:2] == [2, 2]


def test_fast_jack_no_target_when_selected_player_has_empty_hand_returns_to_hand_no_reset():
    game = CardGame(random.Random(101))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)

    fast_jack = PlacedCard(owner_id=attacker.player_id, card=make_card("快手杰克", 2, True), visible_to={attacker.player_id})
    filler = PlacedCard(owner_id=pressure.player_id, card=make_card("神佑者", 5, False), visible_to={pressure.player_id})
    game.state.battlefield = [fast_jack, filler]
    pressure.hand = []

    reset_marks = []

    game.startup_phase(
        lambda _p, _c: True,
        target_player_chooser=lambda _owner, _source, _players: 0,
        revealed_card_chooser=lambda *_args: 0,
        on_startup_reset=lambda b: reset_marks.append(b),
    )

    assert fast_jack.card in attacker.hand
    assert fast_jack.card not in game.state.discard_pile
    assert reset_marks == []


def test_tianyin_cannot_target_itself_and_can_pull_other_battlefield_card():
    game = CardGame(random.Random(102))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)

    tianyin = PlacedCard(owner_id=attacker.player_id, card=make_card("天引", 2, True), visible_to={attacker.player_id})
    target = PlacedCard(owner_id=pressure.player_id, card=make_card("死手", 5, False), visible_to={pressure.player_id})
    game.state.battlefield = [tianyin, target]

    seen_candidates = []

    def chooser(_owner, _source, candidates, mode):
        if mode == "tianyin":
            seen_candidates.extend(candidates)
            return 0
        return 0

    game.startup_phase(lambda _p, _c: True, target_chooser=chooser)

    assert all(c is not tianyin for c in seen_candidates)
    assert target.card in attacker.hand
    assert target not in game.state.battlefield
    assert tianyin.card in game.state.discard_pile


def test_tianyin_no_candidate_returns_to_hand():
    game = CardGame(random.Random(103))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)

    tianyin = PlacedCard(owner_id=attacker.player_id, card=make_card("天引", 2, True), visible_to={attacker.player_id})
    game.state.battlefield = [tianyin]

    game.startup_phase(lambda _p, _c: True, target_chooser=lambda *_args: 0)

    assert tianyin.card in attacker.hand
    assert tianyin.card not in game.state.discard_pile


def test_batch2_priority_order_tianyin_before_fast_jack_even_after_reset():
    game = CardGame(random.Random(120))
    game.setup_game()
    attacker = game.get_player_by_role(Role.ATTACKER)
    pressure = game.get_player_by_role(Role.PRESSURE)

    fast_jack = PlacedCard(owner_id=attacker.player_id, card=make_card("快手杰克", 2, True), visible_to={attacker.player_id})
    tianyin = PlacedCard(owner_id=pressure.player_id, card=make_card("天引", 2, True), visible_to={pressure.player_id})
    extra = PlacedCard(owner_id=attacker.player_id, card=make_card("神佑者", 5, False), visible_to={attacker.player_id})
    game.state.battlefield = [fast_jack, tianyin, extra]
    attacker.hand = [make_card("死手", 5, False)]
    pressure.hand = [make_card("逻各斯", 5, True)]

    batch2_order = []
    current_batch = {"value": None}

    def on_batch(batch):
        current_batch["value"] = batch

    def flip_decider(_player, _placed):
        return True

    def target_chooser(_owner, source, candidates, mode):
        if current_batch["value"] == 2 and mode in {"tianyin", "kill", "poison"}:
            batch2_order.append(source.card.name)
        if mode == "tianyin":
            return next(i for i, c in enumerate(candidates) if c.card.name == "神佑者")
        return 0

    def target_player_chooser(_owner, source, players):
        if current_batch["value"] == 2:
            batch2_order.append(source.card.name)
        return 0

    game.startup_phase(
        flip_decider,
        on_batch_start=on_batch,
        target_chooser=target_chooser,
        target_player_chooser=target_player_chooser,
        revealed_card_chooser=lambda *_args: 0,
        on_startup_reset=lambda _b: None,
    )

    assert batch2_order[0] == "天引"
