"""
Tests for writing and reading time-series with location metadata in DSS-7 files.

DSS-7 stores location in a separate record at /A/B/Location Info////,
written via zlocationStore and read via zlocationRetrieve.  The write path
uses the standard two-call sequence: ztsStore for TS data, then zlocationStore
for location.  This is handled transparently by put_ts(tsc, location=loc).
"""
import pytest
from datetime import datetime as dt
from pathlib import Path

from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer, UNDEFINED
from pydsstools.core.location import LocationInfo
from pydsstools.core.enums import (
    LocCoordSystem,
    LocHorizUnits,
    LocHorizDatum,
    LocVertUnits,
    LocVertDatum,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dss7_file(tmp_path):
    """Yield an open read-write DSS-7 file; close on teardown."""
    path = str(tmp_path / "test_loc_v7.dss")
    fid = HecDss.Open(path, version=7, mode="rw")
    yield fid
    fid.close()


# ---------------------------------------------------------------------------
# Regular time series
# ---------------------------------------------------------------------------

REG_PATHNAME = "/SITE/GAUGE/FLOW//1HOUR/DSS7TEST/"
REG_VALUES   = [100.0, 200.0, 300.0, 400.0]
REG_START    = "01JAN2020 0100"
REG_TIMES_EXPECTED = [
    dt.strptime("01Jan2020 01:00", "%d%b%Y %H:%M"),
    dt.strptime("01Jan2020 02:00", "%d%b%Y %H:%M"),
    dt.strptime("01Jan2020 03:00", "%d%b%Y %H:%M"),
    dt.strptime("01Jan2020 04:00", "%d%b%Y %H:%M"),
]

REG_LOC = LocationInfo(
    pathname=REG_PATHNAME,
    x=-83.47891,
    y=35.72596,
    z=250.5,
    coordinate_system=LocCoordSystem.lat_long,
    coordinate_id=0,
    horizontal_units=LocHorizUnits.decimal_degrees,
    horizontal_datum=LocHorizDatum.wgs84,
    vertical_units=LocVertUnits.meters,
    vertical_datum=LocVertDatum.navd88,
    time_zone="UTC",
    supplemental=["source:stream_gauge", "agency:USGS"],
)


def test_write_read_reg_ts_with_location(dss7_file):
    """Write regular TS + location to DSS-7; read back and verify all fields."""
    fid = dss7_file
    assert fid.version == 7, "Expected a DSS-7 file"

    # --- Write ---
    tsc = TimeSeriesContainer(REG_PATHNAME, len(REG_VALUES), interval=1)
    tsc.start_time = REG_START
    tsc.data_units = "cfs"
    tsc.data_type  = "INST-VAL"
    tsc.tzid       = "UTC"
    tsc.values     = REG_VALUES
    fid.put_ts(tsc, location=REG_LOC)

    # --- Read back ---
    tss, loc = fid.read_ts(REG_PATHNAME, location=True, trim_missing=True)
    assert loc is not None, "Location should be present after write"

    # Values
    assert list(tss.values) == pytest.approx(REG_VALUES, rel=1e-3, abs=1e-4)

    # Times
    assert [t.datetime() for t in tss.times] == REG_TIMES_EXPECTED

    # Coordinates
    assert loc.x == pytest.approx(REG_LOC.x, abs=1e-6)
    assert loc.y == pytest.approx(REG_LOC.y, abs=1e-6)
    assert loc.z == pytest.approx(REG_LOC.z, abs=1e-6)

    # Coordinate descriptor enums
    assert loc.coordinate_system == REG_LOC.coordinate_system
    assert loc.coordinate_id     == REG_LOC.coordinate_id
    assert loc.horizontal_units  == REG_LOC.horizontal_units
    assert loc.horizontal_datum  == REG_LOC.horizontal_datum
    assert loc.vertical_units    == REG_LOC.vertical_units
    assert loc.vertical_datum    == REG_LOC.vertical_datum

    # Timezone
    assert loc.time_zone == REG_LOC.time_zone

    # Supplemental lines
    assert loc.supplemental == REG_LOC.supplemental


# ---------------------------------------------------------------------------
# Irregular time series
# ---------------------------------------------------------------------------

IREG_PATHNAME  = "/SITE/GAUGE/STAGE//IR-YEAR/DSS7TEST/"
IREG_TIMES_STR = ["01JAN2020 1200", "01JAN2021 1200", "01JAN2022 1200"]
IREG_VALUES    = [10.5, 11.2, 9.8]
IREG_BASE      = "01JAN2000"

IREG_LOC = LocationInfo(
    pathname=IREG_PATHNAME,
    x=-118.24368,
    y=34.05223,
    z=71.0,
    coordinate_system=LocCoordSystem.lat_long,
    coordinate_id=0,
    horizontal_units=LocHorizUnits.decimal_degrees,
    horizontal_datum=LocHorizDatum.nad83,
    vertical_units=LocVertUnits.feet,
    vertical_datum=LocVertDatum.navd88,
    time_zone="PST",
    supplemental=["source:lake_gauge"],
)


def test_write_read_ireg_ts_with_location(dss7_file):
    """Write irregular TS + location to DSS-7; read back and verify all fields."""
    from pydsstools.core import HecTime

    fid = dss7_file
    assert fid.version == 7, "Expected a DSS-7 file"

    # --- Write ---
    fid.put_ts(
        IREG_PATHNAME,
        values=IREG_VALUES,
        times=IREG_TIMES_STR,
        julian_base=IREG_BASE,
        data_units="ft",
        data_type="INST-VAL",
        tzid="PST",
        location=IREG_LOC,
    )

    # --- Read back ---
    tss, loc = fid.read_ts(IREG_PATHNAME, location=True)
    assert loc is not None, "Location should be present after write"

    # Values
    assert list(tss.values) == pytest.approx(IREG_VALUES, rel=1e-3, abs=1e-4)

    # Times
    expected_times = [HecTime(t).datetime() for t in IREG_TIMES_STR]
    assert [t.datetime() for t in tss.times] == expected_times

    # Coordinates
    assert loc.x == pytest.approx(IREG_LOC.x, abs=1e-6)
    assert loc.y == pytest.approx(IREG_LOC.y, abs=1e-6)
    assert loc.z == pytest.approx(IREG_LOC.z, abs=1e-6)

    # Coordinate descriptor enums
    assert loc.coordinate_system == IREG_LOC.coordinate_system
    assert loc.coordinate_id     == IREG_LOC.coordinate_id
    assert loc.horizontal_units  == IREG_LOC.horizontal_units
    assert loc.horizontal_datum  == IREG_LOC.horizontal_datum
    assert loc.vertical_units    == IREG_LOC.vertical_units
    assert loc.vertical_datum    == IREG_LOC.vertical_datum

    # Timezone
    assert loc.time_zone == IREG_LOC.time_zone

    # Supplemental
    assert loc.supplemental == IREG_LOC.supplemental


# ---------------------------------------------------------------------------
# Standalone _put_location on DSS-7 should work (unlike DSS-6)
# ---------------------------------------------------------------------------

def test_put_location_standalone_dss7_works(dss7_file):
    """In DSS-7, _put_location can be called independently after _put."""
    fid = dss7_file
    assert fid.version == 7, "Expected a DSS-7 file"

    # Write TS first (no location)
    tsc = TimeSeriesContainer(REG_PATHNAME, len(REG_VALUES), interval=1)
    tsc.start_time = REG_START
    tsc.data_units = "cfs"
    tsc.data_type  = "INST-VAL"
    tsc.values     = REG_VALUES
    fid.put_ts(tsc)

    # Then write location separately
    fid._put_location(REG_LOC)

    # Read back and verify location was stored
    _, loc = fid.read_ts(REG_PATHNAME, location=True)
    assert loc is not None
    assert loc.x == pytest.approx(REG_LOC.x, abs=1e-6)
    assert loc.y == pytest.approx(REG_LOC.y, abs=1e-6)
    assert loc.coordinate_system == REG_LOC.coordinate_system
    assert loc.time_zone == REG_LOC.time_zone
