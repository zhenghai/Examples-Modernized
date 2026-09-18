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
# STATE FIPS -> ABBREVIATION
# ============================================================

STATE_FIPS = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
}


def state_from_place_geoid(place_geoid):
    """
    Census Place GEOIDs begin with the two-digit
    state FIPS code.

    Example:
        3451000 -> 34 -> NJ
    """

    place_geoid = str(place_geoid).strip()

    if len(place_geoid) < 2:
        return ""

    state_fips = place_geoid[:2]

    return STATE_FIPS.get(
        state_fips,
        ""
    )


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
        # Get state from Place GEOID
        # ----------------------------------------------------

        state = state_from_place_geoid(
            place_geoid
        )


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
                existing["state"]
                == state
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
            "state": state,
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
            key=lambda x: (
                x["state"].lower(),
                x["city"].lower()
            )
        )


        # ----------------------------------------------------
        # Primary city/state
        #
        # A ZCTA can overlap multiple Census Places.
        # We preserve all of them.
        # ----------------------------------------------------

        if places:

            primary_city = places[0]["city"]
            primary_state = places[0]["state"]

        else:

            primary_city = ""
            primary_state = ""


        result[zip_code] = {
            "city": primary_city,
            "state": primary_state,
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
                f'{p["city"]}, {p["state"]}'
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
