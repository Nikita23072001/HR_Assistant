import pandas as pd

def clean_dict_keys(data_dict):
    """
    Remove leading and trailing whitespaces from dictionary keys
    and standardize keys to lowercase.
    """
    cleaned_dict = {key.strip().lower(): value for key, value in data_dict.items()}
    return cleaned_dict

def append_dict_to_xlsx(data_dict, filename):
    try:
        # Read existing data from the Excel file, if it exists
        try:
            existing_df = pd.read_excel(filename)
        except FileNotFoundError:
            existing_df = pd.DataFrame()  # Create an empty DataFrame if the file doesn't exist
        
        # Standardize keys to lowercase and clean the dictionary keys
        cleaned_data_dict = clean_dict_keys(data_dict)
        
        # Convert the cleaned dictionary data into a DataFrame
        new_row = pd.DataFrame([cleaned_data_dict.values()], columns=cleaned_data_dict.keys())
        
        # Concatenate the existing DataFrame with the new row
        updated_df = pd.concat([existing_df, new_row], ignore_index=True)
        
        # Write the updated DataFrame to the Excel file
        updated_df.to_excel(filename, index=False)
        
        print("Data appended successfully to", filename)
    except Exception as e:
        print("An error occurred:", e)