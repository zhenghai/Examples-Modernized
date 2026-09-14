import pandas as pd

# Load your file (replace 'your_file.csv' with your actual file path)
file_path = "Pu Course Attendance Tableau Testing.csv"
df = pd.read_csv(file_path)

# 1. Convert 'Actual Attendance' to numeric to ensure accurate filtering,
# then remove all rows where 'Actual Attendance' is equal to 0
df["Actual Attendance"] = pd.to_numeric(df["Actual Attendance"], errors="coerce")
df = df[df["Actual Attendance"] != 0]

# 2. Drop the requested columns if they exist in the dataframe
columns_to_remove = ["Resource Grouping", "Resource", "Special Instructions"]
df = df.drop(columns=[col for col in columns_to_remove if col in df.columns])

# 3. Remove duplicated entries with the same "Reservation ID"
df = df.drop_duplicates(subset=["Reservation ID"], keep="first")

# 4. Remove duplicated entries with the same "Booking ID"
df = df.drop_duplicates(subset=["Booking ID"], keep="first")

# Save the cleaned data to a new file
output_path = "Pu Course Attendance Tableau Testingcleaned.csv"
df.to_csv(output_path, index=False)

print(f"Data cleaned successfully! Saved to {output_path}")
