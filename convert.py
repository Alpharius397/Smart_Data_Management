import pandas as pd
import os

SAMPLE_IMAGE = os.path.join(os.path.dirname(__file__),'img','sample-1.jpg')
""" Sample Image """

def convert_all_sheets_to_csv(input_file, output_folder):
    """
    Converts all sheets in an Excel (.xlsx) file to separate CSV files.

    :param input_file: Path to the input .xlsx file.
    :param output_folder: Folder where the CSV files will be saved.
    """
    try:
        # Read all sheets from the Excel file
        all_sheets = pd.read_excel(input_file, sheet_name=None, engine='openpyxl')
        
        # Iterate through all sheets and save each as a CSV
        for sheet_name, data in all_sheets.items():
            data['IMAGE'] = SAMPLE_IMAGE # adding image path to csv
            output_file = f"{output_folder}/{sheet_name}.csv"
            data.to_csv(output_file, index=False)
            print(f"Saved sheet '{sheet_name}' to '{output_file}'.")
    except Exception as e:
        print(f"Error: {e}")

# Example usage
input_file = "FORMAT.xlsx"  # Replace with your .xlsx file path
output_folder = "output_csv"  # Replace with your desired output folder path

# Create the output folder if it doesn't exist
import os
os.makedirs(output_folder, exist_ok=True)

convert_all_sheets_to_csv(input_file, output_folder)
