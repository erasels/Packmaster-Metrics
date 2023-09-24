from collections import Counter


# Counts packs filtered at some point by each player.
def sum_filtered_packs(data_list):
    word_counts = Counter()
    host_word_counts = {}

    for data_dict in data_list:
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
        print(f"{word}: {count}")


# Counts how many runs were with enabledExpansionPacks out of the total runs
def count_enabled_expansion_packs(data_list):
    enabled_count = 0
    total_count = len(data_list)

    for data_dict in data_list:
        if data_dict.get("enabledExpansionPacks"):
            enabled_count += 1

    print(f"{enabled_count}/{total_count}")


def count_enabled_expansion_packs_per_host(data_list):
    host_count = {}

    for data_dict in data_list:
        host = data_dict.get("host")
        enabled = data_dict.get("enabledExpansionPacks")

        if host is None or enabled is None:
            continue

        if host not in host_count:
            host_count[host] = enabled
        elif enabled:
            host_count[host] = True

    print(f"{sum(host_count.values())}/{len(host_count)}")


# Count pack picks
def count_picked_and_not_picked(data_list):
    picked_counts = Counter()
    not_picked_counts = Counter()
    result = []

    for data_dict in data_list:
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
        print(f"{choice}: {pick_rate:.2%} ({picked_count}/{not_picked_count + picked_count})")


def count_most_common_players(data_list):
    host_counts = Counter()

    for data_dict in data_list:
        host = data_dict.get("host")
        if host:
            host_counts[host] += 1

    most_common_hosts = host_counts.most_common()

    for host, count in most_common_hosts:
        if count >= 20:
            print(f"{host}: {count}")


def count_most_common_picked_hats(data_list):
    picked_hat_counts = Counter()

    for data_dict in data_list:
        picked_hat = data_dict.get("pickedHat")
        if picked_hat:
            picked_hat_counts[picked_hat] += 1

    for picked_hat, count in picked_hat_counts.most_common():
        print(f"{picked_hat}: {count}")


def count_pack_victory_rate(data_list):
    pack_wins = {}
    pack_runs = {}

    for data_dict in data_list:
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
        victory_rate = wins / total_runs if total_runs > 0 else 0.0
        print(f"{pack}: {victory_rate:.2%} ({wins}/{total_runs})")


# Count card picks of current run cards
def count_card_pick_rate(data_list, cards_to_pack):
    picked_counts = Counter()
    not_picked_counts = Counter()
    result = []

    for data_dict in data_list:
        current_packs = set(data_dict.get("currentPacks", "").split(","))
        card_choices = data_dict.get("card_choices", [])
        for choice in card_choices:
            picked = choice.get("picked")
            not_picked = choice.get("not_picked", [])

            if picked and cards_to_pack.get(picked) in current_packs:
                picked_counts.update([picked])

            not_picked = [card for card in not_picked if cards_to_pack.get(card) in current_packs]
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
        print(f"{cards_to_pack[choice]}:{choice}: {pick_rate:.2%} ({picked_count}/{not_picked_count + picked_count})")


def count_win_rates(data_list):
    # Create a dictionary to store wins and total runs per ascension level
    ascension_stats = {}
    all_stats = {"wins": 0, "total_runs": 0}

    for data_dict in data_list:
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

    print(f"Total win rate: {(all_stats['wins']/all_stats['total_runs']):.2%} ({all_stats['wins']}/{all_stats['total_runs']})")
    # Calculate and print win rates per ascension level (sorted)
    for ascension_level in sorted_ascension_levels:
        stats = ascension_stats[ascension_level]
        wins = stats["wins"]
        total_runs = stats["total_runs"]
        win_rate = wins / total_runs if total_runs > 0 else 0.0
        print(f"Win rate on ascension {ascension_level}: {win_rate:.2%} ({wins}/{total_runs})")
