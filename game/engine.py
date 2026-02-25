from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

from .cards import CARD_COUNTS
from .models import Card, GameState, PlacedCard, Player, Role

PLAY_ORDER = [Role.ATTACKER, Role.PRESSURE, Role.SUPPORT]


@dataclass
class RoundResult:
    discarded: List[Card]
    returned_to_hand: List[Card]
    no_flip_all_discarded: bool


class CardGame:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self.state = GameState(players=[Player(1), Player(2), Player(3)], deck=[])

    def build_deck(self) -> List[Card]:
        deck: List[Card] = []
        for name, count in CARD_COUNTS.items():
            deck.extend(Card(name=name) for _ in range(count))
        return deck

    def setup_game(self) -> None:
        deck = self.build_deck()
        self.rng.shuffle(deck)
        self.state.deck = deck

        for _ in range(9):
            for player in self.state.players:
                player.hand.append(self.state.deck.pop())

        self.state.bottom_cards = [self.state.deck.pop(), self.state.deck.pop()]
        self.state.revealed_bottom_cards = list(self.state.bottom_cards)
        self.assign_roles()
        self.claim_bottom_cards_for_attacker()

    def claim_bottom_cards_for_attacker(self) -> None:
        if self.state.bottom_cards_claimed:
            return
        attacker = self.get_player_by_role(Role.ATTACKER)
        claimed = list(self.state.bottom_cards)
        attacker.hand.extend(claimed)
        self.state.claimed_bottom_cards = claimed
        self.state.bottom_cards = []
        self.state.bottom_cards_claimed = True

    def assign_roles(self) -> None:
        attacker: Optional[Player] = None
        for player in self.state.players:
            if any(card.name == "快手杰克" for card in player.hand):
                attacker = player
                break
        if attacker is None:
            attacker = self.rng.choice(self.state.players)

        for player in self.state.players:
            player.role = None

        attacker.role = Role.ATTACKER
        defenders = [p for p in self.state.players if p is not attacker]
        defenders.sort(key=lambda p: p.player_id)
        defenders[0].role = Role.PRESSURE
        defenders[1].role = Role.SUPPORT

    def get_player_by_role(self, role: Role) -> Player:
        return next(p for p in self.state.players if p.role == role)

    def check_faction_failure(self) -> Optional[str]:
        attacker = self.get_player_by_role(Role.ATTACKER)
        pressure = self.get_player_by_role(Role.PRESSURE)
        support = self.get_player_by_role(Role.SUPPORT)

        attacker_cannot_play = not attacker.can_play()
        defenders_cannot_play = (not pressure.can_play()) and (not support.can_play())

        if attacker_cannot_play and defenders_cannot_play:
            self.state.winner = "平局"
            return "平局"
        if attacker_cannot_play:
            self.state.winner = "防守方"
            return "进攻方"
        if defenders_cannot_play:
            self.state.winner = "进攻方"
            return "防守方"
        return None

    def play_phase(self, chooser: Callable[[Player], int]) -> List[PlacedCard]:
        if self.check_faction_failure() is not None:
            return []

        self.state.battlefield = []
        for role in PLAY_ORDER:
            player = self.get_player_by_role(role)
            if not player.can_play():
                continue
            index = chooser(player)
            if index < 0 or index >= len(player.hand):
                raise ValueError(f"玩家{player.player_id} 选择的手牌索引无效: {index}")
            card = player.hand.pop(index)
            placed = PlacedCard(owner_id=player.player_id, card=card, face_up=False, visible_to={player.player_id})
            self.state.battlefield.append(placed)

            if role == Role.PRESSURE:
                support = self.get_player_by_role(Role.SUPPORT)
                placed.visible_to.add(support.player_id)

        return self.state.battlefield

    def startup_phase(self, flip_decider: Callable[[Player, PlacedCard], bool]) -> None:
        for placed in self.state.battlefield:
            owner = next(p for p in self.state.players if p.player_id == placed.owner_id)
            if flip_decider(owner, placed):
                placed.face_up = True

    def end_round(self) -> RoundResult:
        discarded: List[Card] = []
        returned: List[Card] = []
        any_flipped = any(placed.face_up for placed in self.state.battlefield)

        if not any_flipped:
            for placed in self.state.battlefield:
                discarded.append(placed.card)
            self.state.discard_pile.extend(discarded)
            self.state.battlefield = []
            self.state.round_number += 1
            return RoundResult(discarded=discarded, returned_to_hand=returned, no_flip_all_discarded=True)

        for placed in self.state.battlefield:
            if placed.face_up:
                discarded.append(placed.card)
                self.state.discard_pile.append(placed.card)
            else:
                returned.append(placed.card)
                owner = next(p for p in self.state.players if p.player_id == placed.owner_id)
                owner.hand.append(placed.card)

        self.state.battlefield = []
        self.state.round_number += 1
        return RoundResult(discarded=discarded, returned_to_hand=returned, no_flip_all_discarded=False)

    def player_role_map(self) -> Dict[int, Role]:
        return {p.player_id: p.role for p in self.state.players}

    def bottom_card_names(self) -> Sequence[str]:
        return [c.name for c in self.state.revealed_bottom_cards]
