import csv
import json
import urllib.request
from pathlib import Path


# ============================================================
# FILES
# ============================================================

SURVEY_FILE = Path("NatureNationSurveyZipDistance.json")
OUTPUT_FILE = Path("zip-cities.json")


# ============================================================
# OFFICIAL CENSUS FILE
# ============================================================
#
# This is the actual Census 2020 ZCTA -> Place relationship
# file. It is a TXT file, NOT a ZIP archive.
#
# The file contains:
#
# GEOID_ZCTA5_20
# NAMELSAD_ZCTA5_20
# GEOID_PLACE_20
# NAMELSAD_PLACE_20
#
# Each row represents an intersection between a ZCTA and
# a Census Place.
#
# ============================================================

CENSUS_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/rel2020/"
    "zcta520/tab20_zcta520_place20_natl.txt"
)


# ============================================================
# ZIP NORMALIZATION
# ============================================================

def normalize_zip(value):

    if value is None:
        return ""

    value = str(value).strip()

    digits = "".join(
        c for c in value
        if c.isdigit()
    )

    if not digits:
        return ""

    return digits.zfill(5)


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load survey JSON
    # --------------------------------------------------------

    print()
    print("Loading survey data...")

    with SURVEY_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        survey = json.load(f)


    survey_zips = {
        normalize_zip(zip_code)
        for zip_code in survey.keys()
        if normalize_zip(zip_code)
    }


    print(
        f"Survey ZIP codes: {len(survey_zips)}"
    )

    print(
        ", ".join(
            sorted(survey_zips)
        )
    )


    # --------------------------------------------------------
    # Download Census relationship file
    # --------------------------------------------------------

    print()
    print(
        "Downloading Census ZCTA -> Place file..."
    )

    print(
        CENSUS_URL
    )


    request = urllib.request.Request(
        CENSUS_URL,
        headers={
            "User-Agent":
                "Mozilla/5.0"
        }
    )


    try:

        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            data = response.read()

    except Exception as e:

        print()
        print(
            "ERROR downloading Census file:"
        )

        print(
            repr(e)
        )

        raise


    print(
        f"Downloaded {len(data):,} bytes"
    )


    # --------------------------------------------------------
    # Decode
    # --------------------------------------------------------

    text = data.decode(
        "utf-8-sig"
    )


    # --------------------------------------------------------
    # Parse pipe-delimited Census file
    # --------------------------------------------------------

    lines = text.splitlines()


    if not lines:

        raise RuntimeError(
            "Census file is empty."
        )


    reader = csv.DictReader(
        lines,
        delimiter="|"
    )


    print()
    print(
        "Census columns:"
    )

    for field in reader.fieldnames or []:

        print(
            "  " + field
        )


    # --------------------------------------------------------
    # Verify expected fields
    # --------------------------------------------------------

    required_fields = [
        "GEOID_ZCTA5_20",
        "NAMELSAD_ZCTA5_20",
        "GEOID_PLACE_20",
        "NAMELSAD_PLACE_20",
    ]


    missing_fields = [
        field
        for field in required_fields
        if field not in (reader.fieldnames or [])
    ]


    if missing_fields:

        raise RuntimeError(
            "The Census file does not contain the expected "
            "columns.\n\n"
            "Missing:\n"
            + "\n".join(
                missing_fields
            )
        )


    # --------------------------------------------------------
    # Build ZIP -> Census places
    # --------------------------------------------------------

    places_by_zip = {
        zip_code: []
        for zip_code in survey_zips
    }


    rows_read = 0
    rows_matched = 0


    for row in reader:

        rows_read += 1


        zip_code = normalize_zip(
            row.get(
                "GEOID_ZCTA5_20",
                ""
            )
        )


        if zip_code not in survey_zips:

            continue


        rows_matched += 1


        place_name = (
            row.get(
                "NAMELSAD_PLACE_20",
                ""
            )
            or ""
        ).strip()


        place_geoid = (
            row.get(
                "GEOID_PLACE_20",
                ""
            )
            or ""
        ).strip()


        # Some relationship records can have no place.
        if not place_name:

            continue


        # ----------------------------------------------------
        # Clean Census suffixes
        # ----------------------------------------------------

        display_name = place_name


        suffixes = [
            " CDP",
            " city",
            " town",
            " village",
            " borough",
            " township",
            " municipality",
        ]


        for suffix in suffixes:

            if display_name.lower().endswith(
                suffix.lower()
            ):

                display_name = (
                    display_name[
                        : -len(suffix)
                    ]
                    .strip()
                )

                break


        # ----------------------------------------------------
        # Avoid duplicates
        # ----------------------------------------------------

        already_exists = False


        for existing in places_by_zip[zip_code]:

            if (
                existing["city"]
                == display_name
                and
                existing["geoid"]
                == place_geoid
            ):

                already_exists = True
                break


        if already_exists:

            continue


        places_by_zip[zip_code].append({
            "city": display_name,
            "census_name": place_name,
            "geoid": place_geoid,
        })


    # --------------------------------------------------------
    # Build final JSON
    # --------------------------------------------------------

    result = {}


    for zip_code in sorted(
        survey_zips
    ):

        places = places_by_zip.get(
            zip_code,
            []
        )


        # ----------------------------------------------------
        # Sort places alphabetically
        # ----------------------------------------------------

        places.sort(
            key=lambda x: x["city"].lower()
        )


        # ----------------------------------------------------
        # Primary city
        #
        # A ZCTA can overlap multiple Census Places.
        # We preserve all of them.
        # ----------------------------------------------------

        if places:

            primary_city = places[0]["city"]

        else:

            primary_city = ""


        result[zip_code] = {
            "city": primary_city,
            "places": places
        }


    # --------------------------------------------------------
    # Write JSON
    # --------------------------------------------------------

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False
        )


    # --------------------------------------------------------
    # Print report
    # --------------------------------------------------------

    found = 0
    missing = 0


    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)


    for zip_code in sorted(result):

        item = result[zip_code]

        places = item["places"]


        if places:

            found += 1


            names = [
                p["city"]
                for p in places
            ]


            print(
                f"{zip_code}: "
                + ", ".join(names)
            )

        else:

            missing += 1

            print(
                f"{zip_code}: "
                "NO CENSUS PLACE"
            )


    print()
    print("=" * 70)

    print(
        f"Census rows read: {rows_read:,}"
    )

    print(
        f"Rows matching survey ZIPs: "
        f"{rows_matched:,}"
    )

    print(
        f"ZIPs with Census places: "
        f"{found}"
    )

    print(
        f"ZIPs without Census places: "
        f"{missing}"
    )

    print()
    print(
        f"Created: {OUTPUT_FILE}"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
