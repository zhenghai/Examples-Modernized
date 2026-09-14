import csv
import json

result = {
    "name": "Visitors by Time",
    "children": []
}

with open("AOH2025Time.csv", "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        time = row["Time"]

        time_data = {
            "name": time,
            "children": [
                {
                    "name": "Number of Visitors",
                    "size": int(row["Number of Visitors"])
                },
                {
                    "name": "Event",
                    "size": int(row["Event"])
                },
                {
                    "name": "Visitors in Art Space",
                    "size": int(row["Visitors in Art Space"])
                }
            ]
        }

        result["children"].append(time_data)

# Save as JSON
with open("AOH2025Time.json", "w", encoding="utf-8") as file:
    json.dump(result, file, indent=2)

print(json.dumps(result, indent=2))
