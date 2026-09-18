import json
import os
import shutil
import tempfile
import zipfile

import geopandas as gpd
import requests


# ============================================================
# FILES
# ============================================================

INPUT_JSON = "NatureNationSurveyZipDistance.json"
OUTPUT_GEOJSON = "zip-boundaries.geojson"

# Official Census 2020 ZCTA shapefile
CENSUS_URL = (
    "https://www2.census.gov/geo/tiger/TIGER2020/ZCTA5/"
    "tl_2020_us_zcta510.zip"
)

# Add surrounding ZIP boundaries around the survey ZIPs.
# Increase this if you want a larger surrounding region.
BUFFER_DEGREES = 1.0


# ============================================================
# HELPERS
# ============================================================

def normalize_zip(value):
    """Always return a 5-digit ZIP string."""
    digits = "".join(c for c in str(value) if c.isdigit())
    return digits.zfill(5)


# ============================================================
# LOAD SURVEY DATA
# ============================================================

if not os.path.exists(INPUT_JSON):
    raise FileNotFoundError(
        f"Cannot find {INPUT_JSON}. "
        "Put this script in the same folder as the JSON file."
    )

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    survey_data = json.load(f)

survey_zips = {
    normalize_zip(z)
    for z in survey_data.keys()
}

survey_zips.discard("")

print()
print("=" * 70)
print("GENERATING ZIP BOUNDARIES")
print("=" * 70)
print()
print(f"Survey ZIPs: {len(survey_zips)}")
print()


# ============================================================
# TEMPORARY DIRECTORY
# ============================================================

temp_dir = tempfile.mkdtemp(
    prefix="census_zcta_"
)

try:

    zip_file = os.path.join(
        temp_dir,
        "zcta.zip"
    )

    extract_dir = os.path.join(
        temp_dir,
        "zcta"
    )

    os.makedirs(
        extract_dir,
        exist_ok=True
    )


    # ========================================================
    # DOWNLOAD CENSUS FILE
    # ========================================================

    print("Downloading Census 2020 ZCTA data...")
    print(CENSUS_URL)
    print()

    response = requests.get(
        CENSUS_URL,
        stream=True,
        timeout=600
    )

    response.raise_for_status()

    total = int(
        response.headers.get(
            "content-length",
            0
        )
    )

    downloaded = 0

    with open(zip_file, "wb") as f:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if not chunk:
                continue

            f.write(chunk)
            downloaded += len(chunk)

            if total:
                pct = (
                    downloaded /
                    total *
                    100
                )

                print(
                    f"\rDownloaded "
                    f"{downloaded / 1024 / 1024:.1f} MB "
                    f"of "
                    f"{total / 1024 / 1024:.1f} MB "
                    f"({pct:.1f}%)",
                    end="",
                    flush=True
                )

    print()
    print()
    print("Download complete.")
    print()


    # ========================================================
    # EXTRACT SHAPEFILE
    # ========================================================

    print("Extracting Census shapefile...")

    with zipfile.ZipFile(
        zip_file,
        "r"
    ) as z:

        z.extractall(
            extract_dir
        )

    print("Extraction complete.")
    print()


    # ========================================================
    # FIND SHAPEFILE
    # ========================================================

    shp_file = None

    for root, dirs, files in os.walk(
        extract_dir
    ):

        for filename in files:

            if filename.lower().endswith(
                ".shp"
            ):

                shp_file = os.path.join(
                    root,
                    filename
                )

                break

        if shp_file:
            break


    if not shp_file:

        raise RuntimeError(
            "Could not find the Census .shp file."
        )


    print(
        "Shapefile:",
        shp_file
    )
    print()


    # ========================================================
    # READ ZCTA DATA
    # ========================================================

    print(
        "Reading ZCTA geometries..."
    )

    zctas = gpd.read_file(
        shp_file
    )

    print(
        f"Loaded {len(zctas):,} ZCTAs."
    )
    print()


    # ========================================================
    # FIND ZIP COLUMN
    # ========================================================

    zip_column = None

    for candidate in [
        "ZCTA5CE20",
        "ZCTA5CE10",
        "GEOID20",
        "GEOID"
    ]:

        if candidate in zctas.columns:

            zip_column = candidate
            break


    if zip_column is None:

        raise RuntimeError(
            "Could not identify the ZCTA ZIP column.\n"
            f"Available columns: {list(zctas.columns)}"
        )


    print(
        "Using ZIP column:",
        zip_column
    )
    print()


    zctas["ZIP"] = (
        zctas[zip_column]
        .astype(str)
        .str.replace(
            ".0",
            "",
            regex=False
        )
        .str.zfill(5)
    )


    # ========================================================
    # MAKE SURE WE ARE USING WGS84
    # ========================================================

    zctas = zctas.to_crs(
        "EPSG:4326"
    )


    # ========================================================
    # FIND SURVEY ZIP BOUNDARIES
    # ========================================================

    survey_boundaries = zctas[
        zctas["ZIP"].isin(
            survey_zips
        )
    ].copy()


    found_zips = set(
        survey_boundaries["ZIP"]
    )

    missing_zips = sorted(
        survey_zips -
        found_zips
    )


    print(
        f"Survey boundaries found: "
        f"{len(found_zips)} / {len(survey_zips)}"
    )


    if missing_zips:

        print(
            "Survey ZIPs not found:"
        )

        for z in missing_zips:
            print(
                f"  {z}"
            )

    print()


    if survey_boundaries.empty:

        raise RuntimeError(
            "No survey ZIP boundaries were found."
        )


    # ========================================================
    # DETERMINE MAP EXTENT
    # ========================================================

    minx, miny, maxx, maxy = (
        survey_boundaries.total_bounds
    )


    print("Survey extent:")
    print(
        f"  Longitude: {minx:.4f} → {maxx:.4f}"
    )
    print(
        f"  Latitude:  {miny:.4f} → {maxy:.4f}"
    )
    print()


    # ========================================================
    # EXPAND EXTENT
    # ========================================================

    minx -= BUFFER_DEGREES
    maxx += BUFFER_DEGREES
    miny -= BUFFER_DEGREES
    maxy += BUFFER_DEGREES


    print("Expanded extent:")
    print(
        f"  Longitude: {minx:.4f} → {maxx:.4f}"
    )
    print(
        f"  Latitude:  {miny:.4f} → {maxy:.4f}"
    )
    print()


    # ========================================================
    # SELECT ALL ZIPs TOUCHING REGION
    # ========================================================

    print(
        "Selecting surrounding ZIP boundaries..."
    )


    bounds = zctas.geometry.bounds

    regional = zctas[
        (bounds["maxx"] >= minx) &
        (bounds["minx"] <= maxx) &
        (bounds["maxy"] >= miny) &
        (bounds["miny"] <= maxy)
    ].copy()


    print(
        f"Regional boundaries: "
        f"{len(regional):,}"
    )
    print()


    # ========================================================
    # KEEP ONLY WHAT D3 NEEDS
    # ========================================================

    regional = regional[
        [
            "ZIP",
            "geometry"
        ]
    ].copy()


    # ========================================================
    # OPTIONAL SIMPLIFICATION
    # ========================================================
    #
    # Census polygons contain a LOT of points.
    #
    # This makes the GeoJSON dramatically smaller and
    # considerably faster for D3.
    #
    # 0.00005 degrees is approximately 5 meters.
    #
    # Increase to 0.0001 or 0.0002 if the resulting file
    # is still too large.
    #

    print(
        "Simplifying geometries..."
    )

    regional["geometry"] = (
        regional.geometry.simplify(
            tolerance=0.00005,
            preserve_topology=True
        )
    )

    print(
        "Simplification complete."
    )
    print()


    # ========================================================
    # WRITE GEOJSON
    # ========================================================

    print(
        f"Writing {OUTPUT_GEOJSON}..."
    )


    regional.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON"
    )


    # ========================================================
    # REPORT
    # ========================================================

    file_size = (
        os.path.getsize(
            OUTPUT_GEOJSON
        ) / 1024 / 1024
    )


    print()
    print("=" * 70)
    print("SUCCESS")
    print("=" * 70)
    print()

    print(
        f"Survey ZIPs:       {len(survey_zips)}"
    )

    print(
        f"Found survey ZIPs: {len(found_zips)}"
    )

    print(
        f"Missing survey:    {len(missing_zips)}"
    )

    print(
        f"Regional ZIPs:     {len(regional)}"
    )

    print(
        f"GeoJSON size:      {file_size:.1f} MB"
    )

    print(
        f"Output:            {OUTPUT_GEOJSON}"
    )

    print()

    if missing_zips:

        print(
            "Missing survey ZIPs:"
        )

        print(
            ", ".join(missing_zips)
        )

        print()

    print(
        "Your D3 HTML can now load:"
    )

    print(
        "    zip-boundaries.geojson"
    )

    print()


finally:

    shutil.rmtree(
        temp_dir,
        ignore_errors=True
    )
