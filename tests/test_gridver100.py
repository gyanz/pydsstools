import os
from pathlib import Path
import pytest
import numpy as np
from pydsstools.heclib.dss import HecDss

DATA = Path(__file__).parent / "data"

@pytest.fixture
def fidA():
    fid = HecDss.Open(os.path.join(DATA,"sampleA.dss"),mode="r")
    return fid

@pytest.fixture
def fidC():
    fid = HecDss.Open(os.path.join(DATA,"sampleC.dss"),mode="rw")
    return fid

def test_read_hrap(fidA):
    pathname = "/HRAP/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/ZLIB-VER100"
    exp_info = {"grid_type":410,
                "data_units":"mm",
                "data_type":1,
                "lower_left_cell":(901,568),
                "shape":(44,45),
                "cell_size":4762.5,
                "compression_method":26,
                "max_val":1.9317743,
                "min_val":0.0,
                "mean_val":0.04479313,
                "range_val1":0,
                "range_val3":5.0,
                "range_count0":1980,
                "range_count1":714,
                "range_count2":214,
                "range_count3":0,
                "data_source":""}

    ds = fidA.read_grid(pathname)
    ginfo = ds.gridinfo
    range_vals = ginfo.range_vals
    range_counts = ginfo.range_counts
    
    info = {"grid_type":ginfo.grid_type,
            "data_units":ginfo.data_units,
            "data_type":ginfo.data_type,
            "lower_left_cell":ginfo.lower_left_cell,
            "shape":ginfo.shape,
            "cell_size":ginfo.cell_size,
            "compression_method":ginfo.compression_method,
            "max_val":ginfo.max_val,
            "min_val":ginfo.min_val,
            "mean_val":ginfo.mean_val,
            "range_val1":range_vals[1],
            "range_val3":range_vals[3],
            "range_count0":range_counts[0],
            "range_count1":range_counts[1],
            "range_count2":range_counts[2],
            "range_count3":range_counts[3],
            "data_source":ginfo.data_source}
    
    for k,exp_v in exp_info.items():
        v = info[k]
        assert v == pytest.approx(exp_v), "Mismatch at key:{k}, value:{v} | expected:{exp_v}"


def test_read_albers(fidA):
    pathname = "/SHG/BALDEAGLE/PRECIP/23JUL2003:0000/23JUL2003:0100/ZLIB-VER100/"
    exp_info = {"grid_type":420,
                "data_units":"mm",
                "data_type":1,
                "lower_left_cell":(741,1055),
                "shape":(41,31),
                "cell_size":2000.0,
                "compression_method":26,
                "max_val":0.07,
                "min_val":0.0,
                "mean_val":7.0097606e-4,
                "range_val1":0,
                "range_val3":1.0,
                "range_count0":1127,
                "range_count1":1127,
                "range_count2":16,
                "range_count3":0,
                "proj_datum":2,
                }

    ds = fidA.read_grid(pathname)
    ginfo = ds.gridinfo
    range_vals = ginfo.range_vals
    range_counts = ginfo.range_counts
    
    info = {"grid_type":ginfo.grid_type,
            "data_units":ginfo.data_units,
            "data_type":ginfo.data_type,
            "lower_left_cell":ginfo.lower_left_cell,
            "shape":ginfo.shape,
            "cell_size":ginfo.cell_size,
            "compression_method":ginfo.compression_method,
            "max_val":ginfo.max_val,
            "min_val":ginfo.min_val,
            "mean_val":ginfo.mean_val,
            "range_val1":range_vals[1],
            "range_val3":range_vals[3],
            "range_count0":range_counts[0],
            "range_count1":range_counts[1],
            "range_count2":range_counts[2],
            "range_count3":range_counts[3],
            "proj_datum":ginfo.proj_datum}
    
    for k,exp_v in exp_info.items():
        v = info[k]
        assert v == pytest.approx(exp_v), "Mismatch at key:{k}, value:{v} | expected:{exp_v}"

def test_read_spec(fidA):
    pathname = "/UTM_18N/MARFC/PRECIP/23JUL2003:0000/23JUL2003:0100/ZLIB-VER100/"
    exp_info = {"grid_type":430,
                "data_units":"mm",
                "data_type":1,
                "lower_left_cell":(0,0),
                "shape":(133,144),
                "cell_size":1000.0,
                "compression_method":26,
                "max_val":1.9530661,
                "min_val":0.0,
                "mean_val":0.043972425,
                "range_val1":0,
                "range_val3":5.0,
                "range_count0":19152,
                "range_count1":12752,
                "range_count2":3875,
                "range_count3":0,
                "nodata":-3.4028235e38,
                "coords_cell0":(200500.0,4473500.0),
                "crs_name":"METVUEGEN",
                "tzid":"UTC",
                "tzoffset":0,
                "is_interval":True,
                "time_stamped":True
                }

    ds = fidA.read_grid(pathname)
    ginfo = ds.gridinfo
    range_vals = ginfo.range_vals
    range_counts = ginfo.range_counts
    
    info = {"grid_type":ginfo.grid_type,
            "data_units":ginfo.data_units,
            "data_type":ginfo.data_type,
            "lower_left_cell":ginfo.lower_left_cell,
            "shape":ginfo.shape,
            "cell_size":ginfo.cell_size,
            "compression_method":ginfo.compression_method,
            "max_val":ginfo.max_val,
            "min_val":ginfo.min_val,
            "mean_val":ginfo.mean_val,
            "range_val1":range_vals[1],
            "range_val3":range_vals[3],
            "range_count0":range_counts[0],
            "range_count1":range_counts[1],
            "range_count2":range_counts[2],
            "range_count3":range_counts[3],
            "nodata":ginfo.nodata,
            "coords_cell0":ginfo.coords_cell0,
            "crs_name":ginfo.crs_name,
            "tzid":ginfo.tzid,
            "tzoffset":ginfo.tzoffset,
            "is_interval":ginfo.is_interval,
            "time_stamped":ginfo.time_stamped
            
            }
    
    for k,exp_v in exp_info.items():
        v = info[k]
        assert v == pytest.approx(exp_v), "Mismatch at key:{k}, value:{v} | expected:{exp_v}"