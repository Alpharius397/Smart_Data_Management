import pandas as pd

def convert_xlsx_to_csv(input_file, output_file, sheet_name=0):
    """
    Converts an Excel (.xlsx) file to a CSV file.

    :param input_file: Path to the input .xlsx file.
    :param output_file: Path to the output .csv file.
    :param sheet_name: Sheet name or index to convert (default is the first sheet).
    """
    try:
        # Read the specified sheet from the Excel file
        data = pd.read_excel(input_file, sheet_name=sheet_name, engine='openpyxl')
        # Save the data to a CSV file
        data.to_csv(output_file, index=False)
        print(f"Successfully converted '{input_file}' to '{output_file}'.")
    except Exception as e:
        print(f"Error: {e}")

# Example usage
input_file = "FORMAT.xlsx"  # Replace with your .xlsx file path
output_file = "FORMAT.csv"  # Replace with your desired .csv file path
convert_xlsx_to_csv(input_file, output_file)
