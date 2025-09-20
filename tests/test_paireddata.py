import os
from pathlib import Path
import pytest
from datetime import datetime as dt
from pydsstools.heclib.dss import HecDss

DATA = Path(__file__).parent / "data"

@pytest.fixture
def fidA():
    fid = HecDss.Open(os.path.join(DATA,"sampleA.dss"))
    return fid

@pytest.fixture
def fidB():
    fid = HecDss.Open(os.path.join(DATA,"sampleB.dss"))
    return fid


def test_read_paireddata(fidA):
    pathname = r"/PAIREDDATA/COWLITZ/FREQ-FLOW////"
    ex_indx = [0.95,0.80,0.60,0.50,0.40,0.30,0.20,0.10,0.05,0.02,0.01,0.005,0.002,0.001]
    ex_cur1 = [30,40,54,60,70,80,82,86,100,105,110,150,200,500]
    ex_cols = ['PROB','LOG']
    df = fidA.read_pd(pathname,dataframe=True)
    indx = df[ex_cols[0]].values.tolist()
    cur1 = df[ex_cols[1]].values.tolist()
    assert indx == pytest.approx(ex_indx)
    assert cur1 == pytest.approx(ex_cur1)

def test_write_paireddata(fidA):
    pathname = r"/PAIREDDATA/TEST/FREQ-FLOW///WRITE1/"

def _test_prealloc_paireddata(fidA):
    pathname = r"/PAIREDDATA/TEST/FREQ-FLOW///WRITE2/"
    rows = 10
    cols = 5
    label_len = 31
    fidA.preallocate_pd((rows,cols),pathname=pathname,label_size = label_len)
    pinfo = fidA.pd_info(pathname)
    assert len(pinfo.labels[0]) == label_len