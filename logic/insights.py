import re
import statistics
from collections import Counter
from collections import defaultdict

from logic.transformations import *


# Counts the number of packs filtered by each player and prints the most common ones.
def sum_filtered_packs(runs: list[dict]) -> dict:
    word_counts = Counter()
    host_word_counts = {}

    for data_dict in runs:
        host = data_dict.get("host")
        filtered_packs = data_dict.get("filteredPacks", "")

        if not host or not filtered_packs:
            continue

        if host not in host_word_counts:
            host_word_counts[host] = Counter()

        words = filtered_packs.split(",")

        # Count words that haven't been counted for this host before
        new_words = [word for word in words if word not in host_word_counts[host]]
        word_counts.update(new_words)

        # Update host_word_counts for this host with the newly counted words
        host_word_counts[host].update(new_words)

    # Create the data rows sorted by the most filtered packs
    sorted_packs = sorted(word_counts.items(), key=lambda item: item[1], reverse=True)
    data_rows = [[del_prefix(pack), count] for pack, count in sorted_packs]

    insights = {
        "Blacklisted Packs": {
            "description": "How often a pack is blacklisted by unique hosts",
            "headers": ["Pack", "Blacklisted"],
            "data": data_rows
        }
    }

    return insights


# Counts the number of runs with enabledExpansionPacks and prints the ratio.
def count_enabled_expansion_packs(runs: list[dict]) -> dict:
    enabled_count = 0
    total_count = len(runs)

    for data_dict in runs:
        if data_dict.get("enabledExpansionPacks"):
            enabled_count += 1

    ratio = make_ratio(enabled_count, total_count)

    # Construct the insights dictionary for this particular analysis
    insights = {
        "Expansion Pack Usage": {
            "description": "Percentage of runs with expansion packs enabled",
            "headers": ["Enabled", "Total Runs", "Percentage Enabled"],
            "data": [
                [enabled_count, total_count, ratio]
            ]
        }
    }

    return insights


# Counts the number of times each pack was picked and prints the results.
def pack_pick_rate(runs: list[dict]) -> dict:
    picked_counts = Counter()
    not_picked_counts = Counter()
    result = []

    for data_dict in runs:
        pack_choices = data_dict.get("packChoices", [])
        for choice in pack_choices:
            picked = choice.get("picked", "")
            not_picked = choice.get("not_picked", [])

            # Count picked choices
            picked_counts.update([picked])

            # Count not picked choices
            not_picked_counts.update(not_picked)

    for choice, picked_count in picked_counts.items():
        not_picked_count = not_picked_counts[choice]
        total_count = picked_count + not_picked_count
        pick_rate = make_ratio(picked_count, total_count)
        result.append([del_prefix(choice), picked_count, total_count, pick_rate])

    # Sort the results by pick rate
    sorted_result = sorted(result, key=lambda x: float(x[3]), reverse=True)

    insights = {
        "Pack Pick Rate": {
            "description": "How often a pack is picked",
            "headers": ["Pack", "Picked", "Seen", "Pick Rate"],
            "data": sorted_result
        }
    }

    return insights


def count_most_common_players(runs: list[dict]) -> dict:
    host_counts = Counter()

    for data_dict in runs:
        host = data_dict.get("host")
        if host:
            host_counts[host] += 1

    most_common_hosts = host_counts.most_common()

    insights = {
        "Runs by Host": {
            "description": "Number of runs for hosts with at least 20 runs",
            "headers": ["Host", "Runs"],
            "data": []
        }
    }

    # Populate the data list with hosts that meet the threshold
    for host, count in most_common_hosts:
        if count >= 20:
            insights["Runs by Host"]["data"].append([host, count])

    return insights


def hat_pick_rate(runs: list[dict]) -> dict:
    picked_hat_counts = Counter()

    for data_dict in runs:
        picked_hat = data_dict.get("pickedHat")
        if picked_hat:
            picked_hat_counts[picked_hat] += 1

    total_runs = len(runs)
    insights = {
        "Hat Pick Rate": {
            "description": "Pick rate for each hat",
            "headers": ["Hat", "Count", "Pick Rate"],
            "data": []
        }
    }

    # Populate the data part of the insights dictionary
    for picked_hat, count in picked_hat_counts.most_common():
        pick_rate = make_ratio(count, total_runs)
        insights["Hat Pick Rate"]["data"].append([del_prefix(picked_hat), count, pick_rate])

    return insights


def pack_win_rate(runs: list[dict]) -> dict:
    pack_wins = {}
    pack_runs = {}

    for data_dict in runs:
        victory = data_dict.get("victory", False)
        current_packs = data_dict.get("currentPacks", "").split(",")

        for pack in current_packs:
            if pack:
                pack_wins[pack] = pack_wins.get(pack, 0) + int(victory)
                pack_runs[pack] = pack_runs.get(pack, 0) + 1

    sorted_packs = sorted(
        pack_wins.keys(),
        key=lambda pack: (pack_wins[pack] / pack_runs[pack] if pack_runs[pack] > 0 else 0),
        reverse=True
    )

    insights = {
        "Pack Win Rate": {
            "description": "Win rate for each pack",
            "headers": ["Pack", "Wins", "Total", "Win Rate"],
            "data": []
        }
    }

    for pack in sorted_packs:
        wins = pack_wins[pack]
        total_runs = pack_runs.get(pack, 0)
        win_rate = make_ratio(wins, total_runs)
        insights["Pack Win Rate"]["data"].append([del_prefix(pack), wins, total_runs, win_rate])

    return insights


# Count card picks of current run cards (counts upgraded cards seperately)
def card_pick_rate(runs: list[dict], card_to_pack: dict, card_to_rarity: dict) -> dict:
    picked_counts = Counter()
    not_picked_counts = Counter()
    result = []

    for data_dict in runs:
        current_packs = set(data_dict.get("currentPacks", "").split(","))
        card_choices = data_dict.get("card_choices", [])
        for choice in card_choices:
            picked = del_upg(choice.get("picked"))
            not_picked = [del_upg(card) for card in choice.get("not_picked", [])]
            picked_counts.update([picked])
            not_picked_counts.update(not_picked)

    for choice, picked_count in picked_counts.items():
        rar = card_to_rarity.get(choice, "Unknown")
        if rar != "Special" and card_to_pack.get(choice):
            not_picked_count = not_picked_counts[choice]
            total_count = picked_count + not_picked_count
            pick_rate = make_ratio(picked_count, total_count)

            result.append([rar,
                           del_prefix(card_to_pack.get(choice)),
                           del_prefix(choice),
                           picked_count,
                           not_picked_count + picked_count,
                           pick_rate])

    # Sort the results by pick rate in descending order
    sorted_result = sorted(result, key=lambda x: float(x[5]), reverse=True)

    insights = {
        "Card Pick Rate": {
            "description": "How often a card is picked when offered as a card reward",
            "headers": ["Rarity", "Pack", "Card", "Picked", "Seen", "Pick Rate"],
            "data": sorted_result
        }
    }

    return insights


# Create a dictionary to store wins and total runs per ascension level
def count_win_rates_per_asc(runs: list[dict]) -> dict:
    ascension_stats = {}
    all_stats = {"wins": 0, "total_runs": 0}

    for data_dict in runs:
        if "victory" in data_dict:
            ascension_level = data_dict.get("ascension_level", 0)
            victory = data_dict["victory"]

            # Initialize the statistics for the ascension level if not already present
            if ascension_level not in ascension_stats:
                ascension_stats[ascension_level] = {"wins": 0, "total_runs": 0}

            # Update statistics based on victory
            ascension_stats[ascension_level]["total_runs"] += 1
            all_stats["total_runs"] += 1
            if victory:
                ascension_stats[ascension_level]["wins"] += 1
                all_stats["wins"] += 1

    # Sort ascension levels in ascending order
    sorted_ascension_levels = sorted(
        (level for level in ascension_stats.keys() if 0 <= int(level) <= 20),
        key=lambda x: int(x)
    )

    insights = {
        "Win Rate by Ascension Level": {
            "description": "Win rate for each ascension level",
            "headers": ["Ascension Level", "Won", "Total", "Win Rate"],
            "data": []
        }
    }

    # Overall win rate calculation
    total_win_rate = make_ratio(all_stats['wins'], all_stats['total_runs'])
    insights["Win Rate by Ascension Level"]["data"].append(
        ["Overall", all_stats['wins'], all_stats['total_runs'], total_win_rate]
    )

    # Win rates per ascension level  (skipping ascs with less than 100 runs)
    for ascension_level in sorted_ascension_levels:
        stats = ascension_stats[ascension_level]
        if stats["total_runs"] > 100:
            win_rate = make_ratio(stats["wins"], stats["total_runs"])
            insights["Win Rate by Ascension Level"]["data"].append([ascension_level, stats["wins"], stats["total_runs"], win_rate])

    return insights


def median_deck_sizes(runs: list[dict]) -> dict:
    # Create a dictionary to store deck sizes of victorious runs per ascension level
    ascension_deck_sizes = {}
    total_deck_sizes = []

    for data_dict in runs:
        # Check if the dictionary contains a "victory" key and it's True
        if data_dict.get("victory", False):
            ascension_level = data_dict.get("ascension_level", "Unknown")
            master_deck = data_dict.get("master_deck", [])
            deck_size = len(master_deck)

            # Initialize the list for the ascension level if not already present
            if ascension_level not in ascension_deck_sizes:
                ascension_deck_sizes[ascension_level] = []

            ascension_deck_sizes[ascension_level].append(deck_size)
            total_deck_sizes.append(deck_size)

    # Sort ascension levels, handling "Unknown" by using a default value for sorting
    sorted_ascension_levels = sorted(
        ascension_deck_sizes.keys(),
        key=lambda x: int(x) if x != "Unknown" else float("inf")
    )

    data = [
        ["Overall", statistics.median(total_deck_sizes)]
    ]
    for ascension_level in sorted_ascension_levels:
        median_size = statistics.median(ascension_deck_sizes[ascension_level])
        data.append([ascension_level, median_size])

    insights = {
        "Median Deck Sizes": {
            "description": "Median deck size of winning runs for each ascension level",
            "headers": ["Ascension Level", "Median Deck Size"],
            "data": data
        }
    }

    return insights


def card_win_rate(runs: list[dict], card_to_pack: dict, card_to_rarity: dict) -> dict:
    # Create a dictionary to store the number of wins and total runs for each card
    card_stats = {}

    for data_dict in runs:
        # Check if the dictionary contains both "master_deck" and "victory" keys
        if "master_deck" in data_dict and "victory" in data_dict:
            master_deck = [card.split('+')[0] for card in data_dict['master_deck']]
            victory = data_dict["victory"]

            for card in master_deck:
                if card not in card_stats:
                    card_stats[card] = {"wins": 0, "total_runs": 0}

                # Update statistics based on victory
                card_stats[card]["total_runs"] += 1
                if victory:
                    card_stats[card]["wins"] += 1

    sorted_card_stats = sorted(card_stats.items(),
                               key=lambda x: (x[1]["wins"] / x[1]["total_runs"] if x[1]["total_runs"] > 0 else 0.0),
                               reverse=True)

    data = []

    for card, stats in sorted_card_stats:
        if card_to_pack.get(card) and stats["total_runs"] >= 50:
            total_runs = stats["total_runs"]
            win_rate = f"{(stats['wins'] / total_runs) * 100:.2f}" if total_runs > 0 else "N/A"
            data.append([card_to_rarity.get(card, "Unknown"),
                         del_prefix(card_to_pack.get(card)),
                         del_prefix(card),
                         stats['wins'],
                         total_runs,
                         win_rate])

    # Return the insights data structure
    insights = {
        "Win Rate by Card": {
            "description": "Win rate for each card",
            "headers": ["Rarity", "Pack", "Card", "Wins", "Total", "Win Rate"],
            "data": data
        }
    }

    return insights


# This is bogus data for fun
def hat_win_rate(runs: list[dict]) -> dict:
    # Create a dictionary to store the number of wins and total runs for each pickedHat
    picked_hat_stats = {}

    for data_dict in runs:
        # Check if the dictionary contains both "pickedHat" and "victory" keys
        if "pickedHat" in data_dict and "victory" in data_dict:
            picked_hat = data_dict["pickedHat"]
            victory = data_dict["victory"]

            # Initialize the pickedHat's statistics if not already present
            if picked_hat not in picked_hat_stats:
                picked_hat_stats[picked_hat] = {"wins": 0, "total_runs": 0}

            # Update statistics based on victory
            picked_hat_stats[picked_hat]["total_runs"] += 1
            if victory:
                picked_hat_stats[picked_hat]["wins"] += 1

    sorted_results = sorted(picked_hat_stats.items(),
                            key=lambda x: (x[1]["wins"] / x[1]["total_runs"] if x[1]["total_runs"] > 0 else 0.0),
                            reverse=True)

    data = []

    for picked_hat, stats in sorted_results:
        wins = stats["wins"]
        total_runs = stats["total_runs"]
        win_rate = make_ratio(wins, total_runs)
        data.append([del_prefix(picked_hat), wins, total_runs, win_rate])

    sorted_data = sorted(data, key=lambda x: x[3], reverse=True)

    insights = {
        "Hat Win Rate": {
            "description": "Win Rate based on what hat was picked (this is bogus data)",
            "headers": ["Picked Hat", "Wins", "Total", "Win Rate"],
            "data": sorted_data
        }
    }

    return insights


def median_turn_length_per_enemy(runs: list[dict]) -> dict:
    # Create a dictionary to store the turn lengths for each enemy
    enemy_turn_lengths = {}

    for data_dict in runs:
        # Check if the dictionary contains the "damage_taken" key
        if "damage_taken" in data_dict:
            damage_taken = data_dict["damage_taken"]

            for entry in damage_taken:
                enemy = entry.get("enemies", "")
                turns = entry.get("turns", 0)

                # Initialize the enemy's turn lengths list if not already present
                if enemy not in enemy_turn_lengths:
                    enemy_turn_lengths[enemy] = []

                # Append the turn length to the enemy's list
                enemy_turn_lengths[enemy].append(turns)

    sorted_results = sorted(
        enemy_turn_lengths.items(),
        key=lambda x: statistics.median(x[1]),
        reverse=True, )

    insights = {
        "Turn Length": {
            "description": "Median turn length for each enemy",
            "headers": ["Enemy", "Median Turn Length", "Number of Fights"],
            "data": []
        }
    }

    # Populate data for each enemy
    for enemy, turn_lengths in sorted_results:
        median_turn_length = statistics.median(turn_lengths)
        insights["Turn Length"]["data"].append(
            [enemy, median_turn_length, len(turn_lengths)])

    return insights


def _count_upgraded_cards(runs: list[dict]) -> dict:
    card_upgrade_counts = defaultdict(int)

    for run in runs:
        for choice in run.get("campfire_choices", []):
            if choice["key"] == "SMITH":
                card_name = del_prefix(choice["data"])
                card_upgrade_counts[card_name] += 1

    # Sort the cards by their upgrade frequency
    sorted_upgrade_counts = dict(sorted(card_upgrade_counts.items(), key=lambda item: item[1], reverse=True))

    return sorted_upgrade_counts


def upgraded_card_win_rate_analysis(runs: list[dict], card_to_pack: dict) -> dict:
    frequently_upgraded = _count_upgraded_cards(runs)

    # Count the number of runs where the card was upgraded and won
    upgrade_win_counts = defaultdict(int)
    upgrade_total_counts = defaultdict(int)

    # Count the number of runs where the card was present and won
    card_win_counts = defaultdict(int)
    card_total_counts = defaultdict(int)

    for run in runs:
        cards = [del_prefix(del_upg(card)) for card in run['master_deck']]
        upgraded_cards = [del_prefix(choice["data"]) for choice in run.get("campfire_choices", []) if
                          choice["key"] == "SMITH"]

        for card in cards:
            card_total_counts[card] += 1
            if run.get('victory', False):
                card_win_counts[card] += 1

        for upgraded_card in upgraded_cards:
            upgrade_total_counts[upgraded_card] += 1
            if run.get('victory', False):
                upgrade_win_counts[upgraded_card] += 1

    insights = {
        "Card Upgrades": {
            "description": "Card upgrade frequencies and effect on win rate",
            "headers": ["Card", "Amount Upgraded", "Win Rate when Upgraded", "Overall Card Win Rate","Change When Upgraded"],
            "data": []
        }
    }

    sorted_analysis = dict(sorted(frequently_upgraded.items(), key=lambda item: item[1], reverse=True))

    for card, freq in sorted_analysis.items():
        if freq < 350:
            continue

        # The general winrate for multi upgrades was showing as 0, this just makes it display the base card's winrate
        base_card = re.sub(r'\+\d+$', '', card)

        upgrade_win_rate = make_ratio(upgrade_win_counts[card], upgrade_total_counts[card])
        general_win_rate = make_ratio(card_win_counts[base_card], card_total_counts[base_card])

        win_rate_diff = float(upgrade_win_rate) - float(general_win_rate)
        formatted_diff = f"+{win_rate_diff:.2f}" if win_rate_diff > 0 else f"{win_rate_diff:.2f}"
    
        insights["Card Upgrades"]["data"].append([del_prefix(card), freq, upgrade_win_rate, general_win_rate,formatted_diff])

    return insights


def median_health_before_rest(runs: list[dict]) -> dict:
    # Dictionary to hold health values for each ascension level
    ascension_healths = defaultdict(list)
    overall_health_ratios = []  # Track health ratios across all ascensions

    for run in runs:
        ascension = run['ascension_level']
        for choice in run['campfire_choices']:
            if choice['key'] == 'REST':
                floor_index = int(choice['floor'])
                if len(run['current_hp_per_floor']) > floor_index and len(run['max_hp_per_floor']) > floor_index:
                    current_health = run['current_hp_per_floor'][floor_index]
                    max_health = run['max_hp_per_floor'][floor_index]
                    health_ratio = current_health / max_health if max_health > 0 else 0
                    ascension_healths[ascension].append(health_ratio)
                    overall_health_ratios.append(health_ratio)

    # Compute median health ratio for each ascension
    median_healths = {ascension: statistics.median(health_ratios) for ascension, health_ratios in
                      ascension_healths.items()}

    # Compute and print overall median
    overall_median = statistics.median(overall_health_ratios) * 100

    data = [["Overall", f"{overall_median:.2f}"]]
    
    valid_ascensions = [asc for asc in median_healths.keys() if 0 <= int(asc) <= 20]
    for ascension in sorted(valid_ascensions, key=lambda x: int(x), reverse=True):
        health_ratio = median_healths[ascension] * 100
        data.append([ascension, f"{health_ratio:.2f}"])

    # Create insights structure
    insights = {
        "Health Before Rest": {
            "description": "Median HP% before rest across different ascension levels",
            "headers": ["Ascension Level", "Median HP% Before Rest"],
            "data": data
        }
    }

    return insights


def smith_vs_rest_ratio(runs: list[dict]) -> dict:
    # Dictionary to hold count of 'SMITH' and 'REST' choices for each ascension level
    ascension_choices = defaultdict(lambda: {'SMITH': 0, 'REST': 0})
    overall_choices = {'SMITH': 0, 'REST': 0}  # Track overall 'SMITH' and 'REST' choices

    for run in runs:
        ascension = run['ascension_level']
        for choice in run['campfire_choices']:
            if choice['key'] in ['SMITH', 'REST']:
                ascension_choices[ascension][choice['key']] += 1
                overall_choices[choice['key']] += 1

    # Compute and print overall ratio
    overall_ratio = overall_choices['SMITH'] / overall_choices['REST'] if overall_choices['REST'] > 0 else 0

    data = [["Overall", overall_choices['SMITH'], overall_choices['REST'], f"{overall_ratio:.2f}"]]

    valid_ascensions = [asc for asc in ascension_choices.keys() if 0 <= int(asc) <= 20]
    for ascension in sorted(valid_ascensions, key=lambda x: int(x), reverse=True):
        choices = ascension_choices[ascension]
        if (choices['SMITH'] + choices['REST']) > 100:  # Only show ascs with a combined total of 100+ picked
            ratio = choices['SMITH'] / choices['REST'] if choices['REST'] > 0 else 0
            data.append([ascension, choices['SMITH'], choices['REST'], f"{ratio:.2f}"])

    # Format into the insights structure
    insights = {
        "Smith Vs Rest": {
            "description": "Smith-to-rest ratio at campsites",
            "headers": ["Ascension Level", "Number of Smiths", "Number of Rests", "Smith-to-Rest Ratio"],
            "data": data
        }
    }

    return insights


def gem_impact_on_win_rate(runs: list[dict]) -> dict:
    total_runs_with_gems = 0
    wins_with_gems = 0

    total_runs_without_gems = 0
    wins_without_gems = 0

    for run in runs:
        # Check if the run has the GemsPack
        if "anniv5:GemsPack" not in run.get('currentPacks', ''):
            continue

        gem_modifiers = run.get('basemod:card_modifiers', [])

        # Check if any card has a gem modifier
        has_gems = any(gem_modifiers)

        if has_gems:
            total_runs_with_gems += 1
            if run.get('victory', False):
                wins_with_gems += 1
        else:
            total_runs_without_gems += 1
            if run.get('victory', False):
                wins_without_gems += 1

    # Calculate win rates
    win_rate_with_gems = make_ratio(wins_with_gems, total_runs_with_gems)
    win_rate_without_gems = make_ratio(wins_without_gems, total_runs_without_gems)

    insights = {
        "Gem Impact on Win Rate": {
            "description": "Win rate of runs with gems pack: gems slotted vs. no gems slotted",
            "headers": ["Condition", "Wins", "Total", "Win Rate"],
            "data": [
                ["With Gems", wins_with_gems, total_runs_with_gems, win_rate_with_gems],
                ["Without Gems", wins_without_gems, total_runs_without_gems, win_rate_without_gems]
            ]
        }
    }

    return insights


def gem_count_vs_win_rate(runs: list[dict]) -> dict:
    gem_count_to_total_runs = defaultdict(int)
    gem_count_to_wins = defaultdict(int)

    for run in runs:
        # Check if the run has the GemsPack
        if "anniv5:GemsPack" not in run.get('currentPacks', ''):
            continue

        gem_modifiers = run.get('basemod:card_modifiers', [])

        gem_count = 0
        for mod_list in gem_modifiers:
            if mod_list:
                for mod in mod_list:
                    if mod and "thePackmaster.cardmodifiers.gemspack" in mod.get('classname', ''):
                        gem_count += 1

        gem_count_to_total_runs[gem_count] += 1

        if run.get('victory', False):
            gem_count_to_wins[gem_count] += 1

    # Calculate win rates
    results = []
    for gem_count, total_runs in gem_count_to_total_runs.items():
        wins = gem_count_to_wins.get(gem_count, 0)
        win_rate = make_ratio(wins, total_runs)
        results.append([gem_count, wins, total_runs, win_rate])

    # Sort results by gem count
    results.sort(key=lambda x: x[0])

    # Store the results in the desired structure
    insights = {
        "Gem Count vs Win Rate": {
            "description": "Win rate for runs with gems pack by number of gems slotted",
            "headers": ["Gem Count", "Wins", "Total", "Win Rate"],
            "data": results
        }
    }

    return insights


def win_rate_by_ascension_and_pack(runs: list[dict]) -> dict:
    stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'total': 0}))
    overall_stats = defaultdict(lambda: {'wins': 0, 'total': 0})

    for run in runs:
        asc_level = run.get('ascension_level', 0)
        packs = run.get('currentPacks', '').split(',')
        victory = run.get('victory', False)

        for pack in packs:
            stats[pack][asc_level]['total'] += 1
            overall_stats[pack]['total'] += 1
            if victory:
                stats[pack][asc_level]['wins'] += 1
                overall_stats[pack]['wins'] += 1

    win_rate_by_pack = defaultdict(dict)

    for pack, asc_data in stats.items():
        if pack:
            win_rate_by_pack[pack]['Overall'] = make_ratio(overall_stats[pack]['wins'], overall_stats[pack]['total'])
            for asc_level, data in asc_data.items():
                win_rate = make_ratio(data['wins'], data['total'])
                win_rate_by_pack[pack][asc_level] = win_rate

    all_asc_levels = [level for level in range(20, -1, -1)]

    insight = {
        "Win Rate by Pack and Asc": {
            "description": "Pack win rates across ascension levels",
            "headers": ["Pack","Overall Win Rate"] + [f"A{level}" for level in all_asc_levels],
            "data": []
        }
    }

    for pack, asc_data in win_rate_by_pack.items():
        row = [del_prefix(pack), asc_data.get('Overall', "N/A")]
        for asc_level in all_asc_levels:
            row.append(asc_data.get(asc_level, "N/A"))  # Use "N/A" if no data for this ascension level
        insight["Win Rate by Pack and Asc"]["data"].append(row)

    return insight


def win_rate_deviation_between_asc(runs: list[dict]) -> dict:
    pack_stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'total': 0}))
    asc_level_stats = defaultdict(lambda: {'wins': 0, 'total': 0})

    for run in runs:
        asc_level = run.get('ascension_level', 0)
        packs = run.get('currentPacks', '').split(',')
        victory = run.get('victory', False)

        asc_level_stats[asc_level]['total'] += 1
        if victory:
            asc_level_stats[asc_level]['wins'] += 1

        for pack in packs:
            pack_stats[pack][asc_level]['total'] += 1
            if victory:
                pack_stats[pack][asc_level]['wins'] += 1

    insights_data = []
    for pack, asc_data in pack_stats.items():
        if pack:
            asc_0_data = asc_data.get(0, {'wins': 0, 'total': 0})
            asc_20_data = asc_data.get(20, {'wins': 0, 'total': 0})
            asc_0_winrate = asc_0_data['wins'] / asc_0_data['total'] if asc_0_data['total'] > 0 else 0
            asc_20_winrate = asc_20_data['wins'] / asc_20_data['total'] if asc_20_data['total'] > 0 else 0

            deviation = asc_0_winrate - asc_20_winrate

            insights_data.append([
                del_prefix(pack),
                f"{asc_0_winrate * 100:.2f}",
                f"{asc_20_winrate * 100:.2f}",
                f"{deviation:.2%}"
            ])

    insights_data.sort(key=lambda x: float(x[3][:-1]), reverse=True)

    insights = {
        "Pack Win Rate Difference Between A0 and A20": {
            "description": "Difference in pack win rate between ascension 0 and ascension 20",
            "headers": ["Pack", "Asc 0 Win Rate", "Asc 20 Win Rate", "Difference"],
            "data": insights_data
        }
    }

    return insights


def win_rate_deviation_from_average_by_asc(runs: list[dict]) -> dict:
    pack_stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'total': 0}))
    asc_level_stats = defaultdict(lambda: {'wins': 0, 'total': 0})

    for run in runs:
        asc_level = run.get('ascension_level', 0)
        packs = run.get('currentPacks', '').split(',')
        victory = run.get('victory', False)

        asc_level_stats[asc_level]['total'] += 1
        if victory:
            asc_level_stats[asc_level]['wins'] += 1

        for pack in packs:
            pack_stats[pack][asc_level]['total'] += 1
            if victory:
                pack_stats[pack][asc_level]['wins'] += 1

    # Calculate overall average win rates by ascension level
    average_win_rates_by_asc = {}
    for asc_level, data in asc_level_stats.items():
        average_win_rates_by_asc[asc_level] = data['wins'] / data['total'] if data['total'] > 0 else 0

    insights_data = []
    for pack, asc_data in pack_stats.items():
        if pack:
            # Calculate win rates for specific ascension levels for the pack
            asc_0_data = asc_data.get(0, {'wins': 0, 'total': 0})
            asc_20_data = asc_data.get(20, {'wins': 0, 'total': 0})
            pack_asc_0_winrate = asc_0_data['wins'] / asc_0_data['total'] if asc_0_data['total'] > 0 else 0
            pack_asc_20_winrate = asc_20_data['wins'] / asc_20_data['total'] if asc_20_data['total'] > 0 else 0

            # Calculate deviations from the overall average win rates
            deviation_0 = pack_asc_0_winrate - average_win_rates_by_asc.get(0, 0)
            deviation_20 = pack_asc_20_winrate - average_win_rates_by_asc.get(20, 0)

            insights_data.append([
                del_prefix(pack),
                f"{pack_asc_0_winrate * 100:.2f}",
                f"{pack_asc_20_winrate * 100:.2f}",
                f"{deviation_0:.2%}",
                f"{deviation_20:.2%}"
            ])

    insights = {
        "Win Rate Difference from Average": {
            "description": "Win rates for each pack against the average win rate (across all packs) for ascension levels 0 and 20",
            "headers": ["Pack", "Pack Asc 0 Win Rate", "Pack Asc 20 Win Rate", "Difference from Avg Asc 0", "Difference from Avg Asc 20"],
            "data": insights_data
        }
    }

    return insights


# Pick rate deviation of pack average by card (excluding special cards)
def card_pick_deviation(runs: list[dict], card_to_pack: dict, card_to_rarity: dict) -> dict:
    picked_counts = Counter()
    not_picked_counts = Counter()
    card_pick_rates = {}  # To store pick rates of each card
    pack_pick_rates = defaultdict(list)  # To store pick rates of cards for calculating pack averages

    # Count picks and not picks
    for data_dict in runs:
        current_packs = set(data_dict.get("currentPacks", "").split(","))
        card_choices = data_dict.get("card_choices", [])
        for choice in card_choices:
            picked = del_upg(choice.get("picked"))  # Do not score upgraded card choices differently
            not_picked = [del_upg(card) for card in choice.get("not_picked", [])]

            # Exclude special rarity cards from both picked and not picked
            if picked and card_to_pack.get(picked) in current_packs and card_to_rarity.get(picked) != "Special":
                picked_counts.update([picked])

            not_picked = [card for card in not_picked if card_to_pack.get(card) in current_packs and card_to_rarity.get(card) != "Special"]
            not_picked_counts.update(not_picked)

    # Calculate pick rates for each card and aggregate them into packs
    for choice, picked_count in picked_counts.items():
        not_picked_count = not_picked_counts[choice]
        total_count = picked_count + not_picked_count
        pick_rate = picked_count / total_count if total_count > 0 else 0
        card_pick_rates[choice] = pick_rate
        pack_pick_rates[card_to_pack[choice]].append(pick_rate)

    # Calculate the average pick rate for each pack
    pack_average_pick_rates = {pack: statistics.mean(rates) for pack, rates in pack_pick_rates.items() if rates}

    # Calculate deviation of each card's pick rate from its pack's average
    card_deviations = {}
    for card, pick_rate in card_pick_rates.items():
        pack = card_to_pack[card]
        pack_average = pack_average_pick_rates[pack]
        deviation = pick_rate - pack_average
        card_deviations[card] = deviation

    insights = {
        "Card Pick Rate vs Pack Average": {
            "description": "Difference in card pick rate from the pack's average",
            "headers": ["Pack", "Card", "Pick Rate", "Pack Average", "Difference"],
            "data": [
                [del_prefix(card_to_pack[card]), del_prefix(card), f"{card_pick_rates[card] * 100:.2f}",
                 f"{pack_average_pick_rates[card_to_pack[card]] * 100:.2f}", f"{deviation:.2%}"]
                for card, deviation in sorted(card_deviations.items(), key=lambda x: x[1], reverse=True)
            ]
        }
    }
    return insights
