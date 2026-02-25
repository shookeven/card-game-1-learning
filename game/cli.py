from __future__ import annotations

from .engine import CardGame
from .models import PlacedCard, Player, Role


def choose_card_interactive(player: Player) -> int:
    print(f"\n玩家{player.player_id}（{player.role.value}）手牌：")
    for idx, card in enumerate(player.hand):
        print(f"  [{idx}] {card.name}")
    while True:
        raw = input(f"玩家{player.player_id} 请选择要背面放置的手牌索引: ").strip()
        if raw.isdigit() and 0 <= int(raw) < len(player.hand):
            return int(raw)
        print("输入无效，请重试。")


def choose_replenish_card_interactive(player: Player) -> int:
    print(f"玩家{player.player_id} 需要立刻补放1张背面牌：")
    for idx, card in enumerate(player.hand):
        print(f"  [{idx}] {card.name}")
    while True:
        raw = input("请选择补放手牌索引: ").strip()
        if raw.isdigit() and 0 <= int(raw) < len(player.hand):
            return int(raw)
        print("输入无效，请重试。")


def decide_flip_interactive(player: Player, placed: PlacedCard) -> bool:
    while True:
        raw = input(f"玩家{player.player_id} 是否翻面自己的牌《{placed.card.name}》? (y/n): ").strip().lower()
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("请输入 y 或 n。")


def choose_skill_target_interactive(
    player: Player,
    source: PlacedCard,
    candidates: list[PlacedCard],
    mode: str,
) -> int | None:
    if mode == "kill":
        action_text = "击杀"
        extra = "（默认不包含自己的战场牌）"
    elif mode == "poison":
        action_text = "毒杀"
        extra = "（默认不包含自己的战场牌）"
    else:
        action_text = "沉默"
        extra = "（可选任意场上牌，含友方）"

    print(f"玩家{player.player_id} 的《{source.card.name}》触发技能：请选择{action_text}目标{extra}")
    if not candidates:
        print("没有可选目标：该牌回到你的手牌。")
        return None
    for idx, target in enumerate(candidates):
        print(f"  [{idx}] 玩家{target.owner_id} 的《{target.card.name}》")
    while True:
        raw = input("输入目标索引（留空取消）：").strip()
        if raw == "":
            return None
        if raw.isdigit() and 0 <= int(raw) < len(candidates):
            return int(raw)
        print("输入无效，请重试。")


def reveal_battlefield_once(player: Player, battlefield: list[PlacedCard]) -> None:
    print(f"玩家{player.player_id} 通过夜鸦查看战场：")
    for placed in battlefield:
        print(f"  - 玩家{placed.owner_id}：《{placed.card.name}》")


def run_cli_game() -> None:
    game = CardGame()
    game.setup_game()

    print("=== 3人卡牌小游戏（MVP-0）===")
    print("底牌（公开可见）：", ", ".join(game.bottom_card_names()))
    for p in game.state.players:
        print(f"玩家{p.player_id} 角色：{p.role.value}")

    attacker = game.get_player_by_role(Role.ATTACKER)
    claimed = ", ".join(card.name for card in game.state.claimed_bottom_cards)
    print(f"进攻方玩家{attacker.player_id} 领取底牌：{claimed}（手牌 {len(attacker.hand)} 张）")

    while True:
        failed = game.check_faction_failure()
        if failed:
            if failed == "平局":
                print("\n双方均无牌可出，游戏平局！")
            else:
                print(f"\n{failed}无牌可出，游戏结束！胜利方：{game.state.winner}")
            break

        print(f"\n--- 第 {game.state.round_number} 回合 ---")
        placed = game.play_phase(choose_card_interactive)
        print("出牌完成（均为背面）。")

        pressure = game.get_player_by_role(Role.PRESSURE)
        for c in placed:
            if c.owner_id == pressure.player_id:
                print(f"支援位提示：你可见抗压位放置的是《{c.card.name}》。")

        game.startup_phase(
            decide_flip_interactive,
            on_batch_start=lambda b: print(f"进入第{b}批次"),
            target_chooser=choose_skill_target_interactive,
            replenish_chooser=choose_replenish_card_interactive,
            on_reveal_battlefield=reveal_battlefield_once,
            on_startup_reset=lambda b: print(f"启动阶段已重置，重新从第{b}批开始"),
        )
        result = game.end_round()

        if result.no_flip_all_discarded:
            print("本回合无人翻面：战场牌全部进入弃牌区。")
        else:
            print(f"翻面弃置 {len(result.discarded)} 张；未翻面回手 {len(result.returned_to_hand)} 张。")
        print(f"当前弃牌区总数：{len(game.state.discard_pile)}")
