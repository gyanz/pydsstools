from ..core.core_heclib import (HecTime, DssStatusException, GranularityException,ArgumentException)

#getDateTimeValueTuple = core_heclib.getDateTimeValueTuple # args: dateValue, granularity
#getDateTimeStringTuple = core_heclib.getDateTimeStringTuple # args: dateValue, granularity

# HecTime args: dateString, granularity

def pydatetime(*args):
    if len(args) == 1 and isinstance(args[0],str):
        # args: dateString
        return HecTime.getPyDateTimeFromString(args[0])

    # args: dateValue, granularity
    return HecTime.getPyDateTimeFromValue(*args)

