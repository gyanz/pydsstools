'''
Setting Dss Messaging/Logging level
'''
import logging
import sys
from pydsstools.heclib.dss.HecDss import Open


dss_file = "example.dss"
pathname = "/REGULAR/TIMESERIES/FLOW//1HOUR/Ex1/"


with Open(dss_file) as fid:
    logging.info('DSS Logging is DEFAULT')
    ts = fid.read_ts(pathname)


with Open(dss_file,logging_level = 'Debug') as fid:
    logging.info('DSS Logging is DEBUG')
    ts = fid.read_ts(pathname)

with Open(dss_file,logging_level = 'Diagnostic') as fid:
    logging.info('DSS Logging is DEBUG')
    ts = fid.read_ts(pathname)
