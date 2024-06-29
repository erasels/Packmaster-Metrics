from logic import insights
from logic.results import print_insight_dict
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
    print_insight_dict(insights.sum_filtered_packs(all_data))
