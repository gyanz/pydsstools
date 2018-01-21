"""
HEC-DSS's date and time functions
"""
import sys
import logging
from datetime import datetime,timedelta
from dateutil import parser
from ctypes import (c_char,c_char_p,c_int,POINTER,sizeof,cast)
from pydsstools import (_heclib,str2ascii)
from pydsstools.heclib.dssExceptions import GranularityException
__all__ = ["TIME_GRANULARITY_OPTIONS","TIME_GRANULARITY",
           "dateToJulian", "daysSinceJulianBaseDate","dateStringToValue","dateToDays", #all same
            "yearMonthDayToJulian",
            "datetimeToValue","datetimeStringToValue",
           "getDateTimeStringTuple","getDateTimeString",
           "getDateTimeValues", "getPyDateTimeValues" ,"HecTime"]

SECOND_GRANULARITY = 1
MINUTE_GRANULARITY = 60
HOUR_GRANULARITY = 3600
DAY_GRANULARITY = 86400

DAILY_BLOCK = 1
MONTHLY_BLOCK = 2
YEARLY_BLOCK = 3
DECADE_BLOCK = 4
CENTURY_BLOCK = 5

UNDEFINED_TIME = -777777
JULIAN_BASE_DATE = 693960 

TIME_GRANULARITY_OPTIONS = {
                            "SECOND_GRANULARITY":SECOND_GRANULARITY,
                            "MINUTE_GRANULARITY":MINUTE_GRANULARITY,
                            "HOUR_GRANULARITY":HOUR_GRANULARITY,
                            "DAY_GRANULARITY":DAY_GRANULARITY
                           }


TIME_GRANULARITY = {v: k for k, v in TIME_GRANULARITY_OPTIONS.items()}

MAX_DATESTRING_LENGTH = 13
MAX_TIMESTRING_LENGTH = 10


_gdateToJulian = getattr(_heclib,"gdateToJulian")
_gdateToJulian.argtypes=(c_char_p,)
_gdateToJulian.restype = c_int

_ggetDateAndTime = getattr(_heclib,"ggetDateAndTime")
_ggetDateAndTime.argtypes = (c_int,c_int,c_int,c_char*MAX_DATESTRING_LENGTH,
                            c_int,c_char*MAX_TIMESTRING_LENGTH,
                            c_int)

_gyearMonthDayToJulian = getattr(_heclib,"gyearMonthDayToJulian")
_gyearMonthDayToJulian.argtypes=(c_int,c_int,c_int)
_gyearMonthDayToJulian.restype = c_int


SHORT_MONTH_NAMES = {"Jan":1,
                    "Feb":2,
                    "Mar":3,
                    "Apr":4,
                    "May":5,
                    "Jun":6,
                    "Jul":7,
                    "Aug":8,
                    "Sep":9,
                    "Oct":10,
                    "Nov":11,
                    "Dec":12}

LONG_MONTH_NAMES = {"January":1,
                    "February":2,
                    "March":3,
                    "April":4,
                    "May":5,
                    "June":6,
                    "July":7,
                    "August":8,
                    "September":9,
                    "October":10,
                    "November":11,
                    "December":12}

def dateToJulian(dateString):
    """
    Converts Date string to days since Julian base date,which is defined by HEC
    as Dec 31, 1899 (time 00:00 or beginning of day)

    Returns:
        It returns integer days since the beginning of Julian Base Date

    DateString Rules (?):
        Valid: "02JAN1969", "2JAN1969", "02 JAN 1969","02 JANUARY 1969"
        Invalid: don't use 2 digit year and don't include time in the string
    
    Examples:
         returns 10 for Jan 10, 1900
         returns 0 for "31DEC1899"
         returns 1 for "01JAN1900" 
    """
    return _gdateToJulian(str2ascii(dateString))

daysSinceJulianBaseDate = dateToJulian #Alias function, func. name provides clarity
dateStringToValue = dateToJulian
dateToDays = dateToJulian

def yearMonthDayToJulian(year,month,day):
    julian_days = _gyearMonthDayToJulian(year,month,day)
    return julian_days


def datetimeToValue(dateString):
    # Returns python datetime object from string
    try:
        datetime_obj = parser.parse(dateString)
        return datetime_obj
    except:
        _,msg,_ = sys.exc_info()
        if str(msg) == "hour must be in 0..23":
            _datetime = dateString.split()
            _time=_datetime[-1].replace("24","23",1)
            _date=dateString[0:len(dateString)-len(_time)]
            dateString = _date+_time
            try:
                datetime_obj = parser.parse(dateString)
                return datetime_obj
            except:
                pass

        datestr = dateString.lower()
        for x in list(SHORT_MONTH_NAMES.keys()):
            i=datestr.find(x.lower())
            if not i == -1:
                dateString = dateString[0:i] +" "+dateString[i::]
                return parser.parse(dateString)

        for x in list(LONG_MONTH_NAMES.keys()):
            i=datestr.find(x.lower())
            if not i == -1:
                dateString = dateString[0:i] +" "+dateString[i::]
                return parser.parse(dateString)

datetimeStringToValue = datetimeToValue

def getDateTimeStringTuple(dateValue,granularity_value=60):
    """
    Returns:
        Tuple consisting of date and time string (unicode strings)
        date string format: 03Jan1969
        time string format: 11:20:00 (second granularity) or 
                            1120 (minute granularity)

    Notes:
        #granularity value limited to:
            # 1 (SECOND_GRANULARITY)
            # 60 (MINUTE_GRANULARITY) DEFAULT 
        # what about hour and day granularity????
    """

    if not isinstance(dateValue,int):
        return
    
    if not granularity_value in [1,60]:
        print("Granularity of datetime value should be 1 or 60")
        return
    date_array = (c_char*MAX_DATESTRING_LENGTH)()
    time_array = (c_char*MAX_TIMESTRING_LENGTH)()
    status = _ggetDateAndTime(dateValue,granularity_value,0,date_array,
                              sizeof(date_array),
                              time_array,sizeof(time_array))

    datestr = str(cast(date_array,c_char_p).value,"utf-8")
    timestr = str(cast(time_array,c_char_p).value,"utf-8")

    return (datestr,timestr)

def getDateTimeString(dateValue,granularity_value=60,
                      date_style=101,time_style=1,
                      sep=" "):
    
    pass


def getDateTimeValues(dateValue,granularity_value=60):
    """
    Returns:
        Tuples of following type - 
            YYYY,MM,DD,HH,MM,SS for 1 second granularity
            YYYY,MM,DD,HH,MM for 60 second granularity

    """
    datestr,timestr = getDateTimeStringTuple(dateValue,granularity_value)
    day=int(datestr[:2])
    month = SHORT_MONTH_NAMES[datestr[2:5]]
    year = int(datestr[5::])

    try:
        hr,mm,ss = [int(x) for x in timestr.split(":")]
    except ValueError:
        hr,mm = int(timestr[0:2]),int(timestr[2:4])
        ss=0
    return (year,month,day,hr,mm,ss)


class HecTime(object):
    # Three arrtributes are important
    # 1. datetimeValue
    # 2. granularity_value
    # 3. python_datetime
    def __init__(self,datetimeString,granularity_value=60):
        self.granularity_value=granularity_value
        val,pydate = self.parse_datetime(datetimeString,granularity_value) 
        # _parse_datetime adds following attributes
        self.datetimeValue = val 
        self.python_datetime=pydate    

    def __repr__(self):
        return self.__class__.__name__ + "("+ self.formatDate()+")"

    def formatDate(self,format = "%d%b%Y %H:%M"):
        return  self.python_datetime.strftime(format) 

    def dateString(self):
        # granularity based best date string
        return  self.python_datetime.strftime("%d%b%Y") 

    def timeString(self):
        # granularity based best time string
        if self.granularity_value == 1:
            return  self.python_datetime.strftime("%H:%M:%S") 
        elif self.granularity_value ==60:
            return  self.python_datetime.strftime("%H%M") 
        else:
            return None

    @staticmethod
    def parse_datetime(datetimeString,granularity_value):
        pydate = datetimeToValue(datetimeString)
        parsed_date = (pydate.year,pydate.month,pydate.day,
                       pydate.hour,pydate.minute,pydate.second)

        jul_days = yearMonthDayToJulian(*parsed_date[0:3])
        jul_day_val = jul_days*24*3600/granularity_value 
    
        if granularity_value == 60:
            time_val = parsed_date[3]*3600/granularity_value +\
                         parsed_date[4]*60/granularity_value 

        elif granularity_value == 1:
            time_val = parsed_date[3]*3600 + \
                         parsed_date[4]*60 + \
                         parsed_date[5] 
        else:
            raise  GranularityException(granularity_value,"Time granularity is not second or minute")   

        return int(jul_day_val + time_val), pydate    

    def addTime(self,**kwargs):
        # Allowed keywords (only one of the following):
            #days
            #hours
            #minutes
            #seconds
        # value must be integer value

        if not len(kwargs) == 1:
            raise ArgumentException(" Invalid keyword arguments")
        logging.info("%r",kwargs) 
        _key,_value = list(kwargs.items())[0]
        if not isinstance(_value,int):
            raise ValueError("Argument of integer type expected!")

        if _key == "days":
            _new_date = self.python_datetime + timedelta(days=_value)
        elif _key == "hours":
            _new_date = self.python_datetime + timedelta(hours=_value)
        elif _key == "minutes":
            _new_date = self.python_datetime + timedelta(minutes=_value)
        elif _key == "seconds":
            _new_date = self.python_datetime + timedelta(seconds=_value)
        else:
            raise ArgumentException("Wrong type of argument")

        new_datetimeString = _new_date.strftime("%d %b %Y %H:%M:%S")
        new_instance = __class__(new_datetimeString,self.granularity_value)
        self.datetimeValue = new_instance.datetimeValue
        self.python_datetime = _new_date
        return self
            

    def clone(self):
        return __class__(self.formatDate(),self.granularity_value)

