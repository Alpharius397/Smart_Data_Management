import pandas as pd
import os

SAMPLE_IMAGE = os.path.join(os.path.dirname(__file__),'img','sample-1.jpg')
""" Sample Image """

def convert_all_sheets_to_csv(input_file, output_file):
    """
    Converts all sheets in an Excel (.xlsx) file to separate CSV files.

    :param input_file: Path to the input .xlsx file.
    :param output_folder: Folder where the CSV files will be saved.
    """
    try:
        # Read all sheets from the Excel file
        all_sheets = pd.read_excel(input_file,sheet_name=None)
        
        # Iterate through all sheets and save each as a CSV
        for sheet_name, data in all_sheets.items():
            data['IMAGE'] = SAMPLE_IMAGE # adding image path to csv
            file_name = f"{sheet_name}.csv"
            
            output_file = os.path.join(output_file,file_name)
            
            data.to_csv(output_file, index=False)

    except Exception as e:
        print(f"Error: {e}")

input_file_path = os.path.join(os.path.dirname(__file__),'sample_data','sample.xlsx')
output_folder_path = os.path.join(os.path.dirname(__file__),'sample_data','csv_data')

os.makedirs(output_folder_path, exist_ok=True)

convert_all_sheets_to_csv(input_file_path, output_folder_path)
