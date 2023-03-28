import urllib.parse
import re
import basket_case as bc
import geojson_pydantic as gp
from .schemas import ObservationEvent

import math

def tile_to_lat_lon_bbox(z, y, x):
    """
    Convert z, y, and x Slippy map tile indices to a lat/long bounding box.

    Args:
        z (int): The zoom level.
        y (int): The tile row index.
        x (int): The tile column index.

    Returns:
        tuple: A tuple containing the bounding box coordinates in the format:
               (south_latitude, west_longitude, north_latitude, east_longitude)
    """
    # This code, except for this comment, was written by ChatGPT

    def tile_to_lat(y, z):
        n = math.pi - 2 * math.pi * y / (2 ** z)
        return math.degrees(math.atan(math.sinh(n)))

    def tile_to_lon(x, z):
        return x / (2 ** z) * 360 - 180

    south_lat = tile_to_lat(y + 1, z)
    west_lon = tile_to_lon(x, z)
    north_lat = tile_to_lat(y, z)
    east_lon = tile_to_lon(x + 1, z)

    return (south_lat, west_lon, north_lat, east_lon)


def geohash_to_lat_lon_bbox(geohash):
    """
    Convert a geohash to a lat/long bounding box.

    Args:
        geohash (str): The geohash string of varying length.

    Returns:
        tuple: A tuple containing the bounding box coordinates in the format:
               (south_latitude, west_longitude, north_latitude, east_longitude)
    """
    # This code, except for this comment, was written by ChatGPT

    base32 = "0123456789bcdefghjkmnpqrstuvwxyz"
    bits = [16, 8, 4, 2, 1]
    lon_range = [-180.0, 180.0]
    lat_range = [-90.0, 90.0]

    is_even = True
    char = 0

    for c in geohash:
        char = base32.index(c)

        for mask in bits:
            if is_even:
                mid = (lon_range[0] + lon_range[1]) / 2
                if char & mask:
                    lon_range[0] = mid
                else:
                    lon_range[1] = mid
            else:
                mid = (lat_range[0] + lat_range[1]) / 2
                if char & mask:
                    lat_range[0] = mid
                else:
                    lat_range[1] = mid

            is_even = not is_even

    south_lat, north_lat = lat_range
    west_lon, east_lon = lon_range

    return (south_lat, west_lon, north_lat, east_lon)


def enum_to_dict(enum, alpha=False):
    """Convert an enum to a dict of title-cased keys and the corresponding values, optionally alphabetizing."""
    out = {bc.title(e.name.lower().replace("_", " ")): e.value for e in enum}
    if alpha:
        out = {k: out[k] for k in sorted(out.keys())}
    return out


def extract_place_info(url):
    """Extract the place name and latitude and longitude from a Google Maps URL."""

    # Parse the URL and extract the path
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path

    # Split the path into a list of components
    path_components = path.split("/")

    # Extract the place name and latitude and longitude from the path components
    name = bc.title(urllib.parse.unquote(path_components[3]).replace("+", " "))
    data_string = path_components[5]
    data_fields = data_string.split("!")
    lat = None
    lng = None
    for df in data_fields:
        if df.startswith("3d"):
            # latitude
            lat = float(df[2:])
        elif df.startswith("4d"):
            # longitude
            lng = float(df[2:])

    if lat is None or lng is None:
        # Try to extract the latitude and longitude from the path
        lat_lng_string = path_components[4]
        lat_lng_match = re.search(r"@?([\d.-]+),([\d.-]+)", lat_lng_string)
        if lat_lng_match:
            lat = float(lat_lng_match.group(1))
            lng = float(lat_lng_match.group(2))
        else:
            lat = None
            lng = None

    # Return the place info as a dictionary
    return {"description": name, "latitude": lat, "longitude": lng}


def format_as_native(result):
    pass


def format_as_geojson(result):
    # extract geojson features from each row in the result, and add them to a FeatureCollection
    features = []
    for row in result:
        features.append(
            gp.Feature(
                geometry=gp.Point(coordinates=[row["longitude"], row["latitude"]]),
                properties=row,
            )
        )
    return gp.FeatureCollection(features=features)


def canonicalize_identifier(orig: str) -> str:
    """Canonicalize an identifier."""
    return orig.lower().replace(" ", "_").strip()


def compute_reward(observation_event: ObservationEvent) -> int:
    """Compute the reward for an observation."""
    return observation_event.num_observations() * 10


LEVELS = [
    0,
    300,
    900,
    2700,
    6500,
    14000,
    23000,
    34000,
    48000,
    64000,
    85000,
    100000,
    120000,
    140000,
    165000,
    195000,
    225000,
    265000,
    305000,
    355000,
]


def level_for_xp(xp: int) -> int:
    """Compute the level for a given amount of XP."""
    for i, level_xp in enumerate(LEVELS):
        if xp < level_xp:
            return i
    return len(LEVELS)
