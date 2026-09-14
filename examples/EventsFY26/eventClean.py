import re
import pandas as pd

filename = "Events Reporting Spreadsheet_TestFY26.csv"

# 1. Load the CSV file safely handling encoding issues
try:
    df = pd.read_csv(filename, encoding="utf-8-sig")
except UnicodeDecodeError:
    df = pd.read_csv(filename, encoding="latin-1")

# Clean up all column headers by stripping hidden spaces from their names
df.columns = df.columns.str.strip()

# Drop all "Unnamed" columns that clutter the end of your spreadsheet
df = df.loc[:, ~df.columns.str.startswith("Unnamed:")]

# Set explicit column names based on your layout
attendance_col = "Actual Attendance #"
source_location_col = "Location / Room"
target_building_col = "Building / Outside / Off Campus / Virtual"


# 2. Clean characters from Attendance column and remove blank entries
def clean_attendance_to_numbers(val):
    if pd.isna(val):
        return pd.NA
    # Extract only digits from the value using regex (\D means non-digits)
    digits = re.sub(r"\D", "", str(val))
    # If no digits remain, return a null marker
    if digits == "":
        return pd.NA
    return int(digits)


if attendance_col in df.columns:
    print(f"Cleaning attendance column: '{attendance_col}'")

    # Apply character stripping logic to get pure numbers
    df[attendance_col] = df[attendance_col].apply(clean_attendance_to_numbers)

    # Drop any rows where attendance is now null or empty
    df = df.dropna(subset=[attendance_col])
else:
    print(
        f"Warning: Could not find exact column '{attendance_col}'. Please verify your CSV headers."
    )


# 3. Clean the "Location / Room" column
def clean_location_text(val):
    if pd.isna(val):
        return val

    text = str(val)

    # A. Remove everything starting from "confirmed" to the end (case-insensitive)
    text = re.sub(r"confirmed.*", "", text, flags=re.IGNORECASE)

    # B. Remove any isolated opening or closing parentheses
    text = re.sub(r"[()]", "", text)

    # C. Existing logic: Strip digits, spaces, hashtags, dashes, & ampersands from the start
    text = re.sub(r"^[\d\s#\-&]+", "", text)

    # D. Final polish to clear any trailing/leading whitespace left behind after changes
    return text.strip()


if source_location_col in df.columns:
    df[source_location_col] = df[source_location_col].apply(clean_location_text)


# 4. Fill empty entries in the Building column with "Art Museum"
if target_building_col in df.columns:
    # First, handle standard pandas NaN null entries
    df[target_building_col] = df[target_building_col].fillna("Art Museum")

    # Second, handle entries that look empty but are actually empty text strings or blank spaces
    df[target_building_col] = df[target_building_col].astype(str).str.strip()
    df[target_building_col] = df[target_building_col].replace(
        "", "Art Museum"
    )

    # Clean up standard 'nan' text artifacts that can appear during string conversion
    df[target_building_col] = df[target_building_col].replace(
        "NAN", "Art Museum"
    )


# 5. Save to a clean, excel-friendly spreadsheet
df.to_csv(
    "Events Reporting Spreadsheet_TestFY26cleaned.csv",
    index=False,
    encoding="utf-8-sig",
)
print(
    "Process complete! All updates applied based on exact column configurations."
)
