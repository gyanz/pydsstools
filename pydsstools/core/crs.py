import logging
from pyproj import CRS
from . import HRAP_WKT, SHG_WKT
from .enums import Datum, LocCoordSystem, LocHorizUnits, LocHorizDatum


__all__ = ["hrap", "shg", "albers", "make_albers", "wkt_to_crs", "albers_params_from_wkt",
           "crs_short_name", "is_equal_area_conic", "is_hrap", "crs_to_location_attrs"]

ALBERS_WKT = SHG_WKT

SHG_WKT_CUSTOM = """PROJCS[\"USA_Contiguous_Albers_Equal_Area_Conic_USGS_version\",\
GEOGCS[\"GCS_North_American_{0}\",DATUM[\"D_North_American_{0}\",\
SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],\
UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Albers\"],\
PARAMETER[\"False_Easting\",{1}],PARAMETER[\"False_Northing\",{2}],\
PARAMETER[\"Central_Meridian\",{3}],PARAMETER[\"Standard_Parallel_1\",{4}],\
PARAMETER[\"Standard_Parallel_2\",{5}],PARAMETER[\"Latitude_Of_Origin\",{6}],\
UNIT[\"{7}\",1.0]]"""


HEC_SHG_CELLSIZE = (10000, 5000, 2000, 1000, 500, 200, 100, 50, 20, 10)  # meters
HEC_SHG_APART = (
    "SHG10K",
    "SHG5K",
    "SHG2K",
    "SHG1K",
    "SHG500",
    "SHG200",
    "SHG100",
    "SHG50",
    "SHG20",
    "SHG10",
)  # meters


def hrap():
    return HRAP_WKT

def albers():
    return SHG_WKT

def shg():
    return SHG_WKT

def make_albers(
    datum, false_easting, false_northing, cmeridian, par1, par2, lat_origin, proj_units="Meter"
):
    dtm = "UNDEFINED"
    if datum == Datum.nad83:
        dtm = "1983"
    elif datum == Datum.nad27:
        dtm = "1927"
    return SHG_WKT_CUSTOM.format(
        dtm, false_easting, false_northing, cmeridian, par1, par2, lat_origin, proj_units
    )


def wkt_to_crs(wkt):
    crs = None
    try:
        crs = CRS(wkt)
    except:
        pass
    return crs


def parse_crs(crs):
    if not isinstance(crs, CRS):
        try:
            crs = CRS(crs)
        except Exception:
            logging.warning("Could not parse CRS input: %s", crs)
            return None

    crs = crs.to_dict()
    return crs

def is_equal_area_conic(crs):
    if not isinstance(crs, CRS):
        try:
            crs = CRS.from_user_input(crs)
        except Exception:
            logging.warning("Could not parse CRS input: %s", crs)
            return False

    # geographic CRS → not projected at all
    if crs.is_geographic:
        return False

    op = crs.coordinate_operation
    if op is None:
        return False

    method = op.method_name.lower()
    
    # check for known equal-area conic strings
    equal_area_keywords = [
        "equal area conic",
        "albers",
        "albers conic",
        "albers equal area"
    ]
    
    return any(k in method for k in equal_area_keywords)

def is_hrap(crs) -> bool:
    """
    Return True if the CRS looks like NWS HRAP polar stereographic.
    Accepts WKT, PROJ string, EPSG code, or CRS object.
    """
    if not isinstance(crs, CRS):
        try:
            crs = CRS.from_user_input(crs)
        except Exception:
            logging.warning("Could not parse CRS input: %s", crs)
            return False

    d = crs.to_dict()  # PROJ-style dict

    def approx(val, target, tol=1e-6):
        try:
            return abs(float(val) - target) < tol
        except (TypeError, ValueError):
            return False

    # Quick name-based shortcut (many HRAP WKT names contain 'HRAP')
    if "HRAP" in (crs.name or "").upper():
        return True

    # Parameter-based check
    if d.get("proj") != "stere":
        return False

    ok_lat0 = approx(d.get("lat_0") or d.get("lat0"), 90.0)
    ok_lat_ts = approx(d.get("lat_ts"), 60.0)
    ok_lon0 = approx(d.get("lon_0") or d.get("lon0"), -105.0)

    # Sphere radius (a and b or R)
    a = d.get("a") or d.get("R")
    b = d.get("b") or d.get("R")
    ok_radius = approx(a, 6371200.0) and approx(b, 6371200.0)

    return ok_lat0 and ok_lat_ts and ok_lon0 and ok_radius

def albers_params_from_wkt(wkt):
    crs = parse_crs(wkt)
    info = {}
    info["datum"] = crs["datum"]
    info["proj_units"] = crs["units"]
    info["first_parallel"] = crs["lat_1"]
    info["sec_parallel"] = crs["lat_2"]
    info["central_meridian"] = crs["lon_0"]
    info["lat_origin"] = crs["lat_0"]
    info["false_easting"] = crs["x_0"]
    info["false_northing"] = crs["y_0"]
    return info

def crs_to_location_attrs(crs_input):
    """Map a CRS string or object to LocationInfo-compatible attribute values.

    Returns a dict with keys ``coordinate_system``, ``horizontal_units``,
    ``horizontal_datum``, and ``coordinate_id``, or None if the CRS cannot
    be parsed.
    """
    if not isinstance(crs_input, CRS):
        try:
            crs = CRS.from_user_input(crs_input)
        except Exception:
            logging.warning("Could not parse CRS: %s", crs_input)
            return None
    else:
        crs = crs_input

    # --- coordinate_system and coordinate_id ---
    coord_sys = LocCoordSystem.none
    coordinate_id = 0
    if crs.is_geographic:
        coord_sys = LocCoordSystem.lat_long
    elif crs.is_projected:
        utm_zone = crs.utm_zone
        name = (crs.name or "").lower()
        if utm_zone is not None:
            coord_sys = LocCoordSystem.utm
            coordinate_id = int("".join(filter(str.isdigit, utm_zone)))
        elif "state plane" in name or "spcs" in name:
            coord_sys = LocCoordSystem.state_plane_fips
        elif is_equal_area_conic(crs) or is_hrap(crs):
            coord_sys = LocCoordSystem.local
        else:
            coord_sys = LocCoordSystem.local

    # --- horizontal_units ---
    # crs.linear_units  → PROJ abbreviation: "m", "ft", "us-ft", etc.
    # axis.unit_name    → EPSG full name:    "metre", "US survey foot", etc.
    # Both are checked so neither spelling convention is missed.
    horiz_units = LocHorizUnits.unspecified
    if crs.is_geographic:
        horiz_units = LocHorizUnits.decimal_degrees
    elif crs.is_projected:
        proj_unit = crs.linear_units.lower()          # "m", "ft", "us-ft", ...
        axis_unit = crs.axis_info[0].unit_name.lower() if crs.axis_info else ""
        combined  = proj_unit + " " + axis_unit
        if proj_unit == "m" or "metre" in combined or "meter" in combined:
            horiz_units = LocHorizUnits.meters
        elif "ft" in proj_unit or "foot" in combined or "feet" in combined:
            horiz_units = LocHorizUnits.feet

    # --- horizontal_datum ---
    horiz_datum = LocHorizDatum.unset
    try:
        datum_name = (crs.geodetic_crs.datum.name or "").upper()
    except Exception:
        try:
            datum_name = (crs.datum.name or "").upper()
        except Exception:
            datum_name = ""
    if "NAD83" in datum_name or "NORTH AMERICAN 1983" in datum_name:
        horiz_datum = LocHorizDatum.nad83
    elif "NAD27" in datum_name or "NORTH AMERICAN 1927" in datum_name:
        horiz_datum = LocHorizDatum.nad27
    elif "WGS 84" in datum_name or "WGS84" in datum_name or "WGS_1984" in datum_name:
        horiz_datum = LocHorizDatum.wgs84
    elif "WGS 72" in datum_name or "WGS72" in datum_name or "WGS_1972" in datum_name:
        horiz_datum = LocHorizDatum.wgs72

    return {
        "coordinate_system": coord_sys,
        "horizontal_units":  horiz_units,
        "horizontal_datum":  horiz_datum,
        "coordinate_id":     coordinate_id,
    }


def crs_short_name(crs):
    if not isinstance(crs, CRS):
        try:
            crs = CRS.from_user_input(crs)
        except Exception:
            logging.warning("Could not parse CRS input: %s", crs)
            return False

    name = crs.name
    auth = crs.to_authority()
    if auth is not None:
        name = f"{auth[0]}:{auth[1]}"
    return name
