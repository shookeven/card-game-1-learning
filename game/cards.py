from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CardConfig:
    count: int
    activation_batch: int
    has_active_flip_effect: bool


# 正式 29 张牌定义（名称、数量、启动批次）
# 拨钟加速/减速导致的第1/第6批仅预留接口，当前均按基础批次处理。
CARD_CONFIGS: Dict[str, CardConfig] = {
    # 传说
    "天引": CardConfig(count=1, activation_batch=2, has_active_flip_effect=True),
    "快手杰克": CardConfig(count=1, activation_batch=2, has_active_flip_effect=True),
    "收割": CardConfig(count=1, activation_batch=4, has_active_flip_effect=True),
    "圣言巴特": CardConfig(count=1, activation_batch=4, has_active_flip_effect=True),
    "末日布道者": CardConfig(count=1, activation_batch=5, has_active_flip_effect=False),
    # 珍贵
    "女巫扫帚": CardConfig(count=2, activation_batch=3, has_active_flip_effect=True),
    "铁臂祭司": CardConfig(count=2, activation_batch=4, has_active_flip_effect=True),
    "拨钟": CardConfig(count=2, activation_batch=5, has_active_flip_effect=True),
    "逻各斯": CardConfig(count=2, activation_batch=5, has_active_flip_effect=True),
    "死手": CardConfig(count=2, activation_batch=5, has_active_flip_effect=False),
    "夜鸦": CardConfig(count=2, activation_batch=3, has_active_flip_effect=True),
    "女巫": CardConfig(count=2, activation_batch=5, has_active_flip_effect=True),
    "哈伯克拉底": CardConfig(count=2, activation_batch=3, has_active_flip_effect=True),
    # 普通
    "铁手巴特": CardConfig(count=4, activation_batch=4, has_active_flip_effect=True),
    "神佑者": CardConfig(count=4, activation_batch=5, has_active_flip_effect=False),
}

CARD_COUNTS: Dict[str, int] = {name: config.count for name, config in CARD_CONFIGS.items()}
TOTAL_CARDS = 29
STARTUP_BATCH_ORDER = [2, 3, 4, 5]


def get_activation_batch(card_name: str) -> int:
    return CARD_CONFIGS[card_name].activation_batch


def has_active_flip_effect(card_name: str) -> bool:
    return CARD_CONFIGS[card_name].has_active_flip_effect
