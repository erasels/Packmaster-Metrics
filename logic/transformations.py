removable_prefix: str = "anniv5:"


def del_prefix(cardName: str) -> str:
    return cardName.replace(removable_prefix, "")


def del_upg(cardName: str) -> str:
    return cardName.split('+')[0]


def add_pack_prefix(cardName: str, cards_to_packs: dict, keep_upgrade: bool = True) -> str:
    new_prefix = del_prefix(cards_to_packs.get(del_upg(cardName)))
    if keep_upgrade:
        return new_prefix + del_prefix(del_upg(cardName))
    return new_prefix + del_prefix(cardName)

