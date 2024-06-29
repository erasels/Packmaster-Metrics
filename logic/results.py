def print_insight_dict(insights):
    max_width = max(len(sheet_name) for sheet_name in insights.keys())
    for sheet_name, details in insights.items():
        print(f"Sheet Name: {sheet_name.ljust(max_width)}")
        print(f"Description: {details['description']}")
        print("Headers: " + ", ".join(details['headers']))
        col_width = max(len(str(item)) for row in details['data'] for item in row)
        header_row = details['headers']
        max_line_length = len(" | ".join(str(item).ljust(col_width) for item in header_row))
        print("-" * max_line_length)  # Separator between headers and data
        print(" | ".join(str(item).ljust(col_width) for item in header_row))
        print("-" * max_line_length)  # Separator between header and data rows
        for row in details['data']:
            print(" | ".join(str(item).ljust(col_width) for item in row))
        print("-" * max_line_length)  # Separator for readability
