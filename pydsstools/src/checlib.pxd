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
    #int STATUS_OK
    #int STATUS_NOT_OK
    #int STATUS_RECORD_FOUND
    #int STATUS_RECORD_NOT_FOUND
    float UNDEFINED_FLOAT
    double UNDEFINED_DOUBLE
    int UNDEFINED_TIME
    int zisMissingDouble(double value)
    int zisMissingFloat(float value)
    int zisError(int status)
    int zerrorSeverity(int errorCode)
    int zerrorCheck()
    void zsetMessageLevel(int methodID, int levelID)
    int zdataType (long long *ifltab, const char* pathname)
    int zerror(hec_zdssLastError *errorStruct)  
    char* HRAP_SRC_DEFINITION
    char* SHG_SRC_DEFINITION
    char* UTM_SRC_DEFINITION

    
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
    void getDateTimeString(int julian, char *dateString, 
                           size_t sizeofDateString, int dateStyle,
                        int secondsPastMidnight, char *timeString, 
                            size_t sizeofTimeString, int timeStyle)
                            
cdef extern from "heclib.h":
    int zopen(long long *ifltab, const char *dssFilename)
    int zopen6(long long *ifltab, const char *dssFilename)
    int zopen7(long long *ifltab, const char *dssFilename)
    int zclose(long long *ifltab)
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
    zStructTimeSeries *zstructTsNewRegFloats(const char* pathname, 
                                                   float *floatValues, 
                                                   int numberValues, 
                                                   const char *startDate, 
                                                   const char *startTime, 
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
    #int compress_zlib(void* array, int size, void **buffer)
    #int uncompress_zlib(const void* buffer, int size, void* data, int dataSize)
    int zspatialGridRetrieveVersion(long long *ifltab, const char *cpath, int* gridStructVersion)
    #void printGridStruct(long long *ifltab, int funtion_id, zStructSpatialGrid *gdStruct)

cdef extern from "DSSGrid_wrap.h":
    int RetrieveGriddedData_wrap(long long * ifltab, zStructSpatialGrid * gs, int boolRetrieveData)

