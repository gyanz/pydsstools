import os
from pathlib import Path
import pytest
from datetime import datetime as dt
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

def test_read_paireddata(fidA):
    pathname = r"/PAIREDDATA/COWLITZ/FREQ-FLOW////"
    ex_index = [0.95,0.80,0.60,0.50,0.40,0.30,0.20,0.10,0.05,0.02,0.01,0.005,0.002,0.001]
    ex_y0 = [30,40,54,60,70,80,82,86,100,105,110,150,200,500]
    ex_labels = ['1999']
    df = fidA.read_pd(pathname,dataframe=True)
    labels = df.columns.get_level_values('labels').tolist()
    index = df.index.tolist()
    y0 = df['y0'].values.ravel().tolist()
    assert labels == ex_labels
    assert index == pytest.approx(ex_index)
    assert y0 == pytest.approx(ex_y0)

def test_write_paireddata(fidC):
    pathname = r"/PAIREDDATA/TEST/FREQ-FLOW///WRITE1/"

def _test_prealloc_paireddata(fidC):
    pathname = r"/PAIREDDATA/TEST/FREQ-FLOW///WRITE2/"
    rows = 10
    cols = 5
    label_len = 31
    fidA.preallocate_pd((rows,cols),pathname=pathname,label_size = label_len)
    pinfo = fidA.pd_info(pathname)
    assert len(pinfo.labels[0]) == label_len