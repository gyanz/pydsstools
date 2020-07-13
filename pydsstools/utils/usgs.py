import logging
import urllib.request as urllib2
import json
from datetime import datetime
from pydsstools.heclib.utils import HecTime
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer,DssPathName

__all__ = ['gage2dss']

headers ={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','pragma-directive': 'no-cache'}

NWIS_URL = r"https://waterservices.usgs.gov/nwis/dv/?site=%s&startDT=%s&endDT=%s&variable=%s&format=json,1.1"

PARAM_ALLOWED = {'flow': '00060', 'stage': '00065'}

def gage2dss(output, site, param='flow', sdate='1700-01-01', edate=''): 
    """Copy usgs flow or stage regular time-series data to dss file 

    Parameter
    ---------
        output: string or HecDss.Open object
            destination dss file path or object

        site: string, list or dict
            usgs gage id or list of ids or dictionary with key as description and value as gage id

        param: string
            flow or stage

        sdate: string or datetime object
            start date of the data

        edate: string or datetime object
            end date of the data

    Returns
    -------
        None

    Usage
    -----
        >>> gage2dss('dss_out.dss','08354900','flow','2000-01-01')

    """
    if isinstance(site,(int,str)):
        site_alias = [str(site)]
        site_codes = [str(site)]
    elif isinstance(site,dict):
        site_alias = list(site.keys())
        site_code = list(site.values())
    elif isinstance(site,(list,tuple)):
        site_alias = [str(x) for x in site]
        site_code = [str(x) for x in site]
    else:
        logging.error('Incorrect site argument value',exc_info = True)

    _param = PARAM_ALLOWED.get(param.lower(),None)
    if _param is None:
        logging.error('Incorrect param argument value (%r). It mus be one of %r',param,PARAM_ALLOWED.keys(),exc_info = True)

    close_dss = False
    if isinstance(output,HecDss.Open):
        fidout = output
    else:
        fidout = HecDss.Open(output)
        close_dss = True

    if not edate:
        edate = datetime.now().date().strftime('%Y-%m-%d')

    try:
        for alias,siteid in zip(site_alias,site_code):
            url = NWIS_URL%(siteid,sdate,edate,_param)
            logging.debug('url=%s',url)
            req = urllib2.Request(url,None,headers=headers)
            res = urllib2.urlopen(req)
            data = res.read()
            jdata = json.loads(data)
            if not jdata['value']['timeSeries']: 
                logging.warning('No data for gage %s',siteid)
            else:
                ts = jdata['value']['timeSeries'][0]['values'][0]['value']
                if not ts:
                    logging.warning('No data for gage %s',siteid)
                else:
                    site = jdata['value']['timeSeries'][0]['sourceInfo']['siteName'] 
                    param_desc = (jdata['value']['timeSeries'][0]['variable']['variableDescription']).split(',')[0] 
                    unit = jdata['value']['timeSeries'][0]['variable']['unit']['unitCode'] 
                    logging.debug('Data param description is %s',param_desc)
                    logging.debug('Data unit is %s',unit)
                    nodata = ''
                    try:
                        nodata = jdata['value']['timeSeries'][0]['variable']['noDataValue'] 
                    except:
                        pass

                    # Determine time-series interval from first 10 data
                    dates = []
                    for row in ts[0:10]:
                        datestr = row['dateTime'].replace('T',' ')
                        ptime = HecTime(datestr).python_datetime
                        dates.append(ptime)
                    date_diff = [y-x for y,x in zip(dates[1:],dates[0:-1])]
                    logging.debug('date_diff = %r', date_diff)
                    date_diff = [x.total_seconds()/(60.0*60.0) for x in date_diff]
                    period = min(date_diff)
                    logging.debug('Data interval = %r hour',period)
                    
                    interval = '1DAY'
                    if period < 24:
                        interval = '1HOUR'
                    
                    # Write to dss file
                    apart = '' 
                    if alias != siteid:
                        apart = alias
                    bpart = site
                    cpart = param.upper()
                    dpart = ''
                    epart = interval
                    fpart = 'USGS ' + str(siteid) 
                    pathname = '/%s/%s/%s/%s/%s/%s/'%(apart,bpart,cpart,dpart,epart,fpart)
                    fidout.deletePathname(pathname)
                    tsc = TimeSeriesContainer()
                    tsc.pathname = pathname
                    tsc.type = 'INST'
                    tsc.units = unit
                    tsc.interval = 1
                    tsc.numberValues = 1

                    for row in ts:
                        date = row['dateTime'].replace('T',' ')
                        flow = row['value']
                        tsc.startDateTime = date
                        tsc.values = [float(flow)]
                        fidout.put_ts(tsc)

    except Exception as e:
        loging.warning('Error occure for gage = %s',siteid)
        raise e

    finally:
        if close_dss:
            fidout.close()

retrieve = gage2dss

if __name__ == "__main__":
    usgs_gages = {'First Site':      '12359800',
                  'Second Site':     '12362500',
                  }
    gage2dss('dss_out.dss', usgs_gages,'flow')
