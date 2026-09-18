import csv
import pgeocode

# Initialize the US postal code distance calculator
dist_calc = pgeocode.GeoDistance('US')
TARGET_ZIP = '08544'

input_file = 'NatureNationSurveyZip.csv'   
output_file = 'NatureNationSurveyZipDistance.csv'

with open(input_file, mode='r', encoding='utf-8') as infile, \
     open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
    
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    is_first_row = True
    
    for row in reader:
        # Skip completely empty rows
        if not row:
            continue
            
        # 1. Handle the header row dynamically
        if is_first_row:
            row.append('Distance (miles)')
            writer.writerow(row)
            is_first_row = False
            continue
            
        # Skip structural metadata lines that aren't data rows
        if len(row) < 2:
            writer.writerow(row)
            continue
            
        zip_code = row[0].strip()
        
        # Ensure the zip code is padded to 5 digits (e.g., '2114' -> '02114')
        padded_zip = zip_code.zfill(5)
        
        # Calculate distance in kilometers
        distance_km = dist_calc.query_postal_code(padded_zip, TARGET_ZIP)
        
        # Verify valid response and convert to miles (1 km ≈ 0.621371 miles)
        if not hasattr(distance_km, '__iter__') and distance_km >= 0:
            distance_miles = distance_km * 0.621371
            distance_str = f"{distance_miles:.2f}"
        else:
            distance_str = "N/A"
            
        # Update the row's ZIP code to the clean padded version and append the distance
        row[0] = padded_zip
        row.append(distance_str)
        writer.writerow(row)

print(f"Processing complete! Saved to {output_file}")
