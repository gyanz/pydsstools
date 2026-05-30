#cdef extern str DssTimeArray_PythonArrayType = 'l'

cdef extern from "zerrorCodes.h":
    ctypedef struct hec_zdssLastError:
        int errorCode
        int severity
        int errorNumber
        int errorType
        int systemError
        long long lastAddress
        int functionID
        int calledByFunction
        char errorMessage[500] #[MAX_LEN_ERROR_MESS]
        char systemErrorMessage[500] #[MAX_LEN_ERROR_MESS]
        char lastPathname[394] #[MAX_PATHNAME_SIZE]
        char filename[256] #[MAX_FILENAME_LENGTH]
        
    #int zerror(hec_zdssLastError *errorStruct)        
    #hec_zdssLastError zdssLastError # could this be global variable?

cdef extern from "heclib.h":
    #hecdss7.h has status codes
    int STATUS_OKAY
    int STATUS_NOT_OKAY
    int STATUS_RECORD_FOUND
    int STATUS_RECORD_NOT_FOUND
    float UNDEFINED_FLOAT
    double UNDEFINED_DOUBLE
    int UNDEFINED_TIME
    int zisMissingDouble(double value)
    int zisMissingFloat(float value)
    int zerror(hec_zdssLastError *errorStruct)  
    int zerrorCheck()
    int zisError(int status)
    int zerrorSeverity(int errorCode)
    void zsetMessageLevel(int methodID, int levelID)
    int zgetMessageLevel(int group)
    int zdataType (long long *ifltab, const char* pathname)
    char* HRAP_SRC_DEFINITION
    char* SHG_SRC_DEFINITION
    char* UTM_SRC_DEFINITION
    int DATA_TYPE_UGT
    int DATA_TYPE_UG
    int DATA_TYPE_HGT
    int DATA_TYPE_HG
    int DATA_TYPE_AGT
    int DATA_TYPE_AG
    int DATA_TYPE_SGT
    int DATA_TYPE_SG
    char* DATA_TYPE_20
    char* DATA_TYPE_ABBR_20
    char* DATA_TYPE_90
    char* DATA_TYPE_ABBR_90
    char* DATA_TYPE_100
    char* DATA_TYPE_ABBR_100
    char* DATA_TYPE_101
    char* DATA_TYPE_ABBR_101
    char* DATA_TYPE_102
    char* DATA_TYPE_ABBR_102
    char* DATA_TYPE_105
    char* DATA_TYPE_ABBR_105
    char* DATA_TYPE_107
    char* DATA_TYPE_ABBR_107
    char* DATA_TYPE_110
    char* DATA_TYPE_ABBR_110
    char* DATA_TYPE_111
    char* DATA_TYPE_ABBR_111
    char* DATA_TYPE_112
    char* DATA_TYPE_ABBR_112
    char* DATA_TYPE_115
    char* DATA_TYPE_ABBR_115
    char* DATA_TYPE_117
    char* DATA_TYPE_ABBR_117
    char* DATA_TYPE_200
    char* DATA_TYPE_ABBR_200
    char* DATA_TYPE_205
    char* DATA_TYPE_ABBR_205
    char* DATA_TYPE_300
    char* DATA_TYPE_ABBR_300
    char* DATA_TYPE_310
    char* DATA_TYPE_ABBR_310
    char* DATA_TYPE_400
    #char* DATA_TYPE_ABBR_400
    char* DATA_TYPE_401
    #char* DATA_TYPE_ABBR_401
    char* DATA_TYPE_410
    #char* DATA_TYPE_ABBR_410
    char* DATA_TYPE_411
    #char* DATA_TYPE_ABBR_411
    char* DATA_TYPE_420
    #char* DATA_TYPE_ABBR_420
    char* DATA_TYPE_421
    #char* DATA_TYPE_ABBR_421
    char* DATA_TYPE_430
    #char* DATA_TYPE_ABBR_430
    char* DATA_TYPE_431
    #char* DATA_TYPE_ABBR_431
    char* DATA_TYPE_450
    char* DATA_TYPE_ABBR_450
    char* DATA_TYPE_600
    char* DATA_TYPE_ABBR_600
    char* DATA_TYPE_610
    char* DATA_TYPE_ABBR_610
    char* DATA_TYPE_UNDEFINED
    
#cdef extern from "missing.h":
#    int zerror(hec_zdssLastError *errorStruct)
        
cdef extern from "heclib.h":
    # Version
    int zconvertVersion(const char* fileNameFrom, const char* fileNameTo)
    int zgetFileVersion(const char *dssFilename)
    int zgetVersion(long long *ifltab)
    int zgetFullVersion(long long *ifltab) # For example DSS Version "7-BG" = 70207
    #
    int zcopyFile(long long *ifltab, long long *ifltabTo, int statusWanted)
    int zcopyRecord (long long *ifltabFrom, long long *ifltabTo, const char *pathnameFrom, const char *pathnameTo)
    int zduplicateRecord (long long *ifltab, const char *pathnameFrom, const char *pathnameTo) 
    int zdelete(long long *ifltab, const char* pathname)
    # 
    int zcheck(long long *ifltab, const char* pathname)
    int zcatalog(long long *ifltab, const char *pathWithWild, zStructCatalog *catStruct, int boolSorted)
    int zcatalogFile(long long *ifltab, const char *catalogFilename, int boolSorted, const char *pathWithWildChars)
    int zcatalogToFile(long long *ifltab, int catalogHandle, int fortranUnit, int boolSorted)
    int zdataType (long long *ifltab, const char* pathname)

    int zsqueeze(const char *dssFilename)

cdef extern from "heclib.h":
    int spatialDateTime(char *dateTimeString, int *julian, int *seconds)
    int dateToJulian(const char *dateString)
    int julianToDate(int julianDate, int style, char *dateString, size_t sizeofDateString)
    int getDateAndTime(int timeMinOrSec, int timeGranularitySeconds, int julianBaseDate, char *dateString, 
                       int sizeOfDateString, char *hoursMins, int sizeofHoursMins)
    int yearMonthDayToJulian (int year, int month, int day)
    int julianToYearMonthDay (int julian, int *year, int *month, int *day)
    void getDateTimeString(int julian, char *dateString, 
                           size_t sizeofDateString, int dateStyle,
                        int secondsPastMidnight, char *timeString, 
                            size_t sizeofTimeString, int timeStyle)
    int yearMonthDayToDate(int year, int month, int day, int style, char *dateString, size_t lenDateString)                       
    int addCentury(int year)
    int isLeapYear (int year)
    int dateToYearMonthDay(const char *dateString, int *year, int *month, int *day)
    int dayOfWeek(int julian)
    int incrementTime(int intervalSeconds, int numberPeriods, int julianStart, int secondsStart, int *julianEnd, int *secondsEnd)
    void minutesToHourMin(int minutes, char *hoursMins, size_t lenHoursMins)
    int numberPeriods(int intervalSeconds, 
                    int julianStart, int secondsStart, 
                    int julianEnd, int secondsEnd)
    void secondsToTimeString(int secondsPastMidnight, int millsPastSecond, int timeStyle,
                            char *timeString, size_t sizeofTimeString)
    float timeStringToSecondsMills(const char *timeString)
    int cleanTime(int *julianDate, int *itime, int timeGranularitySeconds)

cdef extern from "heclib.h":
    int hec_dss_zopen(long long *ifltab, const char *dssFilename)
    int zopen6(long long *ifltab, const char *dssFilename)
    int zopen7(long long *ifltab, const char *dssFilename)
    int zclose(long long *ifltab)
    int zset(const char* parameter, const char* charVal, int integerValue)
    int zset7(const char* parameter, const char* charVal, int integerValue)
    int zquery(const char* parameter, char* charVal, size_t lenCharVal, int *integerValue)
    # following low level function needed to write grid to DSS6 file
    void zreadx(long long *ifltab, 
                const char *pathname,
                int *internalHeader, int *internalHeaderArraySize , int *internalHeaderNumber, # gridInfoAsInts,  &gridInfoFlatSize, &gridInfoFlatSize
                int *header2, int *header2ArraySize, int *header2Number, #                     # &0 ...
                int *userHeader, int *userHeaderArraySize, int *userHeaderNumber,              # &0 ...
                int *values, int *valuesSize, int *valuesNumber,                               # dataCompressed, &numberDataCompressed, &numberOfCompressed
                int *readPlan,                                                                 # &0 
                int *recordFound)                                                              # &found

    # This is preferred to zreadx - compatible with both DSS-6 and DSS-7 
    int zread(long long *ifltab, zStructTransfer* ztransfer)

    # most of these parameters are in ZStructTransfer.h
    void zwritex(long long *ifltab, 
                 const char *path, int *npath,
                 int *internalHeader, int *internalHeaderNumber,
                 int *header2, int *header2Number,
                 int *userHeader, int *userHeaderNumber,
                 int *values, int *valuesNumber,
                 int *dataType,                                                                 
                 int *plan,
                 int *status, 
                 int *recordFound)                                                              # exists or not

    ctypedef struct zStructTransfer:
        # Private
        int structType
        #
        char *pathname
        int pathnameLength
        int dataType
        int *internalHeader
        int internalHeaderNumber
        int internalHeaderMode
        int *header2
        int header2Number
        int header2Mode
        int *userHeader
        int userHeaderNumber
        int userHeaderMode
        int *values1
        int values1Number
        int values1Mode
        int *values2
        int values2Number
        int values2Mode
        int *values3
        int values3Number
        int values3Mode
        int numberValues
        int logicalNumberValues
        int totalAllocatedSize
        int totalExpandedSize
        int version
        int insufficientSpace
        long long lastWrittenTime
        long long fileLastWrittenTime
        char programName[17]
        long long *info;
        #char allocated[zSTRUCT_length];

    ctypedef struct zStructTimeSeries:
        int *times
        float *floatValues
        double *doubleValues
        int numberValues
        char *type
        char *units
        int timeGranularitySeconds
        int timeIntervalSeconds
        int julianBaseDate
        int startJulianDate
        int endJulianDate
        int startTimeSeconds
        int endTimeSeconds
        char *pathname
        char *pathnameInternal
        int boolRetrieveAllTimes
        char *timeZoneName
        # --- Quality and Notes (Optional) ---
        int *quality           # int quality[numberValues][qualityElementSize]
        int qualityElementSize # length of each quality element; 0 = no quality
        int qualityArraySize   # retrieval only: total int size allocated; not used for storing
        # inotes and cnotes are mutually exclusive (they occupy the same space)
        int *inotes            # fixed-length integer notes (one per value)
        int inoteElementSize
        int inotesArraySize    # retrieval only: total int size allocated; not used for storing
        char *cnotes           # variable-length char notes; one per value, each \0-terminated
        int cnotesSize         # on retrieval: size of cnotes buffer
        int cnotesLengthTotal  # set for storage; returns actual length on retrieval

    const char *ztypeName(int recordType, int boolAbbreviation)
    int ztsPathCheckInterval(long long *ifltab, char *pathname, size_t sizeofPathname)
    int ztsGetStandardInterval(int dssVersion, int *intervalSeconds, char *Epart, size_t sizeofEpart, int *operation)

    zStructTimeSeries *zstructTsNewRegFloats(const char* pathname, 
                                                   float *floatValues, 
                                                   int numberValues, 
                                                   const char *startDate, 
                                                   const char *startTime, 
                                                   const char *units, 
                                                   const char *type)

    zStructTimeSeries *zstructTsNewIrregFloats(const char* pathname,
                                               float *floatValues,
                                               int numberValues,
                                               int *itimes, 
                                               int minSecFlag,
                                               const char* startDateBase, 
                                               const char *units, 
                                               const char *type)

    zStructTimeSeries *zstructTsNewIrregDoubles(const char* pathname,
                                                      double *doubleValues,
                                                      int numberValues,
                                                      int *itimes, 
                                                      int minSecFlag,
                                                      const char* startDateBase, 
                                                      const char *units, 
                                                      const char *type)

    int ztsStore(long long *ifltab, zStructTimeSeries *tss,int storageFlag)
    int ztsRetrieve(long long *ifltab, zStructTimeSeries *tss, 
                          int retrieveFlag, int boolRetrieveDoubles, 
                          int boolRetrieveQualityNotes) # preferred
    zStructTimeSeries *zstructTsNew(const char* pathname) # low-level 
    zStructTimeSeries *zstructTsNewTimes(const char* pathname,
                                      const char* startDate, 
                                      const char* startTime, 
                                      const char* endDate, 
                                      const char* endTime)
    void zstructFree(void *zstruct)


    # paired data series functions
    ctypedef struct zStructPairedData:
        int structType
        char *pathname 
        int numberCurves
        int numberOrdinates
        int startingCurve
        int endingCurve
        int startingOrdinate
        int endingOrdinate
        int numberCurvesInStruct
        int numberOrdinatesInStruct
        float *floatOrdinates
        float *floatValues
        double *doubleOrdinates
        double *doubleValues
        int sizeEachValueRead
        int xprecision
        int yprecision
        char *unitsIndependent
        char *typeIndependent
        char *unitsDependent
        char *typeDependent
        int boolIndependentIsXaxis
        char *labels
        int labelsLength
        char *timeZoneName
        int *userHeader
        int userHeaderNumber
        int *otherInfo
        int otherInfoNumber
        #zStructLocation *locationStruct
        int dataType # float 200, double 205 
        long long lastWrittenTime
        long long fileLastWrittenTime
        char programName[17]
        #char allocated[zSTRUCT_length]

    zStructPairedData* zstructPdNew(const char* pathname)
    int zpdRetrieve(long long *ifltab, zStructPairedData *pds, int retrieveSizeFlag)

    zStructPairedData* zstructPdNewFloats(const char* pathname, float *floatOrdinates, 
                                          float *floatValues, int numberOrdinates, 
                                          int numberCurves, const char *unitsIndependent, 
                                          const char *typeIndependent, 
                                          const char *unitsDependent, 
                                          const char *typeDependent)
    zStructPairedData* zstructPdNewDoubles(const char* pathname, double *doubleOrdinates, 
                                           double *doubleValues, int numberOrdinates, 
                                           int numberCurves, const char *unitsIndependent, 
                                           const char *typeIndependent, 
                                           const char *unitsDependent, 
                                           const char *typeDependent)
    int zpdStore(long long *ifltab, zStructPairedData *pds, int storageFlag)
    int zgetRecordSize(long long *ifltab, zStructRecordSize *recordSize)
    zStructRecordSize* zstructRecordSizeNew(const char* pathname)

    ctypedef struct zStructRecordSize:
        #  Private
        int structType
        char *pathname 
        #  Record information for all data types
        int dataType
        int version
        int numberValues
        int logicalNumberValues
        #  Length (4 byte) of each data array
        int values1Number  #  (For TS, this is data values)
        int values2Number	#  (For TS, this is quality array)
        int values3Number	#  (For TS, this is notes array)
        #  Length (4 byte) of the 3 header arrays
        int internalHeaderNumber
        int header2Number
        int userHeaderNumber
        int allocatedSize
        long long lastWriteTimeMillis 
        char programLastWrite[17]
        char password[17]  #  If no password password[0] = '\0'
                            #  If password and you do not have access, password = 'xxxxxxxxx'
                            #  If password and you have access, then this is the real password
        #  Time Series parameters
        int numberRecordsFound
        int itsTimePrecisionStored
        int tsPrecision
        int tsTimeOffset
        int tsProfileDepthsNumber
        int tsBlockStartPosition
        int tsBlockEndPosition
        int tsValueSize
        int tsValueElementSize
        int tsValuesCompressionFlag
        int tsQualityElementSize
        int tsQualityCompressionFlag
        int tsInotesElementSize
        int tsInotesCompressionFlag
        int tsCnotesLength
        #  Paired Data parameters
        int pdNumberCurves
        int pdNumberOrdinates
        int ipdValueSize
        int pdBoolIndependentIsXaxis
        int pdLabelsLength
        int pdPrecision
        #  Grid parameters
        #  Text parameters
        #  Private - knowing which variables were allocated by the ztsNew functions,
        #  instead of the calling program
        #char allocated[zSTRUCT_length]

    ctypedef struct zStructSpatialTin:
        #  Private
        int structType
        char *pathname  
        # Geospatial metadata
        char* SpatialReferenceSystem
        int SRSType # enum type 0 = WKT
        char* SRSName
        char* SRSUnits
        #  metadata for data values	
        char *units
        char *type
        char *timeZoneName #  Time zone of the data (may or may not match location time zone)
        # Start and end times, required for TIN container, should be derived
        # from the DSS path.
        # TIN is made up of points and connections
        int numberPoints		#  Dimension of arrays
        int connectionSize		#  Second dimension of connection, = 6
        int labelLen			#  Length of label array in bytes
        float slendernessRatio # weeds out splintered triangles
        # These arrays have one value per point
        float *xCoordinate
        float *yCoordinate
        float *value
        int *pointType # enumerated type 0 = DCP 1 = observer gage
        int *isDisabled # enumerated type 0 = active in TIN
        int *numberConnections
        int *connection   #  A doubley dimensioned array
        char *label
        #  Private - knowing which variables were allocated by the ztsNew functions,
        #  instead of the calling program
        #char allocated[zSTRUCT_length]

    zStructSpatialTin* zstructSpatialTinNew(const char* pathname)
    int zspatialTinStore(long long *ifltab, zStructSpatialTin *tinStruct)
    int zspatialTinRetrieve(long long *ifltab, zStructSpatialTin *tinStruct)


    ctypedef struct zStructCatalog:
        #  Private
        int structType
        #  Optional input
        #  For normal catalog, statusWanted = 0, and typeWanted = 0.
        int statusWanted
        int typeWantedStart
        int typeWantedEnd
        #  Search according to record last write time (e.g., records written to
        #  since a previous time (using file header write time)
        #  Times are system times, in mills
        #  lastWriteTimeSearch == 0 for ignore (default)
        #  lastWriteTimeSearchFlag:
        #		-2:		time <  lastWriteTimeSearch
        #		-1:		time <= lastWriteTimeSearch
        #		 0:		time == lastWriteTimeSearch
        #		 1:		time >= lastWriteTimeSearch
        #		 2:		time >  lastWriteTimeSearch
        long long lastWriteTimeSearch 
        int lastWriteTimeSearchFlag   
        #  Output
        #  An array of the pathnames in the DSS file
        char **pathnameList  	 	
        int numberPathnames  #  number of valid pathnames in list
        int boolSorted
        int boolIsCollection
        #  Attribues are descriptors for records, usually used for searching in a list,
        #  but are not used for unique idenity.  
        #  "::" seperates key from attribute, "" seperates attribute sets
        #  For example
        #  pathnameList[43] = /Tulare/Delano/Flow/01Jan1980/1Day/Obs/"
        #  attribues[43] = "County::KernState::CARegion::Southern"
        #  pathnameList[78] = /American/Fair Oaks Local/Flow/01Jan2200/1Hour/ReReg/"
        #  attribues[78] = "Type::SubbasinOrder::142"
        int boolHasAttribues
        char **attributes
        #  If boolIncludeDates == 1 on input, then startDates and endDates
        #  will be int arrays of the julian first and last date for each
        #  record (pathname)
        int boolIncludeDates
        int *startDates
        int *endDates
        #  Always returns these (right there)
        int *recordType
        long long *pathnameHash
        long long *lastWriteTimeRecord
        long long lastWriteTimeFile
        #  CRC values - Resource intensive!  Only use if you reall needed
        unsigned int *crcValues
        int boolGetCRCvalues   #  Set to 1 to have CRC values computed
        #  Private
        int listSize  # size allocated
        long long *sortAddresses  #  Used for sorting
        char *pathWithWildChars  #  Only for info
        #char allocated[zSTRUCT_length]

    zStructCatalog* zstructCatalogNew()


    ctypedef struct zStructSpatialGrid:
        #  Private
        int structType
        #*  Required  *
        char *pathname

        int _structVersion # In case we want to modify the gridstruct later
        int _type # DSS Grid Type 

        # Don't store but in the DSS 
        #int       _infoSize 
        #int       _gridInfoSize 

        int _version
        #int       _verbose
        #int       _startTime
        #int       _endTime 

        char* _dataUnits
        int _dataType
        char* _dataSource # Needed for HRAP grids 
        int _lowerLeftCellX
        int _lowerLeftCellY
        int _numberOfCellsX
        int _numberOfCellsY
        float _cellSize
        int _compressionMethod #zlib for initial implementation
        int _sizeofCompressedElements
        void* _compressionParameters

        char* _srsName
        # for now we're using WKT strings for the SRS definitions, but 
        # here's a placeholder for future options like proj4 or GML
        int _srsDefinitionType
        char* _srsDefinition
        float _xCoordOfGridCellZero
        float _yCoordOfGridCellZero
        float _nullValue
        char* _timeZoneID
        int _timeZoneRawOffset
        int _isInterval # Originally boolean 
        int _isTimeStamped # Originally boolean
        int _numberOfRanges


        # Actual Data
        int _storageDataType
        void *_maxDataValue
        void *_minDataValue
        void *_meanDataValue
        void *_rangeLimitTable
        int *_numberEqualOrExceedingRangeLimit
        void *_data

    cdef enum:
        dataType
    zStructSpatialGrid* zstructSpatialGridNew(const char* pathname)
    int zspatialGridRetrieve(long long *ifltab, zStructSpatialGrid *gdStruct, int boolRetrieveData)
    int zspatialGridStore(long long *ifltab, zStructSpatialGrid *gdStruct)
    int compress_zlib(void* array, int size, void **buffer)
    int uncompress_zlib(const void* buffer, int size, void* data, int dataSize)
    int zspatialGridRetrieveVersion(long long *ifltab, const char *cpath, int* gridStructVersion)
    #void printGridStruct(long long *ifltab, int funtion_id, zStructSpatialGrid *gdStruct)

    char* zlocationPath(const char* pathname)
    zStructLocation* zstructLocationNew(const char* pathname)
    int zlocationStore(long long *ifltab, zStructLocation *locationStruct, int storageFlag)
    int zlocationRetrieve(long long *ifltab, zStructLocation *locationStruct)

    ctypedef struct zStructLocation:
        #int structType                      # [private]
        char *pathname                       # any pathname from the data set; used to form location path

        # --- Location Coordinates ---
        double xOrdinate                     # longitude / easting  (negative = western hemisphere for geographic)
        double yOrdinate                     # latitude / northing
        double zOrdinate                     # elevation

        # coordinateSystem: 0=none  1=Lat/Long  2=State Plane FIPS  3=State Plane ADS  4=UTM  5=local
        int coordinateSystem
        int coordinateID                     # UTM zone #, FIPS SPCS #, or ADS SPCS #

        # horizontalUnits:  0=unspecified  1=feet  2=meters  3=decimal degrees  4=degrees-minutes-seconds
        int horizontalUnits
        # horizontalDatum:  0=unset  1=NAD83  2=NAD27  3=WGS84  4=WGS72  5=local
        int horizontalDatum
        # verticalUnits:    0=unspecified  1=feet  2=meters
        int verticalUnits
        # verticalDatum:    0=unset  1=NAVD88  2=NGVD29  3=local
        int verticalDatum

        char *timeZoneName                   # location time zone (not data TZ); e.g. "PST", never "PDT"
        char *supplemental                   # extra location info (NOT data); null-term, '\n'-delimited pieces

        #char *pathnameInternal              # [private]
        #char allocated[zSTRUCT_length]      # [private]

# DSS-6 Fortran wrappers that expose time-series internal header metadata,
# including location fields (coordinates, timezone, supplemental info).
# zrrtsc_ / zritsc_ are used instead of zlocationRetrieve (DSS-7 only).
cdef extern from "hecdssFort.h":
    # Declared but NOT used in practice: ztsinfo_ requires a full pathname
    # with a non-empty D-part and returns lfound=0 for condensed pathnames
    # (empty D-part, e.g. "//A/B//E/F/"), which is the standard form from
    # the public API.  Use zcatalog + zrrtsc_/zritsc_ instead.
    void ztsinfo_(long long *ifltab, const char *cpath,
                  int *juls, int *istime, int *jule, int *ietime,
                  char *cunits, char *ctype,
                  int *lqual, int *ldouble, int *lfound,
                  size_t cpath_len, size_t cunits_len, size_t ctype_len)

    void zrrtsc_(long long *ifltab,        # opaque DSS file table
                 const char *cpath,        # record pathname string
                 const char *cdate,        # block start date, e.g. "01JAN2000"
                 const char *ctime,        # block start time, e.g. "0720"
                 int *kvals,               # caller buffer size; nvals returns actual count
                 int *nvals,               # number of values actually returned
                 int *lgetdob,             # flag: 1 = populate dvalues instead of svalues
                 int *lfildob,             # flag: 1 = file stores double-precision data
                 float *svalues,           # single-precision output value array
                 double *dvalues,          # double-precision output value array
                 int *jqual,               # per-value quality flag array
                 int *lqual,               # flag: quality data is present in the file
                 int *lqread,              # flag: jqual was successfully populated
                 char *cunits,             # data units string, e.g. "cfs"
                 char *ctype,              # data type string, e.g. "INST-VAL"
                 char *csupp,              # supplemental header text (newline-delimited key=value)
                 int *iofset,              # period-average time offset in minutes
                 int *jcomp,               # block compression code
                 int *itzone,              # numeric UTC timezone offset (minutes)
                 char *ctzone,             # timezone name string, e.g. "PST"
                 double *coords,           # [x, y, z] coordinate array (3 elements)
                 int *icdesc,              # coordinate descriptor codes (6: sys,id,Hu,Hd,Vu,Vd)
                 int *lcoords,             # flag: coords and icdesc were filled (out)
                 int *istat,               # 0=OK; 1=some values missing (-901 sentinel); 2=missing blocks but data found; 3=1+2; 4=no data returned; 5=no pathname; 11=nvals<1; 12=bad interval; 15=bad date/time; 20=not regular TS; 24=bad pathname; >9=illegal call
                 size_t cpath_len,         # Fortran hidden length of cpath
                 size_t cdate_len,         # Fortran hidden length of cdate
                 size_t ctime_len,         # Fortran hidden length of ctime
                 size_t cunits_len,        # Fortran hidden length of cunits
                 size_t ctype_len,         # Fortran hidden length of ctype
                 size_t csupp_len,         # Fortran hidden length of csupp
                 size_t ctzone_len)        # Fortran hidden length of ctzone

    void zritsc_(long long *ifltab,        # opaque DSS file table
                 const char *cpath,        # record pathname string
                 int *juls,                # search window start Julian day
                 int *istime,              # search window start time (minutes since midnight)
                 int *jule,                # search window end Julian day
                 int *ietime,              # search window end time (minutes since midnight)
                 int *lgetdob,             # flag: 1 = populate dvalues instead of svalues
                 int *lfildob,             # flag: 1 = file stores double-precision data
                 int *itimes,              # per-value times in minutes from ibdate (out)
                 float *svalues,           # single-precision output value array
                 double *dvalues,          # double-precision output value array
                 int *kvals,               # caller buffer size; nvals returns actual count
                 int *nvals,               # number of values actually returned
                 int *ibdate,              # base Julian date for itimes (0 = Dec 31 1899 epoch)
                 int *iqual,               # per-value quality flag array
                 int *lqual,               # flag: quality data is present in the file
                 int *lqread,              # flag: iqual was successfully populated
                 char *cunits,             # data units string
                 char *ctype,              # data type string
                 char *csupp,              # supplemental header text (newline-delimited key=value)
                 int *itzone,              # numeric UTC timezone offset (minutes)
                 char *ctzone,             # timezone name string
                 double *coords,           # [x, y, z] coordinate array (3 elements)
                 int *icdesc,              # coordinate descriptor codes (6 elements)
                 int *lcoords,             # flag: coords and icdesc were filled (out)
                 int *inflag,              # read behavior flag (controls block selection)
                 int *istat,               # 0=OK; 1=nvals exceeded kvals (data truncated, header still populated); 3=no values in window; 4=block not found; 20=not irregular TS; 21=buffer too small; 24=not irregular TS pathname
                 size_t cpath_len,         # Fortran hidden length of cpath
                 size_t cunits_len,        # Fortran hidden length of cunits
                 size_t ctype_len,         # Fortran hidden length of ctype
                 size_t csupp_len,         # Fortran hidden length of csupp
                 size_t ctzone_len)        # Fortran hidden length of ctzone

    # DSS-6 regular time-series write with embedded location arguments.
    # C wrapper -> zsrtsc6.f (timezone globals, CSUPP->IUHEAD) -> zsrtsi6.f (header write).
    # istat: 0=OK, 4=all-missing not stored (for iplan!=2), >9=illegal call.
    void zsrtsc_(long long *ifltab,        # opaque DSS file table
                 const char *cpath,        # record pathname string
                 const char *cdate,        # block start date string
                 const char *ctime,        # block start time string
                 int *nvals,               # number of values to write
                 int *ldouble,             # flag: 0 = use svalues, 1 = use dvalues
                 float *svalues,           # single-precision input value array
                 double *dvalues,          # double-precision input value array (unused when ldouble=0)
                 int *jqual,               # per-value quality flag array
                 int *lqual,               # flag: 1 = write quality flags from jqual
                 char *cunits,             # data units string
                 char *ctype,              # data type string
                 double *coords,           # [x, y, z] coordinate array
                 int *ncoords,             # number of coordinates to write (typically 3)
                 int *icdesc,              # coordinate descriptor codes
                 int *ncdesc,              # number of descriptor codes to write (typically 6)
                 char *csupp,              # supplemental header text
                 int *itzone,              # numeric UTC timezone offset (minutes)
                 char *ctzone,             # timezone name string
                 int *iplan,               # storage plan: how to merge with existing data
                 int *jcomp,               # block compression code
                 double *basev,            # compression base value
                 int *lbasev,              # flag: basev is active
                 int *ldhigh,              # flag: use high-precision double storage
                 int *nprec,               # number of precision digits (for compression)
                 int *istat,               # 0=OK; 4=all-missing not stored (unless iplan=2); 11=nvals<1; 12=bad interval; 15=bad date/time; 16=out of memory; 20=wrong record type; 24=bad pathname; 30=read-only file; 51=bad compression scheme; 52=bad precision; 511=record type mismatch; >9=illegal call
                 size_t cpath_len,         # Fortran hidden length of cpath
                 size_t cdate_len,         # Fortran hidden length of cdate
                 size_t ctime_len,         # Fortran hidden length of ctime
                 size_t cunits_len,        # Fortran hidden length of cunits
                 size_t ctype_len,         # Fortran hidden length of ctype
                 size_t csupp_len,         # Fortran hidden length of csupp
                 size_t ctzone_len)        # Fortran hidden length of ctzone

    # DSS-6 irregular time-series write with embedded location arguments.
    # C wrapper -> zsitsc6.f -> zsitsi6.f (header write).
    # istat: 0=OK, >0=error.
    void zsitsc_(long long *ifltab,        # opaque DSS file table
                 const char *cpath,        # record pathname string
                 int *itimes,              # per-value times in minutes from ibdate
                 float *svalues,           # single-precision input value array
                 double *dvalues,          # double-precision input value array (unused when ldouble=0)
                 int *ldouble,             # flag: 0 = use svalues, 1 = use dvalues
                 int *nvalue,              # number of values to write
                 int *ibdate,              # base Julian date for itimes (0 = Dec 31 1899 epoch)
                 int *jqual,               # per-value quality flag array
                 int *lsqual,              # flag: 1 = write quality flags from jqual
                 char *cunits,             # data units string
                 char *ctype,              # data type string
                 double *coords,           # [x, y, z] coordinate array
                 int *ncoords,             # number of coordinates to write (typically 3)
                 int *icdesc,              # coordinate descriptor codes
                 int *ncdesc,              # number of descriptor codes to write (typically 6)
                 char *csupp,              # supplemental header text
                 int *itzone,              # numeric UTC timezone offset (minutes)
                 char *ctzone,             # timezone name string
                 int *inflag,              # storage flag: how to merge with existing data
                 int *istat,               # 0=OK; 4=nvals=0 so nothing was written; 21=buffer too small; 24=not irregular TS pathname; 30=read-only file; >0=error
                 size_t cpath_len,         # Fortran hidden length of cpath
                 size_t cunits_len,        # Fortran hidden length of cunits
                 size_t ctype_len,         # Fortran hidden length of ctype
                 size_t csupp_len,         # Fortran hidden length of csupp
                 size_t ctzone_len)        # Fortran hidden length of ctzone

