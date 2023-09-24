import json
import os
import pickle


def process_file(file_path, data, encoding='utf-8'):
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
    data[relative_path] = sub_list


def iterate_directory(directory, encoding='utf-8'):
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            process_file(file_path, encoding)


def save_data_to_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)


def load_data_from_json(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data


def save_data_to_pickle(filename, data):
    with open(filename, 'wb') as file:
        pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)


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


# To be used on the pack_to_cards dict to reverse it into cards to pack
def reverse_and_flatten_dict(input_dict):
    new_dict = {}
    for key, values in input_dict.items():
        for value in values:
            new_dict[value] = key
    return new_dict