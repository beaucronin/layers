import urllib.parse
import re
import basket_case as bc


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
    path_components = path.split('/')
    
    # Extract the place name and latitude and longitude from the path components
    name = bc.title(urllib.parse.unquote(path_components[3]).replace('+', ' '))
    data_string = path_components[5]
    data_fields = data_string.split('!')
    lat = None
    lng = None
    for df in data_fields:
        if df.startswith('3d'): 
            # latitude
            lat = float(df[2:])
        elif df.startswith('4d'):
            # longitude
            lng = float(df[2:])

    if lat is None or lng is None:
        # Try to extract the latitude and longitude from the path
        lat_lng_string = path_components[4]
        lat_lng_match = re.search(r'@?([\d.-]+),([\d.-]+)', lat_lng_string)
        if lat_lng_match:
            lat = float(lat_lng_match.group(1))
            lng = float(lat_lng_match.group(2))
        else:
            lat = None
            lng = None
    
    # Return the place info as a dictionary
    return {'description': name, 'latitude': lat, 'longitude': lng}
