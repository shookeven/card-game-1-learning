from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set


class Role(Enum):
    ATTACKER = "进攻方"
    PRESSURE = "抗压位"
    SUPPORT = "支援位"


@dataclass
class Card:
    name: str
    activation_batch: int
    has_active_flip_effect: bool = False


@dataclass
class PlacedCard:
    owner_id: int
    card: Card
    face_up: bool = False
    visible_to: Set[int] = field(default_factory=set)


@dataclass
class Player:
    player_id: int
    hand: List[Card] = field(default_factory=list)
    role: Optional[Role] = None

    def can_play(self) -> bool:
        return len(self.hand) > 0


@dataclass
class GameState:
    players: List[Player]
    deck: List[Card]
    bottom_cards: List[Card] = field(default_factory=list)
    revealed_bottom_cards: List[Card] = field(default_factory=list)
    claimed_bottom_cards: List[Card] = field(default_factory=list)
    bottom_cards_claimed: bool = False
    battlefield: List[PlacedCard] = field(default_factory=list)
    discard_pile: List[Card] = field(default_factory=list)
    defeated_this_round: Set[int] = field(default_factory=set)
    silenced_this_round: Set[int] = field(default_factory=set)
    round_number: int = 1
    winner: Optional[str] = None
