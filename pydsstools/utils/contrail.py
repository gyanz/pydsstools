import logging
import sys
from datetime import datetime
import urllib2
from xml.etree import ElementTree
import xml.etree.ElementTree as etree
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer,HecTime

__all__ = ['contrail2dss', 'get_contrail_timeseries']

headers ={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

CONTRAIL_SYSTEM_KEY = None 

CONTRAIL_URL = r'http://cs-017-exchange.onerain.com:8080/OneRain'

CONTRAIL_SENSOR_CLASSES = {10 : 'Rain Increment (in)',
                           11 : 'Rain Accumulation (in)',
                           20 : 'Stage (ft)',
                           25 : 'Flow Volume (cfs)',
                           40 : 'Wind Velocity (mph)',
                           44 : 'Wind Direction (degN)',
                           50 : 'Relative humidity (%)',
                           51 : 'Soil Moisture (%)',
                           53 : 'Barometric Pressure (mBar)',
                           84 : 'Evapotranspiration Rate (mm/hr)'
                          }

__url_date_format = '%Y-%m-%d %H:%M:%S'

__url_space_filler = '%20'

__response_data_tag = 'row'

__response_error_tag = 'error'

def contrail2dss(**kwargs):
    """Copy irregular time-series data from Contrail Data Exchange to dss file

    Parameter
    ---------
        output: string or HecDss.Open object
            destination dss file path or object

        site_id: string
            OneRain site id of gage

        sensor_class: integer
            integer value representing type of sensor such as rainfall, stage, flow, soil moisture, etc.

        sdate: string or datetime object
            start date of the data

        edate: string or datetime object
            end date of the data

    Returns
    -------
        None

    Usage
    -----
        >>> from pydsstools.utils import set_systemkey, contrail2dss
        >>> set_systemkey('Valid System Key obtained from OneRain')
        >>> contrail2dss(output='dss_out.dss',site_id=200,sensor_class=10,sdate='2000-01-01')

    """

    output = kwargs['output']
    site_id = kwargs['site_id']
    sensor_class = kwargs['sensor_class']
    close_dss = False
    if isinstance(output,HecDss.Open):
        fidout = output
    else:
        if not output[-4::].lower() != ".dss":
            output = output + ".dss"
        fidout = HecDss.Open(output)
        close_dss = True
    
    apart = kwargs.get('apart','')
    bpart = kwargs.get('bpart','')
    cpart = ' '.join(CONTRAIL_SENSOR_CLASSES[sensor_class].split()[0:-1])
    dpart = kwargs.get('dpart','')
    epart = 'IR-MONTH'
    fpart = 'OneRain Site ID %s'%(site_id)
    pathname = '/%s/%s/%s/%s/%s/%s/'%(apart,bpart,cpart,dpart,epart,fpart)

    unit = CONTRAIL_SENSOR_CLASSES[sensor_class].split()[-1][1:-1] 
    data_type = 'INST'
    if sensor_class == 11:
        data_type = 'PER-CUM'

    try: 
        fidout.deletePathname(pathname) 
        tsc = TimeSeriesContainer()
        tsc.pathname = pathname
        tsc.type = data_type
        tsc.units = unit
        tsc.interval = -1
        time_values = get_contrail_timeseries(**kwargs) 
        if not time_values[0]:
            logging.warn('Empty data retrieved from Contrail')
            return
        times = [HecTime(x).python_datetime for x in time_values[0]]
        tsc.times = times
        tsc.values = time_values[1]
        tsc.numberValues = len(tsc.times)
        fidout.put_ts(tsc)

    except Exception as e:
        raise e

    finally:
        if close_dss:
            fidout.close()

retrieve = contrail2dss

def set_systemkey(key):
    global CONTRAIL_SYSTEM_KEY
    CONTRAIL_SYSTEM_KEY = key

def check_systemkey(key):
    if CONTRAIL_SYSTEM_KEY is None:
        raise ContrailServerException(value = None, msg = 'Required Contrail Data Exchange System Key not provided. The key can be purchaged from OnRain. Use set_systemkey(key) function to assign the Key.')

class ContrailServerException(Exception):
    def __init__(self,value,msg):
        self.value = value
        self.msg = msg
    def __str__(self):
        return '\n'.join(self.msg)

def get_sensor_id(or_site_id,sensor_class):
    check_systemkey()
    url = ('%s/DataAPI?method=%s&or_site_id=%s&'
          'class=%d&' 
          'system_key=%s&concise=%s'
          )%(CONTRAIL_URL,'GetSensorData',
             or_site_id,sensor_class,
             CONTRAIL_SYSTEM_KEY,'false')

    sensor_id = None
    try:
        req = urllib2.Request(url,None,headers=headers)
        res = urllib2.urlopen(req)
        if not res is None:
            xml_content = res.read()
            tree = etree.ElementTree(etree.fromstring(xml_content))
            root = tree.getroot()
            for sen_id in  root.getiterator('or_sensor_id'):
                sensor_id = sen_id.text
    except:
        logging.error('Error retrieving or_sensor_id',exc_info=True)

    return sensor_id

def get_contrail_timeseries(**kwargs):
    """
    Parameter
    ---------
        site_id: string
            OneRain site id of gage

        sensor_class: integer
            integer value representing type of sensor such as rainfall, stage, flow, soil moisture, etc.

        sdate: string or datetime object
            start date of the data

        edate: string or datetime object
            end date of the data

    Returns
    -------
        times, values tuples

    """
    site_id = kwargs['site_id']
    sensor_class = kwargs['sensor_class']
    sdate = HecTime(kwargs['sdate']) 
    edate = HecTime(kwargs.get('edate',datetime.now().date()))
    timezone = kwargs.get('timezone','UTC')
    tag = kwargs.get('data_tag',__response_data_tag)
    error_tag = kwargs.get('error_tag',__response_error_tag)
    url = _contrail_timeseries_url(site_id,sensor_class,sdate,edate,timezone) 

    res = _contrail_timeseries_resource(url) 
    if not res is None:
        xml_content = res.read()
        tree = etree.ElementTree(etree.fromstring(xml_content))
        root = tree.getroot()
        
        error = []
        for err in root.getiterator(error_tag):
            error.append(err.text)
        if error:
            raise ContrailServerException('Error with Contrail Data Retrieval',error)
        times = []
        values = []
            
        for row in root.getiterator(tag):
            data = row.text.strip().split(',')
            date_time = datetime.strptime(data[2],date_format)
            try:
                value = float(data[4])
            except:
                value = UNDEFINED
            times.append(date_time)
            values.append(value)
        logging.debug('times=%r,values=%r'%(times,values))
        return times,values

def _contrail_timeseries_url(site_id,sensor_class,sdate,edate,timezone):
    sdate_string = sdate.strftime(__url_date_format)
    edate_string = edate.strftime(__url_date_format)
    sensor_id = get_sensor_id(site_id,sensor_class) 
    if sensor_id is None:
        logging.error('Invalid sensor id return for provided site_id and sensor class','')
        return
    url = ('%s/DataAPI?method=%s&or_site_id=%s&or_sensor_id=%s&'
          'data_start=%s&data_end=%s&tz=%s&system_key=%s&concise=%s'
          )%(CONTRAIL_URL,'GetSensorData',site_id,sensor_id,
             sdate_string,edate_string,timezone,CONTRAIL_SYSTEM_KEY,'true')    
    logging.debug(('site id=%s, sensor id=%s, start date=%r, end date=%r, timezone=%s'
                  )%(site_id,sensor_id,sdate,edate,timezone))
    return url.replace(' ', __url_space_filler)

def _contrail_timeseries_resource(url):
    try:
        req = urllib2.Request(url,None,headers=headers)
    except:
        logging.error('Error with Contrail Server Request',exc_info=True)
    else:
        try:
            resource = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            logging.error('HTTPError!',exc_info=True) 
            
        except:
            logging.error('Error with url open command!',exc_info=True)
        else:
            return resource
    return None

