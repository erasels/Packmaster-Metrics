import gc

from logic import insights
from logic.results import print_insight_dict, write_insight_to_file
from logic.storage import *

# Global dictionary to store sublists based on file paths
date_to_metrics = {}
pack_to_cards = {}
card_to_pack = {}

if __name__ == "__main__":
    data_path = os.path.join(os.getcwd(), "data")
    metrics_path = os.path.join(data_path, "metrics")
    data_file = "data.pkl"
    data_file_path = os.path.join(data_path, data_file)

    # Check if the data file exists to avoid reprocessing
    if os.path.exists(data_file_path):
        date_to_metrics = load_data_from_pickle(data_file_path)
    else:
        date_to_metrics = iterate_directory(metrics_path)
        print(date_to_metrics.keys())
        save_data_to_pickle(data_file_path, date_to_metrics)
    print("Data is loaded.")

    pack_to_cards = load_data_from_json(os.path.join(data_path, "packCards.json"))
    card_to_rarity = load_data_from_json(os.path.join(data_path, "rarities.json"))
    card_to_pack = reverse_and_flatten_dict(pack_to_cards)

    all_data = mega_list_merge(date_to_metrics)
    del date_to_metrics
    write_insight_to_file(insights.sum_filtered_packs(all_data))
    write_insight_to_file(insights.count_enabled_expansion_packs(all_data))
    write_insight_to_file(insights.count_pack_picks(all_data))
    write_insight_to_file(insights.count_most_common_players(all_data))
    write_insight_to_file(insights.count_most_common_picked_hats(all_data))
    write_insight_to_file(insights.count_pack_victory_rate(all_data))
    write_insight_to_file(insights.count_card_pick_rate(all_data, card_to_pack, card_to_rarity))
    write_insight_to_file(insights.count_win_rates_per_asc(all_data))
    write_insight_to_file(insights.count_median_deck_sizes(all_data))
    write_insight_to_file(insights.count_average_win_rate_per_card(all_data, card_to_pack, card_to_rarity))
    write_insight_to_file(insights.count_win_rate_per_picked_hat(all_data))
    write_insight_to_file(insights.count_median_turn_length_per_enemy(all_data))
    write_insight_to_file(insights.upgraded_card_win_rate_analysis(all_data))
    write_insight_to_file(insights.median_health_before_rest(all_data))
    write_insight_to_file(insights.smith_vs_rest_ratio(all_data))
    write_insight_to_file(insights.gem_impact_on_win_rate(all_data))
    write_insight_to_file(insights.gem_count_vs_win_rate(all_data))
    write_insight_to_file(insights.win_rate_by_ascension_and_pack(all_data))
    write_insight_to_file(insights.win_rate_deviation_between_asc(all_data))
    write_insight_to_file(insights.win_rate_deviation_from_average_by_asc(all_data))
    write_insight_to_file(insights.calculate_card_pick_deviation(all_data, card_to_pack, card_to_rarity))

    del all_data
    gc.collect()

