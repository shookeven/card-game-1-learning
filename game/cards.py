from __future__ import annotations

from typing import Dict

# 正式 29 张牌定义（仅名称与数量）
CARD_COUNTS: Dict[str, int] = {
    # 传说
    "天引": 1,
    "快手杰克": 1,
    "收割": 1,
    "圣言巴特": 1,
    "末日布道者": 1,
    # 珍贵
    "女巫扫帚": 2,
    "铁臂祭司": 2,
    "拨钟": 2,
    "逻各斯": 2,
    "死手": 2,
    "夜鸦": 2,
    "女巫": 2,
    "哈伯克拉底": 2,
    # 普通
    "铁手巴特": 4,
    "神佑者": 4,
}

TOTAL_CARDS = 29
