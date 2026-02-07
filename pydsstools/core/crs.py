import logging
from pyproj import CRS
from . import HRAP_WKT, SHG_WKT
from .enums import Datum


__all__ = ["hrap", "shg", "albers", "make_albers", "wkt_to_crs", "albers_params_from_wkt", "crs_short_name","is_equal_area_conic","is_hrap"]

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
