
# Regex patterns for parsing datetime string

__AMPM = r'(?:[AP]\.?M\.?|[AP])'

#__ISO = re.compile(r'^\s*(?P<date>-?\d{4,}-\d{2}-\d{2})[T ](?P<time>\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?)\s*$', re.I)
__ISO = re.compile(r'^\s*(?P<date>-?\d{4,}-\d{2}-\d{2})[T ](?P<time>\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?)\s*$', re.I)

# Only treat as GRID if there's exactly one ':' in the whole string
#__GRID = re.compile(r'^\s*(?P<date>.+?)\s*:\s*(?P<time>(24(?:00|0000)|(?:[01]?\d|2[0-3])[0-5]\d(?:[0-5]\d)?))\s*[;,.]*\s*$', re.I)
__GRID = re.compile(r'^\s*(?P<date>.+?)\s*:\s*(?P<time>\d{3,4}(?:\d{2})?)\s*[;,.]*\s*$', re.I)

# Require that the time at the end is NOT immediately preceded by a digit.
# This avoids mis-parsing "...1985:01:00" as "5:01:00".
#__COLON_TIME = re.compile( rf'(?<!\d)(?P<time>(?:24:00(?::00)?|(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?)(?:\s*{__AMPM})?)\s*[;,.]*\s*$', re.I)
__COLON_TIME = re.compile(rf'(?<!\d)(?P<time>\d{{1,2}}:\d{{2}}(?::\d{{2}})?(?:\s*{__AMPM})?)\s*[;,.]*\s*$', re.I)

# Same non-digit boundary rule for plain HHMM times.
#__PLAIN_TIME = re.compile(rf'(?<!\d)(?P<time>(24(?:00|0000)|(?:[01]?\d|2[0-3])[0-5]\d(?:[0-5]\d)?)(?:\s*{__AMPM})?)\s*[;,.]*\s*$', re.I)
__PLAIN_TIME = re.compile(rf'(?<!\d)(?P<time>\d{{3,4}}(?:\d{{2}})?(?:\s*{__AMPM})?)\s*[;,.]*\s*$', re.I)

cdef class HecTime:
    """ HecTime(date_string/datetime/HecTime/None,[granularity],[midnight_as_2400],[date_style],[time_style])

    Parses the datetime and stores two attributes:
    i> julian: days since 31 DEC 1899
    ii> seconds: number of seconds which is less than or equal to 86400 (i.e., total seconds in a DAY)

    """

    cdef:
        int _julian
        int _seconds_since_midnight
        int _granularity
        bint _midnight_as_2400
        int _date_style
        int _time_style

    def __init__(self, *arg, **kwargs):
        cdef:
            str datetime_str
            str date_str, time_str
            object julian_base
            int granularity
            object jul_sec

        date_time = None
        if len(arg) != 0:
            date_time = arg[0]

        granularity = kwargs.pop("granularity",60)
        self._midnight_as_2400 = kwargs.pop("midnight_as_2400",False)
        self._date_style = kwargs.pop("date_style",2)
        self._time_style = kwargs.pop("time_style",2)

        if granularity in (1,60,3600,86400):
            self._granularity = granularity
        else:
            logging.warning(f"Expected 1, 60, 3600 or 86400 seconds for granularity but got {granularity}")    
            logging.warning("Using granularity of 60 seconds")
            self._granularity = 60    

        if date_time is None:
            self._julian = UNDEFINED_TIME
            self._seconds_since_midnight = UNDEFINED_TIME

        elif isinstance(date_time, str):
            date_str, time_str = self.split_datetime(date_time)
            # the API functions requires colon between date and time later on
            # TODO: check if API function supports AM/PM
            if not time_str.strip():
                logging.info(f"HecTime parsing of '{date_time}' returned an empty time component (date part = {date_str}); defaulting time to 0000")
                time_str = "0000"

            datetime_str = f"{date_str}:{time_str}"

        elif isinstance(date_time, datetime):
            datetime_str = date_time.strftime("%d%b%Y:%H:%M:%S")

        elif isinstance(date_time,HecTime):
            self._julian = date_time.julian()
            self._seconds_since_midnight = date_time.seconds_since_midnight()
            self._granularity = date_time.granularity()
            self._midnight_as_2400 = date_time.midnight_as_2400()
            self._date_style = date_time.date_style()
            self._time_style = date_time.time_style()
        
        elif isinstance(date_time,int):
            julian_base = kwargs.pop("julian_base",0)
            jul_sec = HecTime._value_to_julian_seconds2(date_time,granularity,julian_base)
            self._julian = jul_sec[0]
            self._seconds_since_midnight = jul_sec[1]

        else:
            raise ValueError(f"Expected datetime,string or HecTime object but received {type(date_time).__name__}")    

        if isinstance(date_time, (datetime,str)):
            try:
                jul_sec = HecTime._datetime_to_julian_seconds(datetime_str)
            except:
                raise ValueError(f"Error parsing datetime({date_time})")

            self._julian = jul_sec[0]
            #if granularity == 1:
            #    # to prevent overflow?
            #    self._julian += 25568
            self._seconds_since_midnight = jul_sec[1]

        self.set_midnight_as_2400(self._midnight_as_2400)    

    def value(self,none_as_undefined=False):
        cdef:
            int days
            int seconds
            int granularity
            int increments_in_day
            int increments_in_sec
            int value

        if self.is_undefined():
            if none_as_undefined:
                return None
            else:    
                return UNDEFINED_TIME
        days = self.julian()
        seconds = self.seconds_since_midnight()
        granularity = self.granularity()

        #if granularity == 1:
        #    days -= 25568        

        increments_in_day = <int>(86400/granularity)
        increments_in_sec = <int>(seconds/granularity)
        value = days*increments_in_day + increments_in_sec
        return value 

    def julian(self):
        return self._julian

    def seconds_since_midnight(self):
        return self._seconds_since_midnight

    def granularity(self):
        return self._granularity

    def date_style(self):
        return self._date_style    

    def time_style(self):
        return self._time_style

    def midnight_as_2400(self):
        return self._midnight_as_2400

    def set_midnight_as_2400(self,flag=True):
        self._midnight_as_2400 = flag 
        if not self.is_undefined():
            if flag:
                if self.seconds_since_midnight() == 0:
                    self._julian -= 1
                    self._seconds_since_midnight = 86400
            else:    
                if self.seconds_since_midnight() == 86400:
                    self._julian += 1
                    self._seconds_since_midnight = 0

    def is_undefined(self):
        if self.julian() == UNDEFINED_TIME or self.seconds_since_midnight() == UNDEFINED_TIME:
            return True    

    def date(self,date_style=None):
        if self.is_undefined():
            return "UNDEFINED"
        if date_style is None:
            date_style = self.date_style()
        return HecTime._julian_to_date(self.julian(),date_style)

    def time(self,time_style=None):
        if self.is_undefined():
            return "UNDEFINED"
        if time_style is None:
            time_style = self.time_style()
        return HecTime._seconds_to_time(self.seconds_since_midnight(), time_style_code=time_style)

    def datetime(self):
        if self.is_undefined():
            return

        htime = self
        if self.midnight_as_2400():
            htime = self.clone()
            htime.set_midnight_as_2400(False)

        #01Jun2025
        date = htime.date(104)
        #10:30:00
        time = htime.time(2)
        return datetime.strptime(f"{date} {time}","%d%b%Y %H:%M:%S")

    def second(self):
        if self.is_undefined():
            return
        ts = self.time(2)
        if ts:
            ts = ts.split(":")
            return int(ts[2])

    def minute(self):
        if self.is_undefined():
            return
        ts = self.time(2)
        if ts:
            ts = ts.split(":")
            return int(ts[1])

    def hour(self):
        if self.is_undefined():
            return
        ts = self.time(2)
        if ts:
            ts = ts.split(":")
            return int(ts[0])

    def day(self):
        if self.is_undefined():
            return
        yymmdd = HecTime._julian_to_ymd(self.julian())
        if yymmdd:
            return yymmdd[2]

    def month(self):
        if self.is_undefined():
            return
        yymmdd = HecTime._julian_to_ymd(self.julian())
        if yymmdd:
            return yymmdd[1]

    def year(self):
        if self.is_undefined():
            return
        yymmdd = HecTime._julian_to_ymd(self.julian())
        if yymmdd:
            return yymmdd[0]

    def add_seconds(self,int count):
        self.add_time(1,count)
    
    def add_minutes(self,int count):
        self.add_time(60,count)

    def add_hours(self,int count):
        self.add_time(3600,count)

    def add_days(self,int count):
        self.add_time(86400,count)

    def add_delta(self,rdelta):
        if not isinstance(rdelta,relativedelta):
            raise TypeError(f"Expective dateutils.relativedelta but received {type(rdelta)}")
        
        if self.is_undefined():
            return
        dt = self.datetime()
        dt += rdelta
        htime = HecTime(dt,
                        granularity=self.granularity(),
                        midnight_as_2400=self.midnight_as_2400(),
                        date_style = self.date_style(),
                        time_style = self.time_style(),
                       )    
        self._julian = htime.julian()               
        self._seconds_since_midnight = htime.seconds_since_midnight()               
        self._granularity = htime.granularity()               
        self._date_style = htime.date_style()               
        self._time_style = htime.time_style()               
        self._midnight_as_2400 = htime.midnight_as_2400()              

    def add_time(self,interval_seconds,periods=1):
        if self.is_undefined():
            return
        jul_sec = HecTime._increment_julian_date_time(self.julian(),self.seconds_since_midnight(),interval_seconds,periods)
        self._julian = jul_sec[0]
        self._seconds_since_midnight = jul_sec[1]
        self.clean_time()


    def clone(self):
        htime = HecTime(self)
        return htime

    @staticmethod
    def split_datetime(str s):
        """
        Split a single mixed date/time string into (date_str, time_str).

        Handles:
          - ISO/XML: 'YYYY-MM-DDThh:mm:ss[Z|+hh:mm]' or with space
          - Trailing times: '... 10:00', '... 10:00:59', '... 10:00 P.M.'
          - Midnight forms: '... 24:00' or '... 24:00:00'
          - Grid style: 'DATE:HHMM' and 'DATE:HHMMSS' (e.g., 'JUN 1, 1985:010000')
          - Plain trailing digits: '... 1000' or '... 010000'
          - Trims trailing punctuation on the date; preserves AM/PM dots.
        """
        if s is None:
            return ("", "")

        s_stripped = s.strip()
        if s_stripped.lower() == "undefined":
            result =  ("", "")
            logging.debug(f"Parsed as {result}")
            return result

        try:
            # Defined regex fails to parse date string (no time part)
            # Using dateutils to fix this
            dt = parser.parse(s)
            result = dt.strftime("%d%b%Y:%H%M%S")
            result = result.split(":")
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                logging.debug(f"Parsed by dateutil: {s} only contains date")
                s = s.strip()
                if s[-1] in (".",",","-","_",";",":"):
                    s = s[0:-1]
                return (s,"")

            # At this point, dateutil has parsed the datetime string; however, we want the date+time to be parsed by regex instead.
            # This makes the pytest "expected" value deterministic and explicitly defined.

        except:
            logging.debug(f"Failed to parse '{s}' with dateutil; falling back to regex-based parsing.")        

        # 1) ISO/XML
        m = __ISO.match(s_stripped)
        if m:
            logging.debug("Parsed datetime: ISO format")
            result = (m.group('date'), m.group('time'))
            logging.debug(f"Parsed as {result}")
            return result

        # 2) GRID (exactly one colon in entire input)
        if s_stripped.count(':') == 1:
            mg = __GRID.match(s_stripped)
            if mg:
                logging.debug("Parsed datetime: GRID format")
                result =  (mg.group('date').rstrip(' ,;:.'), mg.group('time'))
                logging.debug(f"Parsed as {result}")
                return result

        # 3) Trailing hh:mm[:ss][ AM/PM]
        m = __COLON_TIME.search(s_stripped)
        if m:
            logging.debug("Parsed datetime: COLON format")
            start = m.start('time')
            left = s_stripped[:start].rstrip(' ,;:.')   # also strip trailing '.'
            right = s_stripped[start:].strip().rstrip(' ,;')  # keep '.' for "P.M."
            result = (left,right)
            logging.debug(f"Parsed as {result}")
            return result

        # 4) Trailing hhmm[ AM/PM]
        m = __PLAIN_TIME.search(s_stripped)
        if m:
            logging.debug("Parsed datetime: PLAIN format")
            start = m.start('time')
            left = s_stripped[:start].rstrip(' ,;:.')   # also strip trailing '.'
            right = s_stripped[start:].strip().rstrip(' ,;')  # keep '.' for "P.M."
            result = (left,right)
            logging.debug(f"Parsed as {result}")
            return result

        # 5) No time found — trim trailing punctuation commonly seen after dates
        logging.debug("Parsed datetime: time not found")
        result =  (s_stripped.rstrip(' ,;:.'), "")
        logging.debug(f"Parsed as {result}")
        return result

    def __repr__(self):
        return self.__class__.__name__ + "("+ self.date() + " " + self.time() + f" midnight-as-2400={self._midnight_as_2400}" +")"

    #@staticmethod
    #def _clean(int julian,int seconds,int granularity):
    #    cdef:
    #        int status
    #        int days=julian
    #        int secs=seconds
    #
    #    status = cleanTime(&days,&secs,granularity)
    #    if status == 1:
    #        return (days,secs)
    def clean_time(self):
        if not self.is_undefined():
            jul_sec = HecTime._clean_time(self.julian(),self.seconds_since_midnight())
            self._julian = jul_sec[0]
            self._seconds_since_midnight = jul_sec[1]
            self.set_midnight_as_2400(self.midnight_as_2400())

    @staticmethod
    def _clean_time(int julian,int seconds):
        if seconds > 86400:
            julian += 1
            seconds = seconds - 86400
        elif seconds < 0:
            julian -= 1
            seconds = 86400 - seconds

        return (julian,seconds)

    @staticmethod
    def _datetime_from_value(int time, int granularity, int julian_base=0):
        cdef:
            char cdate[20]
            char ctime[15]
            int size_date = sizeof(cdate)
            int size_time = sizeof(ctime)
            int status
        
        if not (granularity == 1 or granularity == 60):
            raise ValueError(f'Granularity must be either 0 or 60 seconds, but {granularity} provided')

        status = getDateAndTime(time, granularity, julian_base, 
                                cdate, size_date, ctime, size_time)
        if status == nok:
            return None

        return (cdate,ctime)
    
    @staticmethod
    def _value_to_julian_seconds(int time, int granularity, int julian_base=0):
        cdef:
            int julian
            int seconds
            int increments_in_day

        increments_in_day = <int>(86400/granularity)
        julian = <int>(time/increments_in_day)
        seconds = (time - julian*increments_in_day)*granularity
        julian += julian_base
        #julian,seconds = HecTime._clean(julian,seconds,1)
        return (julian,seconds)

    @staticmethod
    def _value_to_julian_seconds2(int time, int granularity, object julian_basedate):

        julian_base = julian_basedate

        if isinstance(julian_basedate,str):
            julian_base = HecTime._date_to_julian(julian_basedate)

        if not isinstance(julian_base,int):
            raise ValueError(f"Invalid julian base date ({julian_basedate}) provided")

        return HecTime._value_to_julian_seconds(time,granularity,julian_base)    

    @staticmethod
    def _datetime_to_julian_seconds(str std_datetime_str):
        """Date and time in std_datetime_str should be separared with colon. See examples:
               01DEC2016:0000
               01DEC2016:00:00
               01DEC2016:00:00:00

           Note:
           date is parsed with _date_to_julian
           time is parsed with _time_to_seconds but does not allow fraction second or the last time style
           0000 = returns 0 seconds
           2400 = returns SECS_IN_1_DAY 
        """
        cdef:
            char* cdatetime
            int days
            int seconds
            int status

        logging.debug(f"Converting {std_datetime_str} to (julian,seconds)")
        # TODO: verify input string is correctly formatted
        if not std_datetime_str:
            logging.debug('datetime is empty or None')
            return

        cdatetime = std_datetime_str    
        status = spatialDateTime(cdatetime,&days,&seconds)
        if status == nok:
            raise ValueError(f"Invalid datetime string ({std_datetime_str}) can not be parsed to julian days and seconds")

        days,seconds = HecTime._clean_time(days,seconds)    

        return (days,seconds)    

    @staticmethod
    def _dates_to_julian(date):
        cdef:
            int days
            str _date

        if isinstance(date,int):
            days = date
        elif isinstance(date,str):
            days = HecTime._date_to_julian(date)  
        elif isinstance(date,(tuple,list)):
            days = HecTime._date_to_julian(*date)
        elif isinstance(date,datetime):
            _date = date.strftime("%d%b%Y")  
            days = HecTime._date_to_julian(_date)  
        elif isinstance(date,HecTime):
            days = date.julian()
        else:
            return
        return days

    @staticmethod
    def _date_to_julian(*args):
        """date_to_julian(date_str)
           date_to_julian(year,month,day) 
        """
        cdef:
            str date_str
            char* cdate
            int year
            int month
            int day
            int days

        if len(args) == 1:
            date_str = args[0]
            cdate = date_str
            days = dateToJulian(date_str)

        elif len(args) == 3:
            year = args[0]
            month = args[1]
            day = args[2]
            days = yearMonthDayToJulian(year,month,day)

        else:
            raise TypeError(f"Functions takes either 1 (date) or 3 positional (year, month and day) arguments but {len(args)} were given")

        if days == UNDEFINED_TIME:
            return

        return days

    @staticmethod
    def _julian_to_date(int days,int date_style_code=4):
        """
        """
        cdef:
            char cdate[20]
            int sz = sizeof(cdate)
            int status

        status = julianToDate(days,date_style_code,cdate,sz)
        if status == nok:
            return None
        return cdate

    @staticmethod
    def _julian_to_datetime(int days, int seconds, int date_style_code, int time_style_code):
        cdef:
            str date_str
            str time_str

        date = HecTime._julian_to_date(days,date_style_code)    
        time = HecTime._seconds_to_time(seconds,time_style_code=time_style_code)
        return (date,time)

    @staticmethod
    def _julian_to_dayofweek(int days):
        """Returns 1 to 7 (Sunday to Saturday)
        """
        cdef:
            int day
        day  = dayOfWeek(days)
        return day    

    @staticmethod
    def _julian_to_ymd(int days):
        """Return (YYYY,M,D)
        """
        cdef:
            int year
            int month
            int day
            int status

        status = julianToYearMonthDay(days,&year,&month,&day)
        if status == nok:
            return None

        return (year,month,day)
    
    @staticmethod
    def _increment_julian_date_time(int jl_days, int jl_seconds, int interval_seconds, int number_periods):
        cdef:
            int days
            int seconds
            int status

        status = incrementTime(interval_seconds,number_periods,jl_days,jl_seconds,&days,&seconds)
        if status == nok:
            return None
        return(days,seconds)

    @staticmethod
    def _minutes_to_hhmm(int minutes):
        cdef:
            char hhmm[6]
            sz = sizeof(hhmm)

        minutesToHourMin(minutes,hhmm,sz)            
        return hhmm

    @staticmethod
    def _seconds_to_time(int seconds, int milliseconds=0, int time_style_code=2):
        cdef:
            char ctime[15]
            int sz = sizeof(ctime)
        
        if time_style_code in (0,1,2,3):
            secondsToTimeString(seconds,milliseconds,time_style_code,ctime,sz)
            return ctime 
        logging.warning(f"Unexpected time_style_code = {time_style_code} received")

    @staticmethod
    def _time_to_seconds(str time_str):
        """
        Valid time string formats:
        0830
        08:30
        08:30:43
        08:30:43.5
        """
        cdef:
            float seconds
            char* ctime = time_str
        seconds = timeStringToSecondsMills(ctime)
        if seconds != nok:
            return seconds    


    @staticmethod
    def _number_of_periods(int standard_interval_seconds, 
                                 int jul_start, int jul_start_seconds,
                                 int jul_end, int jul_end_seconds,
                                 ):
        cdef:
            int count

        count = numberPeriods(standard_interval_seconds,
                              jul_start,jul_start_seconds,
                              jul_end,jul_end_seconds,
                             )
        if count == nok:
            return None

        return count 

    @staticmethod
    def _date_to_ymd(str date_str):
        cdef:
            char* cdate = date_str
            int year
            int month
            int day
            int status
        
        status = dateToYearMonthDay(cdate,&year,&month,&day)
        if status == nok:
            return None

        return (year,month,day)


    @staticmethod
    def _add_century(int year):
        year = addCentury(year)
        return year

    @staticmethod
    def _is_leap(int year):
        cdef:
            status = 0
        status = isLeapYear(year)
        return status


    @staticmethod
    def _date_style_codes():
        pass
        styles = {
                  0:"June 2, 1985",
                  1:"Jun 2, 1985",
                  2:"2 June 1985",
                  3:"June 1985",
                  4:"02Jun1985",
                  5:"2Jun1985",
                  6:"Jun1985",
                  7:"02 Jun 1985",
                  8:"2 Jun 1985",
                  9:"Jun 1985",
                  10:"June 2, 85",
                  11:"Jun 2, 85",
                  12:"2 June 85",
                  13:"June 85",
                  14:"02Jun85",
                  15:"2Jun1985",
                  16:"Jun85",
                  17:"02 Jun 85",
                  18:"2 Jun 85",
                  19:"Jun 85",
                 }

        codes = range(100,120)
        styles.update(dict(zip(codes,[x.upper() for x in styles])))
        styles.update( {
                  -1: "6/2/85",
                  -2: "6-2-85",
                  -11: "06/02/85",
                  -12: "06-02-85",
                  -13: "1985-06-02",
                  -101: "6/2/1985",
                  -102: "6-2-1985",
                  -111: "06/02/1985",
                  -112: "06-02-1985"  
                 })

        return styles


