import statistics
from collections import Counter
from itertools import combinations
from collections import defaultdict
from logic.transformations import *


# Counts the number of packs filtered by each player and prints the most common ones.
def sum_filtered_packs(runs: list[dict]) -> None:
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

    for word, count in word_counts.most_common():
        print(f"{del_prefix(word)}: {count}")


# Counts the number of runs with enabledExpansionPacks and prints the ratio.
def count_enabled_expansion_packs(runs: list[dict]) -> None:
    enabled_count = 0
    total_count = len(runs)

    for data_dict in runs:
        if data_dict.get("enabledExpansionPacks"):
            enabled_count += 1

    print(make_ratio(enabled_count, total_count))


# Counts the number of runs with enabledExpansionPacks for each host and prints the ratio.
def count_enabled_expansion_packs_per_host(runs: list[dict]) -> None:
    host_count = {}

    for data_dict in runs:
        host = data_dict.get("host")
        enabled = data_dict.get("enabledExpansionPacks")

        if host is None or enabled is None:
            continue

        if host not in host_count:
            host_count[host] = enabled
        elif enabled:
            host_count[host] = True

    print(f"{sum(host_count.values())}/{len(host_count)}")


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
            print(f"{index + 1}. {cards[0]} and {cards[1]}: Frequency - {count_data['frequency']}, Win Rate - {count_data['win_rate']:.2f}%")


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

