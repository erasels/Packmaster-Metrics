import os
import json
import pickle

from logic import insights

# Global dictionary to store sublists based on file paths
date_to_metrics = {}
# Dictionairy of packs to cards
pack_to_cards = {}
cards_to_pack = {}


def process_file(file_path, encoding='utf-8'):
    # Create a sub list based on the path of the file from the working directory
    relative_path = os.path.relpath(file_path, start=os.getcwd()).replace('\\', '/')
    sub_list = []

    # Open and read the file line by line
    with open(file_path, 'r', encoding=encoding, errors='replace') as file:
        for index, line in enumerate(file):
            try:
                # Parse each line as JSON and convert it into a dictionary
                data = json.loads(line)
                event = data['event']
                event['host'] = data.get('host', '')
                event['time'] = data.get('time', '')
                sub_list.append(event)
            except json.JSONDecodeError:
                print(f"{index} line in {file_path} is not valid JSON. Skipped it.")
                pass

    # Store the sub_list in the sublists_dict using the relative path as the key
    date_to_metrics[relative_path] = sub_list


def iterate_directory(directory, encoding='utf-8'):
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            process_file(file_path, encoding)


def save_data_to_json(filename):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(date_to_metrics, file, indent=4)


def load_data_from_json(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data


def save_data_to_pickle(filename):
    with open(filename, 'wb') as file:
        pickle.dump(date_to_metrics, file, protocol=pickle.HIGHEST_PROTOCOL)


def load_data_from_pickle(filename):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
        return data


# Takes in a dict with keys consisting of YYYY/MM/DD and merges lists based on the input level (2 = YYYY/MM)
def round_date_keys(input_dict, level):
    if level < 0:
        raise ValueError("Level must be a non-negative integer.")

    merged_dict = {}

    for date_key, data_list in input_dict.items():
        date_parts = date_key.split('/')
        rounded_key = '/'.join(date_parts[:level])

        if rounded_key not in merged_dict:
            merged_dict[rounded_key] = []

        # Merge the lists at the specified level
        merged_dict[rounded_key].extend(data_list)

    return merged_dict


def flatten_dict(input_dict):
    flat_list = []

    for key, value in input_dict.items():
        if isinstance(value, list):
            for item in value:
                flat_list.append({key: item})
        else:
            flat_list.append({key: value})

    return flat_list


# To be used on the pack_to_cards dict to reverse it into cards to pack
def reverse_and_flatten_dict(input_dict):
    new_dict = {}
    for key, values in input_dict.items():
        for value in values:
            new_dict[value] = key
    return new_dict


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
        save_data_to_pickle(data_file_path)

    pack_to_cards = load_data_from_json(os.path.join(data_path, "packCards.json"))
    cards_to_pack = reverse_and_flatten_dict(pack_to_cards)

    all_data_dict = round_date_keys(date_to_metrics, 0)
    insights.count_pack_victory_rate(all_data_dict[""])
