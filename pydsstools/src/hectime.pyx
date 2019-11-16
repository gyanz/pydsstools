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

cpdef int _dateToJulian(str dateString):
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
    cdef:
        char * dstr = dateString
        int result
    result = dateToJulian(dstr)
    return result

cpdef str _julianToDate(int days, int fmt=4):
    cdef:
        char cdate[13]
        int sizeDateString = sizeof(cdate)
        int status

    status = julianToDate(days,fmt,cdate,sizeDateString)
    return cdate


cpdef tuple _getDateAndTime(int timeMinOrSec, int timeGranularitySeconds, int julianBaseDate = 0):
    cdef:
        #char *dstr = dateString
        #char *hhmm = hoursMins
        char cdate[13]
        char ctime[10]
        int sizeDateString = sizeof(cdate)
        int sizeHoursMins = sizeof(ctime)
        int status

    status = getDateAndTime(timeMinOrSec, timeGranularitySeconds, julianBaseDate, 
                            cdate, sizeDateString, ctime, sizeHoursMins)
    if not status == STATUS_OK:
        return ('','')
    return (cdate,ctime)

cpdef int _datetimeToSeconds(char *datetimeString):
    cdef:
        int julian[1]
        int seconds[1]
        int total_seconds

    julian[:] = [0]
    seconds[:] = [0]
    spatialDateTime(datetimeString, julian, seconds)
    total_seconds = julian[0] * 24 *3600 + seconds[0]
    return total_seconds

cpdef tuple _datetimeToSeconds2(char *datetimeString):
    cdef:
        int julian[1]
        int seconds[1]
        int total_seconds

    julian[:] = [0]
    seconds[:] = [0]
    spatialDateTime(datetimeString, julian, seconds)
    return (julian,seconds)

cdef int _yearMonthDayToJulian(int year, int month, int day):
    cdef int julian_days 
    julian_days = yearMonthDayToJulian(year,month,day)
    return julian_days


def getDateTimeStringTuple(dateValue,granularity=60,julianBaseDate=0):
    """
    Returns:
        Tuple consisting of date and time string (unicode strings)
        date string format: 03Jan1969
        time string format: 11:20:00 (second granularity) or 
                            1120 (minute granularity)

    Notes:
        #granularity value limited to:
            # 1 (SECOND_GRANULARITY)
            # 0 or 60 (MINUTE_GRANULARITY) DEFAULT 
        # what about hour and day granularity????
    """

    if not isinstance(dateValue,int):
        return
    
    datestr,timestr = _getDateAndTime(dateValue,granularity,julianBaseDate)

    return (datestr,timestr)

def getPyDateTimeFromString(dateString):
    # Returns python datetime object from string
    try:
        datetime_obj = parser.parse(dateString)
        return datetime_obj
    except:
        _,msg,_ = sys.exc_info()
        if "hour must be in 0..23" in str(msg):
            _datetime = dateString.split()
            _time=_datetime[-1].replace("24","23",1)
            _date=dateString[0:len(dateString)-len(_time)]
            dateString = _date+_time
            try:
                datetime_obj = parser.parse(dateString)
                datetime_obj = datetime_obj + timedelta(hours=1)
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


def getPyDateTimeFromValue(dateValue,granularity=60,julianBaseDate=0):
    tup = getDateTimeStringTuple(dateValue,granularity,julianBaseDate)
    if tup[0]:
        datetimestr = tup[0] + " " + tup[1]
        datetime_obj = getPyDateTimeFromString(datetimestr)
        return datetime_obj


def getDateTimeValueTuple(dateValue,granularity=60,julianBaseDate=0):
    """
    Returns:
        Tuples of following type - 
            YYYY,MM,DD,HH,MM,SS for 1 second granularity
            YYYY,MM,DD,HH,MM for 60 second granularity

    """
    datestr,timestr = getDateTimeStringTuple(dateValue,granularity,julianBaseDate)
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
    # 2. granularity
    # 3. python_datetime
    def __init__(self,datetimeString,granularity=60,julianBaseDate=0):
        if isinstance(julianBaseDate,str):
            julianBaseDate = _dateToJulian(julianBaseDate)
        self.julianBaseDate = julianBaseDate
        self._granularity=granularity
        val,pydate = self.parse_datetime_string(datetimeString,granularity,self.julianBaseDate) 
        # _parse_datetime adds following attributes
        self._datetimeValue = val 
        self._python_datetime=pydate    

    @property
    def granularity(self):
        return self._granularity

    @property
    def datetimeValue(self):
        return self._datetimeValue

    @property
    def python_datetime(self):
        return self._python_datetime

    def __repr__(self):
        return self.__class__.__name__ + "("+ self.formatDate()+")"

    def formatDate(self,format = "%d%b%Y %H:%M:%S"):
        return  self.python_datetime.strftime(format) 

    def dateString(self):
        # granularity based best date string
        return  self.python_datetime.strftime("%d%b%Y") 

    def timeString(self):
        # granularity based best time string
        return  self.python_datetime.strftime("%H:%M:%S") 
        '''
        if self.granularity == 1:
            return  self.python_datetime.strftime("%H:%M:%S") 
        elif self.granularity ==60:
            return  self.python_datetime.strftime("%H%M") 
        else:
            return None
        '''
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
        new_instance = __class__(new_datetimeString,self.granularity)
        self._datetimeValue = new_instance.datetimeValue
        self._python_datetime = _new_date
        return self

    def clone(self):
        return __class__(self.formatDate(),self.granularity)

    @classmethod
    def getHecTimeFromPyDateTime(cls,pydate,granularity=60,julianBaseDate=0):
        return cls(pydate,granularity,julianBaseDate)

    @staticmethod
    def parse_datetime_string(datetimeString,granularity=60,julianBaseDate=0):
        cdef:
            int datetimeval
        if granularity == 0:
            granularity = 60
            logging.debug('Granularity of 0 interpreted as minute')

        if not granularity in [1,60,3600,86400]:
            raise GranularityException(granularity,'Time granularity can only be 1 (1 second), 60 (1 minute), 3600 (1 hour) or 86400 (1 day)')

        if isinstance(datetimeString,datetime):
            pydate = datetimeString
        else:
            pydate = getPyDateTimeFromString(datetimeString)
        parsed_date = (pydate.year,pydate.month,pydate.day,
                       pydate.hour,pydate.minute,pydate.second)

        yy,mm,dd = parsed_date[0:3]
        jul_days = _yearMonthDayToJulian(yy,mm,dd)
    
        time_val = (jul_days*24*3600*1.0 + parsed_date[3]*3600*1.0 + parsed_date[4]*60*1.0)/granularity 
        base_val = (julianBaseDate*24*3600*1.0)/granularity

        datetimeval = int(round(time_val-base_val))

        return datetimeval, pydate    

    @staticmethod
    def getDateTimeStringTuple(dateValue,granularity=60,julianBaseDate=0):
        return getDateTimeStringTuple(dateValue,granularity,julianBaseDate)

    @staticmethod
    def getPyDateTimeFromString(dateString):
        return getPyDateTimeFromString(dateString)

    @staticmethod
    def getPyDateTimeFromValue(dateValue,granularity=60,julianBaseDate=0):
        return getPyDateTimeFromValue(dateValue,granularity,julianBaseDate)

    @staticmethod
    def getDateTimeValueTuple(dateValue,granularity=60,julianBaseDate=0):
        return getDateTimeValueTuple(dateValue,granularity,julianBaseDate)

    @staticmethod
    def getJulianDaysFromDate(str dateString):
        cdef:
            int days
        days = _dateToJulian(dateString)
        if not days == UNDEFINED_TIME:
            return days

    @staticmethod
    def getDateFromJulianDays(days,fmt=4):
        return _julianToDate(days, fmt)

