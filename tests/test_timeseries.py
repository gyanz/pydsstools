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
    pathname = "/IRREGULAR/TIMESERIES/PARAM//IR-Decade//"
    ex_times = [
        dt.strptime("01Jan2019 02:01","%d%b%Y %H:%M"),
        dt.strptime("01Jan5000 01:02","%d%b%Y %H:%M"),
    ]
    ex_flows = [2019,5000]
    ts = fidA.read_ts(pathname)
    times = [x.datetime() for x in ts.times]
    flows = ts.values.tolist()
    assert flows == pytest.approx(ex_flows,rel=1e-3,abs=1e-4)
    assert times == ex_times               

def test_write_ireg_timeseries(fidC):
    from pydsstools.core import HecTime
    pathname = r"/A/B/C//IR-DAY/Write/"
    julian_base = "01JAN2000"
    times =  ["02JUL2010 1200", "05JAN2012 0000", "15MAR2014 0200", "25FEB2018 0500", "19DEC2024 1200"]
    values = [1,20,30,40,50]
    data_units = "ft"
    data_type = "INST"
    tzid = "UTC"
    fidC.put_ts(pathname,values=values,times=times,julian_base=julian_base,data_units=data_units,data_type=data_type,tzid=tzid)
    # Read back
    ts = fidC.read_ts(pathname,regular=False)
    ex_values = values
    ex_times = [HecTime(x).datetime() for x in times]
    values =  list(ts.values)
    times = [x.datetime() for x in ts.times]
    assert values == pytest.approx(ex_values,rel=1e-3,abs=1e-4)
    assert times == ex_times
