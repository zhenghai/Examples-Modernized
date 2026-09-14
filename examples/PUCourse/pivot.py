import pandas as pd

# Load your file (replace with your actual file path)
file_path = "Pu Course Attendance Tableau Testingcleaned.csv"
df = pd.read_csv(file_path)

# 1. Clean and standardize the column data
df["Group"] = df["Group"].fillna("Unassigned/Other").str.strip()
df["Actual Attendance"] = (
    pd.to_numeric(df["Actual Attendance"], errors="coerce").fillna(0).astype(int)
)
df["Duration (Minutes)"] = (
    pd.to_numeric(df["Duration (Minutes)"], errors="coerce").fillna(0).astype(int)
)

# 2. Pivot the data to aggregate both metrics by Group
# Using 'sum' calculates both the total visitor footprint and the total room-time used
group_pivot = df.pivot_table(
    index="Group",
    values=["Actual Attendance", "Duration (Minutes)"],
    aggfunc="sum",
).reset_index()

# Divide the entire column by 60 and round the results
group_pivot["Duration (Hours)"] = (group_pivot["Duration (Minutes)"] / 60).round(2)

# 3. Explicitly reorder columns to put Duration (Minutes) as the second column
#group_pivot = group_pivot[["Group", "Duration (Minutes)", "Actual Attendance"]]

# 4. Sort the results from the highest attendance footprint to the lowest
group_pivot = group_pivot.sort_values(by="Actual Attendance", ascending=False)

# 5. Save the summary file
output_path = "attendance_and_duration_pivot_by_group.csv"
group_pivot.to_csv(output_path, index=False)

print("Reservation data pivoted by Group successfully!")
print(f"Summary matrix saved to: {output_path}")

# Display a preview of the summary matrix in the terminal
print("Group Summary Preview:")
print(group_pivot.to_string(index=False))
