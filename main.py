from logic import insights
from logic.storage import *

# Global dictionary to store sublists based on file paths
date_to_metrics = {}
# Dictionairy of packs to cards
pack_to_cards = {}
cards_to_pack = {}

if __name__ == "__main__":
    data_path = os.path.join(os.getcwd(), "data")
    metrics_path = os.path.join(data_path, "metrics")
    data_file = "data.pkl"
    data_file_path = os.path.join(data_path, data_file)

    # Check if the data file exists to avoid reprocessing
    if os.path.exists(data_file_path):
        date_to_metrics = load_data_from_pickle(data_file_path)
    else:
        iterate_directory(metrics_path)
        save_data_to_pickle(data_file_path, date_to_metrics)

    pack_to_cards = load_data_from_json(os.path.join(data_path, "packCards.json"))
    cards_to_pack = reverse_and_flatten_dict(pack_to_cards)

    all_data_dict = round_date_keys(date_to_metrics, 0)
    insights.count_card_pick_rate(all_data_dict[""], cards_to_pack)
