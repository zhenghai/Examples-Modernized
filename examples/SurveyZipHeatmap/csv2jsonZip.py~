import csv
import json

def convert_csv_to_json(csv_filepath, json_filepath):
    zip_lookup_map = {}
    
    with open(csv_filepath, mode='r', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file)
        # --- ROBUST HEADER MATCHING ---
        # Normalize headers by stripping whitespace and converting to lowercase
        normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}
        
        # Dynamically locate the correct column key name
        target_key = None
        if 'zip code' in normalized_headers:
            target_key = normalized_headers['zip code']
        elif 'zipcode' in normalized_headers:
            target_key = normalized_headers['zipcode']
        elif 'zip' in normalized_headers:
            target_key = normalized_headers['zip']
            
        if not target_key:
            raise KeyError(f"Could not find a ZIP code column. Available columns are: {reader.fieldnames}")
        # ------------------------------
        for row in reader:
            zip_code = row[target_key].strip()
            
            # Skip invalid non-geographic or non-routable placeholder entries
            if zip_code == "08571" or not zip_code:
                continue
                
            # Build key index lookup object
            zip_lookup_map[zip_code] = {
                "count": int(row['Count']),
                "distance": row['Distance (miles)'].strip()
            }
            
    # Write optimized JSON output file
    with open(json_filepath, mode='w', encoding='utf-8') as json_file:
        json.dump(zip_lookup_map, json_file, indent=4)
    print(f"Success: Processed data saved cleanly to '{json_filepath}'")

# Execution Hook
if __name__ == "__main__":
    # Assumes your data file is stored in the same folder as 'data.csv'
    convert_csv_to_json('NatureNationSurveyZipDistance.csv', 'NatureNationSurveyZipDistance.json')
