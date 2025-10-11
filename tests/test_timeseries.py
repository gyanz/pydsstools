import os
from pathlib import Path
import pytest
from datetime import datetime as dt
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer, UNDEFINED

DATA = Path(__file__).parent / "data"

@pytest.fixture
def fidA():
    fid = HecDss.Open(os.path.join(DATA,"sampleA.dss"),mode="r")
    return fid

@pytest.fixture
def fidC():
    fid = HecDss.Open(os.path.join(DATA,"sampleC.dss"),mode="rw")
    return fid

def test_read_reg_timeseries(fidA):
    print(fidA.filename)
    pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR//"
    start_date = "15JUL2019 2300"
    end_date = "16JUL2019 0100"
    ex_times = [
        dt.strptime("15Jul2019 23:00","%d%b%Y %H:%M"),
        dt.strptime("16Jul2019 00:00","%d%b%Y %H:%M"),
        dt.strptime("16Jul2019 01:00","%d%b%Y %H:%M"),
    ]
    ex_flows = [10000,24.1,25]
    ts = fidA.read_ts(pathname, window=(start_date,end_date))
    times = [x.datetime() for x in ts.times]
    flows = ts.values.tolist()
    assert flows == pytest.approx(ex_flows,rel=1e-3,abs=1e-4)
    assert times == ex_times               

def test_write_reg_timeseries(fidC):
    pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/Write/"
    count = 4
    interval = 1
    tsc = TimeSeriesContainer(pathname,count,interval)
    tsc.start_time = "01JAN2025 23:00"
    tsc.data_units = "cfs"
    tsc.data_type = "INST"
    tsc.tzid = "UTC"
    tsc.values = [10,20,UNDEFINED,40]
    fidC.put_ts(tsc)
    # Read back
    ts = fidC.read_ts(pathname,trim_missing=True)
    ex_values = [10,20,UNDEFINED,40]
    ex_times = [
        dt.strptime("01Jan2025 23:00","%d%b%Y %H:%M"),
        dt.strptime("02Jan2025 00:00","%d%b%Y %H:%M"),
        dt.strptime("02Jan2025 01:00","%d%b%Y %H:%M"),
        dt.strptime("02Jan2025 02:00","%d%b%Y %H:%M"),
    ]
    values =  list(ts.values)
    times = [x.datetime() for x in ts.times]
    assert values == pytest.approx(ex_values,rel=1e-3,abs=1e-4)
    assert times == ex_times

def test_read_ireg_timeseries(fidA):
    pass             