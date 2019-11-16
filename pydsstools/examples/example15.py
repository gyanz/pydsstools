'''
Setting Dss Messaging/Logging level
'''
import logging
logging.basicConfig(level = logging.DEBUG)
import sys
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.heclib.utils import dss_logging

dss_logging.config(level='General')


dss_file = "example.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/Ex1/"


with Open(dss_file) as fid:
    logging.info('Reading timeseries')
    ts = fid.read_ts(pathname)

