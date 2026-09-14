import pandas as pd

# --------------------------------------------------
# 1. Load the CSV file
# --------------------------------------------------

input_file = r"C:\Users\hz2005\Downloads\AOH2025c.csv"

df = pd.read_csv(input_file)

# Clean column names in case there are extra spaces
df.columns = df.columns.str.strip()

print("Columns found:")
print(df.columns.tolist())

# --------------------------------------------------
# 2. Convert Hour of Entry to a proper datetime
# --------------------------------------------------

df["Hour of Entry"] = pd.to_datetime(
    df["Hour of Entry"].astype(str).str.strip(),
    format="%I:%M %p"
)

# --------------------------------------------------
# 3. Create the hourly summary
# --------------------------------------------------

hourly_totals = df.groupby(
    df["Hour of Entry"].dt.strftime("%I:%M %p")
)[
    ["Number of Visitors", "Event", "Visitors in Art Space"]
].sum()

# --------------------------------------------------
# 4. Put metrics in rows and hours in columns
# --------------------------------------------------

pivot_table = hourly_totals.T

# --------------------------------------------------
# 5. Put hours in chronological order
# --------------------------------------------------

hour_order = [
    "10:00 AM",
    "11:00 AM",
    "12:00 PM",
    "01:00 PM",
    "02:00 PM",
    "03:00 PM",
    "04:00 PM",
    "05:00 PM",
    "06:00 PM",
    "07:00 PM",
    "08:00 PM",
]

# Only keep hours that actually exist in the data
existing_hours = [
    hour for hour in hour_order
    if hour in pivot_table.columns
]

pivot_table = pivot_table.reindex(
    columns=existing_hours,
    fill_value=0
)

# --------------------------------------------------
# 6. Display result
# --------------------------------------------------

print("\nHourly Pivot Table:")
print(pivot_table)

# --------------------------------------------------
# 7. Export to Excel
# --------------------------------------------------

output_file = "visitor_hourly_pivot.xlsx"

pivot_table.to_excel(output_file)

print(f"\nSaved to: {output_file}")
