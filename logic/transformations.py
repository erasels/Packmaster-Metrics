removable_prefix: str = "anniv5:"


def del_prefix(cardName: str) -> str:
    return cardName.replace(removable_prefix, "")


def del_upg(cardName: str) -> str:
    return cardName.split('+')[0]


def add_pack_prefix(cardName: str, card_to_pack: dict, keep_upgrade: bool = True) -> str:
    new_prefix = del_prefix(card_to_pack.get(del_upg(cardName)))
    if keep_upgrade:
        return new_prefix + ":" + del_prefix(del_upg(cardName))
    return new_prefix + ":" + del_prefix(cardName)


def make_ratio(positive: int, total: int) -> str:
    rate = (positive / total) * 100 if total > 0 else 0.0
    return f"{rate:.2f}"
