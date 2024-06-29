import os


def print_insight_dict(insights):
    for sheet_name, details in insights.items():
        # Sheet header
        max_width = max(len(sheet_name) for sheet_name in insights.keys())
        print(f"Sheet Name: {sheet_name.ljust(max_width)}")
        print(f"Description: {details['description']}")

        # Calculate maximum column width for each column
        headers = details['headers']
        data = details['data']
        col_widths = [max(len(str(item)) for item in [header] + [row[index] for row in data]) for index, header in enumerate(headers)]

        # Print table
        def format_row(row, widths):
            return " | ".join(str(item).ljust(width) for item, width in zip(row, widths))

        # Header and separator
        header_row = format_row(headers, col_widths)
        print("-" * len(header_row))
        print(header_row)
        print("-" * len(header_row))

        # Data rows
        for row in data:
            print(format_row(row, col_widths))
        print("-" * len(header_row))  # End separator


def write_insight_to_file(insights, output_directory="insight_files"):
    # Create the output directory if it does not exist
    os.makedirs(output_directory, exist_ok=True)

    for sheet_name, details in insights.items():
        print(f"Writing {sheet_name} to file.")
        # Prepare the file path
        file_path = os.path.join(output_directory, f"{sheet_name}.txt")

        with open(file_path, 'w', encoding='utf-8') as file:
            # Sheet header
            max_width = max(len(sheet_name) for sheet_name in insights.keys())
            file.write(f"Description: {details['description']}\n")

            # Calculate maximum column width for each column
            headers = details['headers']
            data = details['data']
            col_widths = [max(len(str(item)) for item in [header] + [row[index] for row in data]) for index, header in enumerate(headers)]

            # Helper function to format a row
            def format_row(row, widths):
                return " | ".join(str(item).ljust(width) for item, width in zip(row, widths))

            # Header and separator
            header_row = format_row(headers, col_widths)
            file.write("-" * len(header_row) + "\n")
            file.write(header_row + "\n")
            file.write("-" * len(header_row) + "\n")

            # Data rows
            for row in data:
                file.write(format_row(row, col_widths) + "\n")
            file.write("-" * len(header_row) + "\n")  # End separator
