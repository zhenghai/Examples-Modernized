import json
from pathlib import Path

import zipcodes


# ============================================================
# FILES
# ============================================================

SURVEY_FILE = Path(
    "NatureNationSurveyZipDistance.json"
#    "MiraclesBorderSurveyZipDistance.json"
)

OUTPUT_FILE = Path(
    "NatureNationSurveyZip-cities.json"
#    "MiraclesBorderSurveyZip-cities.json"
)


# ============================================================
# ZIP NORMALIZATION
# ============================================================

def normalize_zip(value):

    if value is None:
        return ""

    digits = "".join(
        c
        for c in str(value)
        if c.isdigit()
    )

    if not digits:
        return ""

    return digits.zfill(5)


# ============================================================
# LOAD SURVEY ZIPs
# ============================================================

def load_survey_zips():

    print()
    print(
        "Loading survey data..."
    )

    if not SURVEY_FILE.exists():

        raise FileNotFoundError(
            f"Could not find {SURVEY_FILE}"
        )


    with SURVEY_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        survey = json.load(f)


    if not isinstance(
        survey,
        dict
    ):

        raise RuntimeError(
            f"{SURVEY_FILE} must contain "
            "a JSON object."
        )


    survey_zips = set()


    for zip_code in survey.keys():

        normalized = normalize_zip(
            zip_code
        )

        if normalized:

            survey_zips.add(
                normalized
            )


    print(
        f"Survey ZIP codes: "
        f"{len(survey_zips)}"
    )


    return survey_zips


# ============================================================
# LOOK UP ZIP
# ============================================================

def lookup_zip(zip_code):

    try:

        matches = zipcodes.matching(
            zip_code
        )

    except Exception as error:

        print(
            f"WARNING: could not look up "
            f"{zip_code}: {error}"
        )

        return None


    if not matches:

        return None


    # --------------------------------------------------------
    # The Zipcodes package normally returns the exact ZIP
    # record. Use the first matching record.
    # --------------------------------------------------------

    record = matches[0]


    city = (
        record.get(
            "city",
            ""
        )
        or ""
    ).strip()


    state = (
        record.get(
            "state",
            ""
        )
        or ""
    ).strip()


    if not city or not state:

        return None


    # --------------------------------------------------------
    # Preserve the additional city information supplied by
    # the Zipcodes database.
    # --------------------------------------------------------

    acceptable_cities = record.get(
        "acceptable_cities",
        []
    )


    unacceptable_cities = record.get(
        "unacceptable_cities",
        []
    )


    if not isinstance(
        acceptable_cities,
        list
    ):

        acceptable_cities = []


    if not isinstance(
        unacceptable_cities,
        list
    ):

        unacceptable_cities = []


    return {

        "city":
            city,

        "state":
            state,

        "acceptable_cities":
            acceptable_cities,

        "unacceptable_cities":
            unacceptable_cities,

        "county":
            record.get(
                "county",
                ""
            ),

        "active":
            record.get(
                "active",
                True
            ),

        "zip_code_type":
            record.get(
                "zip_code_type",
                ""
            ),

    }


# ============================================================
# BUILD ZIP CITY DATA
# ============================================================

def build_zip_cities():

    survey_zips = load_survey_zips()


    result = {}


    found = 0

    missing = 0


    print()
    print(
        "Looking up ZIP codes..."
    )


    print(
        "-" * 70
    )


    for zip_code in sorted(
        survey_zips
    ):

        record = lookup_zip(
            zip_code
        )


        if record is None:

            missing += 1


            print(
                f"{zip_code}: "
                "NOT FOUND"
            )

            continue


        found += 1


        result[zip_code] = record


        print(
            f'{zip_code}: '
            f'{record["city"]}, '
            f'{record["state"]}'
        )


    # ========================================================
    # WRITE JSON
    # ========================================================

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


    # ========================================================
    # VERIFY 08540
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "08540 CHECK"
    )

    print(
        "=" * 70
    )


    if "08540" in result:

        record = result[
            "08540"
        ]


        print(
            f'ZIP:   08540'
        )

        print(
            f'City:  {record["city"]}'
        )

        print(
            f'State: {record["state"]}'
        )

        print(
            f'County: {record["county"]}'
        )

        print(
            f'Type:  {record["zip_code_type"]}'
        )


    else:

        print(
            "08540 was not found."
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print(
        "=" * 70
    )

    print(
        "RESULTS"
    )

    print(
        "=" * 70
    )


    print(
        f"Survey ZIPs:       "
        f"{len(survey_zips):,}"
    )


    print(
        f"ZIPs found:        "
        f"{found:,}"
    )


    print(
        f"ZIPs not found:    "
        f"{missing:,}"
    )


    print()
    print(
        f"Created: "
        f"{OUTPUT_FILE}"
    )


    print(
        "=" * 70
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    build_zip_cities()
