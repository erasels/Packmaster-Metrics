import statistics
from collections import Counter
from itertools import combinations
from collections import defaultdict
from typing import List, Dict, Tuple, Any

from logic.transformations import *


# Counts the number of packs filtered by each player and prints the most common ones.
def sum_filtered_packs(runs: list[dict]) -> Dict:
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
        "Blacklisted packs": {
            "description": "Shows how often packs are blacklisted by unique hosts.",
            "headers": ["Pack Name", "Filtered"],
            "data": data_rows
        }
    }

    return insights


# Counts the number of runs with enabledExpansionPacks and prints the ratio.
def count_enabled_expansion_packs(runs: list[dict]) -> Dict:
    enabled_count = 0
    total_count = len(runs)

    for data_dict in runs:
        if data_dict.get("enabledExpansionPacks"):
            enabled_count += 1

    ratio = make_ratio(enabled_count, total_count)

    # Construct the insights dictionary for this particular analysis
    insights = {
        "Expansionpack Usage": {
            "description": "Shows the number and percentage of runs with expansion packs enabled.",
            "headers": ["Enabled Expansion Packs", "Total Runs", "Percentage Enabled"],
            "data": [
                [enabled_count, total_count, ratio]
            ]
        }
    }

    return insights


# Counts the number of times each pack was picked and prints the results.
def count_pack_picks(runs: list[dict]) -> None:
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

        # Calculate pick rate
        if total_count > 0:
            pick_rate = picked_count / total_count
        else:
            pick_rate = 0.0

        result.append((choice, picked_count, not_picked_count, pick_rate))

    # Sort the results by pick rate in descending order
    sorted_result = sorted(result, key=lambda x: x[3], reverse=True)

    for choice, picked_count, not_picked_count, pick_rate in sorted_result:
        print(f"{del_prefix(choice)}: {pick_rate:.2%} ({picked_count}/{not_picked_count + picked_count})")


def count_most_common_players(runs: list[dict]) -> None:
    host_counts = Counter()

    for data_dict in runs:
        host = data_dict.get("host")
        if host:
            host_counts[host] += 1

    most_common_hosts = host_counts.most_common()

    for host, count in most_common_hosts:
        if count >= 20:
            print(f"{host}: {count}")


def count_most_common_picked_hats(runs: list[dict]) -> None:
    picked_hat_counts = Counter()

    for data_dict in runs:
        picked_hat = data_dict.get("pickedHat")
        if picked_hat:
            picked_hat_counts[picked_hat] += 1

    for picked_hat, count in picked_hat_counts.most_common():
        print(f"{del_prefix(picked_hat)}: {count}")


def count_pack_victory_rate(runs: list[dict]) -> None:
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

    for pack in sorted_packs:
        wins = pack_wins[pack]
        total_runs = pack_runs.get(pack, 0)
        print(f"{del_prefix(pack)}: {make_ratio(wins, total_runs)}")


# Count card picks of current run cards (counts upgraded cards seperately)
def count_card_pick_rate(runs: list[dict], card_to_pack: dict) -> None:
    picked_counts = Counter()
    not_picked_counts = Counter()
    result = []

    for data_dict in runs:
        current_packs = set(data_dict.get("currentPacks", "").split(","))
        card_choices = data_dict.get("card_choices", [])
        for choice in card_choices:
            picked = choice.get("picked")
            not_picked = choice.get("not_picked", [])

            if picked and card_to_pack.get(picked) in current_packs:
                picked_counts.update([picked])

            not_picked = [card for card in not_picked if card_to_pack.get(card) in current_packs]
            not_picked_counts.update(not_picked)

    for choice, picked_count in picked_counts.items():
        not_picked_count = not_picked_counts[choice]
        total_count = picked_count + not_picked_count

        # Calculate pick rate
        if total_count > 0:
            pick_rate = picked_count / total_count
        else:
            pick_rate = 0.0

        result.append((choice, picked_count, not_picked_count, pick_rate))

    # Sort the results by pick rate in descending order
    sorted_result = sorted(result, key=lambda x: x[3], reverse=True)

    for choice, picked_count, not_picked_count, pick_rate in sorted_result:
        print(f"{add_pack_prefix(choice, card_to_pack)}: {pick_rate:.2%} ({picked_count}/{not_picked_count + picked_count})")


def count_win_rates(runs: list[dict]) -> None:
    # Create a dictionary to store wins and total runs per ascension level
    ascension_stats = {}
    all_stats = {"wins": 0, "total_runs": 0}

    for data_dict in runs:
        # Check if the dictionary contains a "victory" key
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
    sorted_ascension_levels = sorted(ascension_stats.keys(), key=lambda x: int(x))

    print(
        f"Total win rate: {make_ratio(all_stats['wins'], all_stats['total_runs'])}")
    # Calculate and print win rates per ascension level (sorted)
    for ascension_level in sorted_ascension_levels:
        stats = ascension_stats[ascension_level]
        wins = stats["wins"]
        total_runs = stats["total_runs"]
        print(f"Win rate on ascension {ascension_level}: {make_ratio(wins, total_runs)}")


def count_median_deck_sizes(runs: list[dict]) -> None:
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

    print(f"Median deck size for any ascension: {statistics.median(total_deck_sizes)}")
    # Calculate and print median deck size per ascension level (sorted)
    for ascension_level in sorted_ascension_levels:
        median_size = statistics.median(ascension_deck_sizes[ascension_level])
        print(f"Median deck size for ascension {ascension_level}: {median_size}")


def count_average_win_rate_per_card(runs: list[dict], card_to_pack: dict) -> None:
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

    cards_with_200_runs_or_more = []
    cards_with_less_than_200_runs = []

    for card, stats in sorted_card_stats:
        total_runs = stats["total_runs"]
        if total_runs >= 200:
            cards_with_200_runs_or_more.append((card, stats))
        else:
            cards_with_less_than_200_runs.append((card, stats))

    # Sort the cards with at least 200 total runs by win rate
    sorted_cards_with_200_runs_or_more = sorted(
        cards_with_200_runs_or_more,
        key=lambda x: (x[1]["wins"] / x[1]["total_runs"] if x[1]["total_runs"] > 0 else 0.0),
        reverse=True,
    )

    # Combine and print the results
    sorted_results = sorted_cards_with_200_runs_or_more + cards_with_less_than_200_runs

    # Calculate and print the average win rate for each card
    for card, stats in sorted_results:
        if card_to_pack.get(card):
            wins = stats["wins"]
            total_runs = stats["total_runs"]
            print(f"{add_pack_prefix(card, card_to_pack)}: {make_ratio(wins, total_runs)}")


def count_average_win_rate_per_card_split_by_rarity(runs: list[dict], card_to_pack: dict, card_to_rarity: dict) -> None:
    # Create a dictionary to store the number of wins and total runs for each card
    card_stats = {}

    for data_dict in runs:
        if "master_deck" in data_dict and "victory" in data_dict:
            master_deck = [card.split('+')[0] for card in data_dict['master_deck']]
            victory = data_dict["victory"]

            for card in master_deck:
                if card not in card_stats:
                    card_stats[card] = {"wins": 0, "total_runs": 0}

                card_stats[card]["total_runs"] += 1
                if victory:
                    card_stats[card]["wins"] += 1

    # Group cards by rarity
    rarity_groups = {}
    for card, stats in card_stats.items():
        rarity = card_to_rarity.get(card, "Unknown")
        if rarity not in rarity_groups:
            rarity_groups[rarity] = []
        rarity_groups[rarity].append((card, stats))

    # Process and print results for each rarity group
    for rarity, cards in rarity_groups.items():
        print(f"\n------ {rarity.upper()} ------\n")
        sorted_cards = sorted(
            cards,
            key=lambda x: (x[1]["wins"] / x[1]["total_runs"] if x[1]["total_runs"] > 0 else 0.0),
            reverse=True
        )

        for card, stats in sorted_cards:
            if card_to_pack.get(card):
                wins = stats["wins"]
                total_runs = stats["total_runs"]
                print(f"{add_pack_prefix(card, card_to_pack)}: {make_ratio(wins, total_runs)}")


# This is bogus data for fun
def count_win_rate_per_picked_hat(runs: list[dict]) -> None:
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

    # Calculate and print the win rate for each pickedHat
    for picked_hat, stats in sorted_results:
        wins = stats["wins"]
        total_runs = stats["total_runs"]
        print(f"{del_prefix(picked_hat)}: {make_ratio(wins, total_runs)}")


def count_median_turn_length_per_enemy(runs: list[dict], high_value_threshold: int = 200) -> None:
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

    low_value_results = []
    high_value_results = []

    for stat in sorted_results:
        if len(enemy_turn_lengths[stat[0]]) < high_value_threshold:
            low_value_results.append(stat)
        else:
            high_value_results.append(stat)

    # Calculate and print the median turn length per enemy
    for enemy, turn_lengths in high_value_results:
        median_turn_length = statistics.median(turn_lengths)
        print(f"{enemy}: {median_turn_length} turns (from {len(turn_lengths)} fights)")
    print(f"---- The following results have less than {high_value_threshold} recorded combats ----")
    for enemy, turn_lengths in low_value_results:
        median_turn_length = statistics.median(turn_lengths)
        print(f"{enemy}: {median_turn_length} turns (from {len(turn_lengths)} fights)")


# Turned out kind of useless, since popular packs have a heavy influence on this output. Prints the frequency of the pair and the total win rate with that pair in the deck.
# Analyzes card synergy based on the frequency and win rate of card combinations.
def card_synergy_analysis(runs: list[dict]) -> None:
    # Counting the frequency of each card pair in winning runs
    pair_counts = defaultdict(int)
    total_winning_runs = 0

    cards_to_clean = ["Rummage", "Cardistry", "Strike", "Defend", "AscendersBane"]

    for run in runs:
        if run.get('victory', False):
            total_winning_runs += 1
            # Remove upgrade and prefix from cards
            cards = [del_prefix(del_upg(card)) for card in run['master_deck']]
            # Removing unwanted cards from the dataset
            cards = [card for card in cards if card not in cards_to_clean]
            # Ensuring each card is unique for the current run
            cards = list(set(cards))

            for combo in combinations(cards, 2):
                # Sorting to ensure (CardA, CardB) is the same as (CardB, CardA)
                sorted_combo = tuple(sorted(combo))
                pair_counts[sorted_combo] += 1

    # Analyzing card pairs
    synergy_data = {}
    for pair, count in pair_counts.items():
        win_rate = (count / total_winning_runs) * 100
        synergy_data[pair] = {
            'frequency': count,
            'win_rate': win_rate
        }

    # Sorting card pairs by win rate for better insight
    sorted_synergy_data = dict(sorted(synergy_data.items(), key=lambda item: item[1]['win_rate'], reverse=True))

    for index, (cards, count_data) in enumerate(sorted_synergy_data.items()):
        if count_data['frequency'] >= 800:
            print(
                f"{index + 1}. {cards[0]} and {cards[1]}: Frequency - {count_data['frequency']}, Win Rate - {count_data['win_rate']:.2f}%")


# Analyzes the efficiency of packs based on the win rates of runs containing cards from those packs.
def pack_efficiency_analysis(runs: list[dict], card_to_pack: dict) -> None:
    pack_counts = defaultdict(int)
    pack_win_counts = defaultdict(int)

    for run in runs:
        # Dictionary to keep track of cards from each pack in the current run
        run_pack_counts = defaultdict(int)

        for card in run['master_deck']:
            # Get the card's pack
            clean_card = del_upg(card)
            pack_name = card_to_pack.get(clean_card)

            if not pack_name:  # Skip cards that can't be associated with a pack
                continue

            # Increment the count for this pack for the current run
            run_pack_counts[pack_name] += 1

        # Update the global pack counts with the counts from this run
        for pack, count in run_pack_counts.items():
            pack_counts[pack] += count
            if run.get('victory', False):
                pack_win_counts[pack] += count

    # Calculate the win rates
    pack_win_rates = {}
    for pack, count in pack_counts.items():
        win_count = pack_win_counts.get(pack, 0)
        pack_win_rates[pack] = (win_count / count if count > 0 else 0.0, make_ratio(win_count, count))

    # Sort packs by win rate
    sorted_packs = sorted(pack_win_rates.items(), key=lambda x: x[1][0], reverse=True)

    # Display results
    for pack, (win_rate_percentage, win_rate_str) in sorted_packs:
        print(f"{del_prefix(pack)}: {win_rate_str}")


def count_upgraded_cards(runs: list[dict]) -> dict:
    card_upgrade_counts = defaultdict(int)

    for run in runs:
        for choice in run.get("campfire_choices", []):
            if choice["key"] == "SMITH":
                card_name = del_prefix(choice["data"])
                card_upgrade_counts[card_name] += 1

    # Sort the cards by their upgrade frequency
    sorted_upgrade_counts = dict(sorted(card_upgrade_counts.items(), key=lambda item: item[1], reverse=True))

    return sorted_upgrade_counts


def upgraded_card_win_rate_analysis(runs: list[dict]) -> dict:
    frequently_upgraded = count_upgraded_cards(runs)

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

    analysis = {}
    for card, freq in frequently_upgraded.items():
        upgrade_win_rate = make_ratio(upgrade_win_counts[card], upgrade_total_counts[card])
        general_win_rate = make_ratio(card_win_counts[card], card_total_counts[card])
        analysis[card] = {
            "upgrade_frequency": freq,
            "upgrade_win_rate": upgrade_win_rate,
            "general_win_rate": general_win_rate
        }

    # Sorting by upgrade frequency for better insight
    sorted_analysis = dict(sorted(analysis.items(), key=lambda item: item[1]['upgrade_frequency'], reverse=True))

    for card, stats in sorted_analysis.items():
        if stats['upgrade_frequency'] < 350:
            continue
        print(f"{card}: Upgraded {stats['upgrade_frequency']} times")
        print(f"\tWin Rate when upgraded: {stats['upgrade_win_rate']}")
        print(f"\tGeneral Win Rate: {stats['general_win_rate']}\n")

    return sorted_analysis


def median_health_before_rest(runs: List[Dict[str, any]]) -> Dict[int, float]:
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
    overall_median = statistics.median(overall_health_ratios)
    print(f"Overall Median Health Ratio Before Rest: {overall_median:.2%}")

    # Print results for each ascension, sorted
    for ascension in sorted(median_healths.keys()):
        health_ratio = median_healths[ascension]
        print(f"Ascension {ascension}: Median Health Ratio Before Rest: {health_ratio:.2%}")

    return median_healths


def smith_vs_rest_ratio(runs: List[Dict[str, any]]) -> Dict[int, Tuple[int, int]]:
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
    print(
        f"Overall Smith to Rest Ratio: {overall_ratio:.2f} ({overall_choices['SMITH']} Smiths / {overall_choices['REST']} Rests)")

    # Compute and print ratio for each ascension, sorted
    for ascension in sorted(ascension_choices.keys()):
        choices = ascension_choices[ascension]
        ratio = choices['SMITH'] / choices['REST'] if choices['REST'] > 0 else 0
        print(
            f"Ascension {ascension}: Smith to Rest Ratio: {ratio:.2f} ({choices['SMITH']} Smiths / {choices['REST']} Rests)")

    return ascension_choices


def gem_impact_on_win_rate(runs: List[Dict[str, Any]]) -> Dict[str, str]:
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

    results = {
        "Win Rate with Gems": win_rate_with_gems,
        "Win Rate without Gems": win_rate_without_gems
    }

    # Printing the results
    print("Gem Impact on Win Rate:")
    for key, value in results.items():
        print(f"{key}: {value}")
    print("\n")

    return results


def gem_count_vs_win_rate(runs: List[Dict[str, Any]]) -> Dict[int, str]:
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
    results = {}
    for gem_count, total_runs in gem_count_to_total_runs.items():
        wins = gem_count_to_wins.get(gem_count, 0)
        results[gem_count] = make_ratio(wins, total_runs)

    # Sorting results by gem count
    sorted_results = dict(sorted(results.items()))

    # Printing the results
    print("Win Rate by Number of Socketed Gems:")
    for gem_count, win_rate in sorted_results.items():
        print(f"{gem_count} gems: {win_rate}")
    print("\n")

    return sorted_results


def card_gem_synergies(runs: List[Dict[str, Any]]) -> Dict[str, int]:
    card_gem_combinations = defaultdict(int)

    for run in runs:
        # Ensure the run has the GemsPack
        if "anniv5:GemsPack" not in run.get('currentPacks', ''):
            continue

        master_deck = run.get('master_deck', [])
        gem_modifiers = run.get('basemod:card_modifiers', [])

        for card, mod_list in zip(master_deck, gem_modifiers):
            if mod_list:
                for mod in mod_list:
                    if mod and "thePackmaster.cardmodifiers.gemspack" in mod.get('classname', ''):
                        # Create a combination key
                        combo = f"{del_prefix(del_upg(card))}_{(mod['classname'].split('.')[-1]).replace('Mod', '')}"
                        card_gem_combinations[combo] += 1

    # Filter out combinations that occur less than 50 times
    frequent_combinations = {k: v for k, v in card_gem_combinations.items() if v >= 50}

    # Sorting results by frequency
    sorted_results = dict(sorted(frequent_combinations.items(), key=lambda item: item[1], reverse=True))

    # Printing the results
    print("Frequent Card-Gem Combinations:")
    for combo, count in sorted_results.items():
        print(f"{combo}: {count} times")
    print("\n")

    return sorted_results


def win_rate_by_ascension_and_pack(runs: List[Dict[str, Any]]) -> Dict[str, Dict[int, str]]:
    stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'total': 0}))

    for run in runs:
        asc_level = run.get('ascension_level', 0)
        packs = run.get('currentPacks', '').split(',')
        victory = run.get('victory', False)

        for pack in packs:
            stats[pack][asc_level]['total'] += 1
            if victory:
                stats[pack][asc_level]['wins'] += 1

    win_rate_by_pack = defaultdict(dict)

    for pack, asc_data in stats.items():
        for asc_level, data in asc_data.items():
            win_rate = make_ratio(data['wins'], data['total'])
            win_rate_by_pack[pack][asc_level] = win_rate

    # Print the results
    for pack, asc_data in win_rate_by_pack.items():
        print(f"Pack: {del_prefix(pack)}")
        for asc_level in range(0, 21):
            if asc_level in asc_data:
                print(f"Ascension {asc_level}: {asc_data[asc_level]}")
        print("\n")

    return win_rate_by_pack


def win_rate_deviation_by_ascension_and_pack(runs: List[Dict[str, Any]]) -> Dict[str, Dict[int, str]]:
    stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'total': 0}))

    for run in runs:
        asc_level = run.get('ascension_level', 0)
        packs = run.get('currentPacks', '').split(',')
        victory = run.get('victory', False)

        for pack in packs:
            stats[pack][asc_level]['total'] += 1
            if victory:
                stats[pack][asc_level]['wins'] += 1

    average_win_rates = {}
    for pack, asc_data in stats.items():
        total_wins = sum(data['wins'] for data in asc_data.values())
        total_runs = sum(data['total'] for data in asc_data.values())
        average_win_rates[pack] = total_wins / total_runs if total_runs > 0 else 0

    win_rate_deviation_by_pack = defaultdict(dict)

    for pack, asc_data in stats.items():
        for asc_level, data in asc_data.items():
            win_rate = data['wins'] / data['total'] if data['total'] > 0 else 0
            deviation = win_rate - average_win_rates[pack]
            sign = '+' if deviation > 0 else ''
            win_rate_deviation_by_pack[pack][asc_level] = f"{sign}{deviation:.2%}"

    # Print the results
    for pack in sorted(win_rate_deviation_by_pack.keys(), key=lambda p: del_prefix(p)):
        print(f"Pack: {del_prefix(pack)}")
        for asc_level in range(0, 21):
            if asc_level in win_rate_deviation_by_pack[pack]:
                print(f"Ascension {asc_level}: Deviation from average: {win_rate_deviation_by_pack[pack][asc_level]}")
        print("\n")

    return win_rate_deviation_by_pack


def win_rate_deviation_by_ascension_and_pack_compact(runs: List[Dict[str, Any]]) -> Dict[str, Dict[int, str]]:
    stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'total': 0}))

    for run in runs:
        asc_level = run.get('ascension_level', 0)
        packs = run.get('currentPacks', '').split(',')
        victory = run.get('victory', False)

        for pack in packs:
            stats[pack][asc_level]['total'] += 1
            if victory:
                stats[pack][asc_level]['wins'] += 1

    average_win_rates = {}
    for pack, asc_data in stats.items():
        total_wins = sum(data['wins'] for data in asc_data.values())
        total_runs = sum(data['total'] for data in asc_data.values())
        average_win_rates[pack] = total_wins / total_runs if total_runs > 0 else 0

    win_rate_deviation_by_pack = defaultdict(dict)

    for pack, asc_data in stats.items():
        for asc_level, data in asc_data.items():
            win_rate = data['wins'] / data['total'] if data['total'] > 0 else 0
            deviation = win_rate - average_win_rates[pack]
            sign = '+' if deviation > 0 else ''
            win_rate_deviation_by_pack[pack][asc_level] = f"{sign}{deviation:.2%}"

    # Print the results in a compact format
    for pack in sorted(win_rate_deviation_by_pack.keys(), key=lambda p: del_prefix(p)):
        a0_deviation = win_rate_deviation_by_pack[pack].get(0, "N/A")
        a20_deviation = win_rate_deviation_by_pack[pack].get(20, "N/A")

        # Calculate the difference between A0 and A20
        if a0_deviation != "N/A" and a20_deviation != "N/A":
            diff_deviation = float(a0_deviation.rstrip('%')) - float(a20_deviation.rstrip('%'))
            sign = '+' if diff_deviation > 0 else ''
            diff_deviation_str = f"{sign}{diff_deviation:.2f}%"
        else:
            diff_deviation_str = "N/A"

        print(
            f"{del_prefix(pack)}, Difference: 0/20: {diff_deviation_str}, A0: {a0_deviation}, A20: {a20_deviation}")

    return win_rate_deviation_by_pack


def win_rate_deviation_by_ascension_and_pack_vs_average(runs: List[Dict[str, Any]]) -> Dict[str, Dict[int, str]]:
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

    average_win_rates_by_asc = {}
    for asc_level, data in asc_level_stats.items():
        average_win_rates_by_asc[asc_level] = data['wins'] / data['total'] if data['total'] > 0 else 0

    win_rate_deviation_by_pack = defaultdict(dict)

    for pack, asc_data in pack_stats.items():
        for asc_level, data in asc_data.items():
            win_rate = data['wins'] / data['total'] if data['total'] > 0 else 0
            deviation = win_rate - average_win_rates_by_asc[asc_level]
            sign = '+' if deviation > 0 else ''
            win_rate_deviation_by_pack[pack][asc_level] = f"{sign}{deviation:.2%}"

    # Print the results in a verbose format
    for pack in sorted(win_rate_deviation_by_pack.keys(), key=lambda p: del_prefix(p)):
        print(f"\nPack: {del_prefix(pack)}")
        for asc_level in range(0, 21):
            deviation = win_rate_deviation_by_pack[pack].get(asc_level, "N/A")
            print(f"Ascension{asc_level}: Deviation from average: {deviation}")

    return win_rate_deviation_by_pack


def win_rate_deviation_by_ascension_and_pack_vs_average_compact(runs: List[Dict[str, Any]]) -> Dict[str, Dict[int, str]]:
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

    average_win_rates_by_asc = {}
    for asc_level, data in asc_level_stats.items():
        average_win_rates_by_asc[asc_level] = data['wins'] / data['total'] if data['total'] > 0 else 0

    win_rate_deviation_by_pack = defaultdict(dict)

    for pack, asc_data in pack_stats.items():
        for asc_level, data in asc_data.items():
            win_rate = data['wins'] / data['total'] if data['total'] > 0 else 0
            deviation = win_rate - average_win_rates_by_asc[asc_level]
            sign = '+' if deviation > 0 else ''
            win_rate_deviation_by_pack[pack][asc_level] = f"{sign}{deviation:.2%}"

    # Print the results in a compact format
    for pack in sorted(win_rate_deviation_by_pack.keys(), key=lambda p: del_prefix(p)):
        a0_deviation = win_rate_deviation_by_pack[pack].get(0, "N/A")
        a20_deviation = win_rate_deviation_by_pack[pack].get(20, "N/A")

        # Calculate the difference between A0 and A20
        if a0_deviation != "N/A" and a20_deviation != "N/A":
            diff_deviation = float(a0_deviation.rstrip('%')) - float(a20_deviation.rstrip('%'))
            sign = '+' if diff_deviation > 0 else ''
            diff_deviation_str = f"{sign}{diff_deviation:.2f}%"
        else:
            diff_deviation_str = "N/A"

        print(
            f"{del_prefix(pack)}, Difference: 0/20: {diff_deviation_str}, A0: {a0_deviation}, A20: {a20_deviation}")

    return win_rate_deviation_by_pack


def win_rate_deviation_by_ascension_and_pack_sorted(runs: List[Dict[str, Any]]) -> Dict[str, Dict[int, str]]:
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

    average_win_rates_by_asc = {}
    for asc_level, data in asc_level_stats.items():
        average_win_rates_by_asc[asc_level] = data['wins'] / data['total'] if data['total'] > 0 else 0

    win_rate_deviation_by_pack = defaultdict(dict)

    for pack, asc_data in pack_stats.items():
        for asc_level, data in asc_data.items():
            win_rate = data['wins'] / data['total'] if data['total'] > 0 else 0
            deviation = win_rate - average_win_rates_by_asc[asc_level]
            sign = '+' if deviation > 0 else ''
            win_rate_deviation_by_pack[pack][asc_level] = f"{sign}{deviation:.2%}"

    # Sorting packs by the difference in win rate deviation between A0 and A20
    sorted_packs = sorted(win_rate_deviation_by_pack.keys(),
                          key=lambda p: abs(float(win_rate_deviation_by_pack[p].get(0, "0%").rstrip('%')) -
                                            float(win_rate_deviation_by_pack[p].get(20, "0%").rstrip('%'))),
                          reverse=True)

    # Print the results
    for pack in sorted_packs:
        a0_deviation = win_rate_deviation_by_pack[pack].get(0, "N/A")
        a20_deviation = win_rate_deviation_by_pack[pack].get(20, "N/A")

        # Calculate the difference between A0 and A20
        if a0_deviation != "N/A" and a20_deviation != "N/A":
            diff_deviation = float(a0_deviation.rstrip('%')) - float(a20_deviation.rstrip('%'))
            sign = '+' if diff_deviation > 0 else ''
            diff_deviation_str = f"{sign}{diff_deviation:.2f}%"
        else:
            diff_deviation_str = "N/A"

        print(f"{del_prefix(pack)}, Difference: 0/20: {diff_deviation_str}, A0: {a0_deviation}, A20: {a20_deviation}")

    return win_rate_deviation_by_pack


# Pick rate deviation of pack average by card (excluding special cards)
def calculate_card_pick_deviation_per_pack(runs: List[Dict], card_to_pack: Dict[str, str], card_to_rarity: dict) -> None:
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

    # Sort and print results
    sorted_card_deviations = sorted(card_deviations.items(), key=lambda x: x[1], reverse=True)
    for card, deviation in sorted_card_deviations:
        pack = card_to_pack[card]
        card_pick_rate = card_pick_rates[card]
        pack_average = pack_average_pick_rates[pack]
        print(f"{del_prefix(pack)}:{del_prefix(card)}: Pick rate: {card_pick_rate:.2%}, Pack avg: {pack_average:.2%}, Deviation: {deviation:.2%}")
