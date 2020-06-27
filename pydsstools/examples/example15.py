'''
HecTime and writing Irregular time-series safely
'''
import sys
from pydsstools.heclib.dss.HecDss import Open
from pydsstools.core import TimeSeriesContainer
from pydsstools.heclib.utils import HecTime, DssLastError

dss_file = "example.dss"

fid = Open(dss_file) 

def decor(func):
    def f(*arg,**kwargs):
        try:
            result = func(*arg,**kwargs)
        except:
            print(sys.exc_info()[1])
            print(func.__name__ + ' !!!!!Failed!!!!!\n')
        else:
            print(func.__name__ + ' *****Passed******\n')
            return result
    return f

@decor
def test1():
    # Pass but dss "warning" level error
    fid.read_ts('/a/b/c//e/f/')
    err = DssLastError()
    print("DSS Warning = " + err.errorMessage)

@decor
def test2():
    # Pass
    t = HecTime('02JAN2019 00:00',granularity=60)
    print('dss times value = %r'%t.datetimeValue)

@decor
def test3():
    # Fail
    # time value overflows due to seconds granularity
    t = HecTime('02JAN2019 00:00:10',granularity=1)
    print('dss times value = %r'%t.datetimeValue)

@decor
def test4():
    # Pass
    # Minute granularity does not overflow here (but minute presicion)
    t = HecTime('02JAN2019 00:00:10',granularity=60)
    print('dss times value = %r'%t.datetimeValue)

@decor
def test5():
    # Pass
    # Second granularity does flow without larger julianBaseDate
    pathname ="/IRREGULAR/TIMESERIES/PARAM//IR-DECADE/Ex14_Test5/"
    t = HecTime('02JAN2019 00:10',granularity=1, julianBaseDate='01JAN2000')
    print('dss times value = %r'%t.datetimeValue)


@decor
def test6():
    # Fail 
    # Large date variation and seconds granularity although
    # prevent_overflow = True tries to prevent overflow by setting smallest date (01JAN2019) as julianBaseDate
    pathname ="/IRREGULAR/TIMESERIES/PARAM//IR-DAY/Ex14_Test6/"    
    T = ['01JAN2019 01:00','01JAN2455 00:00']
    tsc = TimeSeriesContainer()
    tsc.pathname = pathname
    tsc.interval = -1
    tsc.granularity = 1
    tsc.times = T
    tsc.values = [2019,5000]
    tsc.numberValues = 2
    fid.put_ts(tsc,prevent_overflow=True)
    #
    ts = fid.read_ts(pathname,regular=False)
    print(ts.pytimes)
    print(ts.values)

@decor
def test7():
    # Pass
    # Writing one time,value pair with prevent_overflow = True is safest 
    pathname = "/IRREGULAR/TIMESERIES/PARAM//IR-DECADE/Ex14_Test7/"
    T = ['01JAN2019 02:01:05','01JAN5000 01:02:06']
    V = [2019,5000]
    for t,v in zip(T,V):
        tsc = TimeSeriesContainer()
        tsc.pathname = pathname
        tsc.interval = -1
        tsc.granularity = 60
        tsc.times = [t]
        tsc.values = [v]
        tsc.numberValues = 1
        fid.put_ts(tsc,prevent_overflow=True)
        
    ts = fid.read_ts(pathname,regular=False)
    print(ts.times)
    print(ts.pytimes)
    print(ts.values)
    return tsc,ts
    

test1()
test2()
test3()
test4()
test5()
test6()
test7()

