import json
import os

from logic.storage import load_data_from_json

data_path = os.path.join(os.getcwd(), "data")
card_to_rarity = load_data_from_json(os.path.join(data_path, "rarities.json"))

# The required prefixes
required_prefixes = {"anniv5", "clockworkchar", "oceanrodent", "bogwarden"}
rarities = {}

# Used to map list of lists to a dict
for card_rarity_pair in card_to_rarity:
    card_name, rarity = card_rarity_pair
    # Check if the card name starts with one of the required prefixes
    if any(card_name.startswith(prefix + ":") for prefix in required_prefixes) or ":" not in card_name:
        rarities[card_name] = rarity


output_file_path = os.path.join(data_path, "rarities.json")
with open(output_file_path, 'w') as file:
    json.dump(rarities, file, indent=4)
