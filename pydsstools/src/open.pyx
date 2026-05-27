# TODO: Improve error check and messaging

cdef class Open:
    """
    Internal file handle class for DSS file operations.

    This is a low-level Cython class that provides direct access to HEC-DSS C library
    functions. Users should use the high-level Open class from pydsstools.heclib.dss.HecDss
    instead of using this class directly.

    Parameters
    ----------
    dssFilename : str or bytes
        Path to the DSS file (ASCII encoded).
    version : {6, 7} or None, optional
        DSS file version to use. Default is None.

        - 6 : Use DSS-6 library functions
        - 7 : Use DSS-7 library functions
        - None : Automatically detect version from existing file, or create new file
          using DSS-7 if file does not exist

    Attributes
    ----------
    version : int
        The DSS file version being used (6 or 7).
    filename : str
        The path to the DSS file.
    file_status : int
        Status code from file open operation.
    read_status : int
        Status code from last read operation.
    write_status : int
        Status code from last write operation.

    Notes
    -----
    This class is intended for internal use. Public API is provided through
    pydsstools.heclib.dss.HecDss.Open class which wraps this class with a more
    user-friendly interface.
    """
    cdef:
        long long ifltab[500]
        readonly int version
        readonly str filename
        readonly int file_status
        readonly int read_status
        readonly int write_status

    def __init__(self, dssFilename, version=None):
        if version == 6:
            self.file_status = zopen6(self.ifltab, dssFilename)
        elif version == 7:
            self.file_status = zopen7(self.ifltab, dssFilename)
        else:
            self.file_status = hec_dss_zopen(self.ifltab, dssFilename)
        isError(self.file_status)
        self.version = zgetVersion(self.ifltab)
        self.filename = dssFilename

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        self.close()

    def close(self):
        """Close the DSS file handle."""
        if self.ifltab != NULL:
            zclose(self.ifltab)

    def __version__(self):
        return
        #return zgetFullVersion(self.ifltab)

    def get_status(self):
        """
        Get file operation status codes.

        Returns
        -------
        tuple of (int, int, int)
            Tuple containing (file_status, read_status, write_status).
        """
        return (self.file_status, self.read_status, self.write_status)

    cpdef TimeSeriesStruct _read_ts_normal(self, char *pathname, int retrieveFlag=-1,
                                        int boolRetrieveDoubles=1,
                                        int boolRetrieveQualityNotes=0, int boolRetrieveAllTimes=0):
        """
        Read time-series data from DSS file (internal method).

        This is an internal method. Use the public read_ts method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : bytes
            DSS pathname to retrieve data from (ASCII encoded).
        retrieveFlag : int, optional
            Controls how data is retrieved. Default is -1.

            For regular time series:

            - 0 : Adhere to time window strictly
            - -1 : Trim missing data at beginning and end (not inside)

            For irregular time series:

            - 0 : Adhere to time window strictly
            - 1 : Retrieve one value before time window
            - 2 : Retrieve one value after time window
            - 3 : Retrieve one value before and after time window
        boolRetrieveDoubles : int, optional
            Control precision of retrieved values. Default is 1.

            - 0 : Retrieve values as stored; if missing, return as double
            - 1 : Retrieve as floats
            - 2 : Retrieve as doubles
        boolRetrieveQualityNotes : {0, 1}, optional
            Whether to retrieve quality notes. Default is 0.

            - 0 : Do not retrieve quality and notes
            - 1 : Retrieve quality notes if they exist
        boolRetrieveAllTimes : {0, 1}, optional
            Whether to retrieve all times ignoring date part. Default is 0.

        Returns
        -------
        TimeSeriesStruct
            Time series structure containing the retrieved data.

        Notes
        -----
        This is a low-level method. Use read_ts from the public API instead.
        """
        cdef:
            zStructTimeSeries *ztss = NULL
        ztss = zstructTsNew(pathname)

        if boolRetrieveAllTimes:
            ztss[0].boolRetrieveAllTimes = 1

        self.read_status = ztsRetrieve(self.ifltab, ztss, retrieveFlag,
                                       boolRetrieveDoubles,
                                       boolRetrieveQualityNotes)

        isError(self.read_status)

        if boolRetrieveDoubles == 1:
            ztss[0].doubleValues = NULL
        elif boolRetrieveDoubles == 2:
            ztss[0].floatValues = NULL

        tss = createTSS(ztss)
        return tss

    cpdef TimeSeriesStruct _read_ts_window(self, char *pathname, char *startDate,
                                            char *startTime, char *endDate,
                                            char *endTime,
                                            int retrieveFlag=-1,
                                            int boolRetrieveDoubles=1,
                                            int boolRetrieveQualityNotes=0):
        """
        Read time-series data within a time window (internal method).

        This is an internal method. Use the public read_ts method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : bytes
            DSS pathname to retrieve data from (ASCII encoded).
        startDate : bytes
            Start date for the time window.
        startTime : bytes
            Start time for the time window.
        endDate : bytes
            End date for the time window.
        endTime : bytes
            End time for the time window.
        retrieveFlag : int, optional
            Controls how data is retrieved. Default is -1.
            See _read_ts_normal for details.
        boolRetrieveDoubles : int, optional
            Control precision of retrieved values. Default is 1.
            See _read_ts_normal for details.
        boolRetrieveQualityNotes : {0, 1}, optional
            Whether to retrieve quality notes. Default is 0.

        Returns
        -------
        TimeSeriesStruct
            Time series structure containing the retrieved data.

        Notes
        -----
        This is a low-level method. Use read_ts from the public API instead.
        """
        cdef:
            zStructTimeSeries *ztss = NULL
        ztss = zstructTsNewTimes(pathname, startDate, startTime, endDate, endTime)
        self.read_status = ztsRetrieve(self.ifltab, ztss, retrieveFlag,
                                       boolRetrieveDoubles,
                                       boolRetrieveQualityNotes)

        isError(self.read_status)

        if boolRetrieveDoubles == 1:
            ztss[0].doubleValues = NULL
        elif boolRetrieveDoubles == 2:
            ztss[0].floatValues = NULL

        tss = createTSS(ztss)
        return tss

    cpdef void _put(self, TimeSeriesContainer tsc, int storageFlag=0) except *:
        """
        Write time-series data to DSS file (internal method).

        This is an internal method. Use the public put_ts method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        tsc : TimeSeriesContainer
            Time series container with data to write.
        storageFlag : int, optional
            Storage flag for controlling write behavior. Default is 0.

        Notes
        -----
        This is a low-level method. Use put_ts from the public API instead.
        """
        cdef:
            TimeSeriesStruct ts_st
            zStructTimeSeries *tss
        ts_st = tsc.create_tss()
        tss = ts_st.tss
        if tss == NULL:
            logging.error("Failed to write time-series")
            return
        self.write_status = ztsStore(self.ifltab, tss, storageFlag)
        isError(self.write_status)

    cpdef int _copyRecordsFrom(self, Open copyFrom, str pathnameFrom, str pathnameTo="") except *:
        """
        Copy records from another DSS file to this file (internal method).

        Parameters
        ----------
        copyFrom : Open
            Source DSS file object to copy from.
        pathnameFrom : str
            Pathname in the source file.
        pathnameTo : str, optional
            Pathname in this file. If empty, uses pathnameFrom. Default is "".

        Returns
        -------
        int
            Status code of the copy operation.

        Notes
        -----
        This is a low-level method. Use copy_path from the public API instead.
        """
        cdef int status
        if not pathnameTo:
            pathnameTo = pathnameFrom
        status = copyRecord(copyFrom, self, pathnameFrom, pathnameTo)
        return status

    cpdef int _copyRecordsTo(self, Open copyTo, str pathnameFrom, str pathnameTo="") except *:
        """
        Copy records from this file to another DSS file (internal method).

        Parameters
        ----------
        copyTo : Open
            Destination DSS file object to copy to.
        pathnameFrom : str
            Pathname in this file.
        pathnameTo : str, optional
            Pathname in the destination file. If empty, uses pathnameFrom. Default is "".

        Returns
        -------
        int
            Status code of the copy operation.

        Notes
        -----
        This is a low-level method. Use copy_path from the public API instead.
        """
        cdef int status
        if not pathnameTo:
            pathnameTo = pathnameFrom
        status = copyRecord(self, copyTo, pathnameFrom, pathnameTo)
        return status


    cpdef PairedDataStruct _read_pd(self, char *pathname, tuple window=None):
        """
        Read paired data from DSS file (internal method).

        This is an internal method. Use the public read_pd method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : bytes
            DSS pathname to retrieve paired data from (ASCII encoded).
        window : tuple of (int, int, int, int) or None, optional
            Index window (1-based) as (row_start, row_end, col_start, col_end).
            If None, retrieves all data. Default is None.

        Returns
        -------
        PairedDataStruct
            Paired data structure containing the retrieved data.

        Notes
        -----
        - Indexes are 1-based (C API convention).
        - This is a low-level method. Use read_pd from the public API instead.
        """
        # Read paired data from the given pathname
        # indexes are 1-based
        cdef:
            zStructPairedData *zpds = NULL
            # retrieve as float
            int rsize_flag = 1
            int row_start, row_end, col_start, col_end

        zpds = zstructPdNew(pathname)

        if window:
            row_start, row_end, col_start, col_end = window
            zpds[0].startingOrdinate = row_start
            zpds[0].endingOrdinate = row_end
            zpds[0].startingCurve = col_start
            zpds[0].endingCurve = col_end

        self.read_status = zpdRetrieve(self.ifltab, zpds, rsize_flag)
        isError(self.read_status)
        pd_st = createPDS(zpds)
        return pd_st

    cpdef int _prealloc_pd(self, PairedDataContainer pdc) except *:
        """
        Preallocate space for paired data in DSS file (internal method).

        This is an internal method. Use the public preallocate_pd method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pdc : PairedDataContainer
            Paired data container specifying the structure to preallocate.

        Returns
        -------
        int
            Status code (implicitly through exception handling).

        Notes
        -----
        - When preallocating, label_size determines how much space to allocate
          for curve labels. If 0, default size is used.
        - This is a low-level method. Use preallocate_pd from the public API instead.
        """
        # When preallocating pd, it is important to know how much size to allocate
        #   for the labels
        # label_size = number of characters in label for a curve in pd
        # When it is 0, default size is used
        # TODO: Error check
        cdef:
            PairedDataStruct pd_st
            zStructPairedData *zpds

        pdc.set_clabels(pdc_mode.allocate)
        pd_st = write_allocate_pdata(pdc)
        zpds = pd_st.zpds
        self.write_status = zpdStore(self.ifltab, zpds, 10)
        isError(self.write_status)

    cpdef int _put_one_pd(self, PairedDataContainer pdc, int col_index, tuple row_window=None) except *:
        """
        Write a single curve to preallocated paired data record (internal method).

        This is an internal method. Use the public put_pd method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pdc : PairedDataContainer
            Paired data container with a single curve to write.
        col_index : int
            Column index (1-based) to write the curve to.
        row_window : tuple of (int, int) or None, optional
            Row range (1-based) as (row_start, row_end). If None, writes to all rows.
            Default is None.

        Returns
        -------
        int
            Status code (implicitly through exception handling).

        Raises
        ------
        ValueError
            If indexes are out of range or data size mismatches.
        IndexError
            If curve has too many values.

        Notes
        -----
        - All indexes are 1-based (C API convention).
        - This is a low-level method. Use put_pd from the public API instead.
        """
        cdef:
            PairedDataStruct pd_st
            zStructPairedData *zpds
            dict info
            int rows, cols
            int row_start, row_end
            int label_size

        # TODO: check data size and indexes
        info = self._pd_info(pdc.pathname)
        rows = info["data_no"]
        cols = info["curve_no"]
        label_size = info['label_size']
        logging.debug(f"Average label size of preallocated paired data = {label_size}")
        pdc.set_clabels(pdc_mode.one, label_size)

        if col_index < 1 or col_index > cols:
            raise ValueError(f"Curve index '{col_index}' is outside the range '1 - {cols}'")

        if not row_window:
            if pdc.rows != rows:
                raise ValueError(f"The number of elements in the curve '{pdc.rows}' is not equal to total rows '{rows}' in the paired data record in the file.")

            pd_st = write_one_pdata(self.ifltab, pdc, col_index)

        else:
            row_start, row_end = row_window

            if row_start < 1 or row_start > rows:
                raise ValueError(f"Paired data row_start index '{row_start}' is outside the range '1 - {rows}'")

            if row_end < 1 or row_end > rows:
                raise ValueError(f"Paired data row_end index '{row_end}' is outside the range '1 - {rows}'")

            if row_start > row_end:
                raise ValueError(f"Paired data row_start '{row_start}' is greater than row_end '{row_end}'")

            if row_start + pdc.rows - 1 > rows:
                raise IndexError("Paired data curve has too many values exceeding allowable row_end index")

            pd_st = write_one_pdata(self.ifltab, pdc, col_index, row_start, row_end)

        zpds = pd_st.zpds
        self.write_status = zpdStore(self.ifltab, zpds, 11)
        isError(self.write_status)

    cpdef int _put_pd(self, PairedDataContainer pdc) except *:
        """
        Write paired data to DSS file (internal method).

        This is an internal method. Use the public put_pd method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pdc : PairedDataContainer
            Paired data container with data to write.

        Returns
        -------
        int
            Status code (implicitly through exception handling).

        Notes
        -----
        This is a low-level method. Use put_pd from the public API instead.
        """
        # TODO: Error check
        cdef:
            PairedDataStruct pd_st
            zStructPairedData *zpds

        pdc.set_clabels(pdc_mode.normal)
        pd_st = write_normal_pdata(pdc)
        zpds = pd_st.zpds
        self.write_status = zpdStore(self.ifltab, zpds, 0)
        isError(self.write_status)

    cpdef void _read_grid100(self, const char *pathname, SpatialGridStruct sg_st, bint retrieve_data) except *:
        """
        Read DSS-7 format (version 100) grid data (internal method).

        This is an internal method. Use the public read_grid method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : bytes
            DSS pathname for the grid record (ASCII encoded).
        sg_st : SpatialGridStruct
            Spatial grid structure to populate with retrieved data.
        retrieve_data : bool
            If True, retrieve grid data. If False, retrieve only metadata.

        Notes
        -----
        This is a low-level method. Use read_grid from the public API instead.
        """
        cdef:
            zStructSpatialGrid *zsgs = NULL
        zsgs = zstructSpatialGridNew(pathname)
        # check if above api call has problem
        isError(ok)
        self.read_status = zspatialGridRetrieve(self.ifltab, zsgs, retrieve_data)
        isError(self.read_status)
        updateSGS(sg_st, zsgs)

    cpdef void _read_grid0(self, const char *pathname, SpatialGridStruct sg_st, object gridinfo6, bint retrieve_data) except *:
        """
        Read DSS-6 format (version 0) grid data and convert to version 100 (internal method).

        This is an internal method. Use the public read_grid method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : bytes
            DSS pathname for the grid record (ASCII encoded).
        sg_st : SpatialGridStruct
            Spatial grid structure to populate with retrieved data.
        gridinfo6 : GridInfo6
            Grid information object for version 6 format.
        retrieve_data : bool
            If True, retrieve grid data. If False, retrieve only metadata.

        Notes
        -----
        This is a low-level method. Use read_grid from the public API instead.
        """
        cdef:
            int status
            zStructSpatialGrid *zsgs = NULL
        zsgs = zstructSpatialGridNew(pathname)
        status = read_grid0_as_grid100(self.ifltab, zsgs, gridinfo6, retrieve_data)
        logging.debug(f"Read grid0 status = {status}")
        updateSGS(sg_st, zsgs)

    cpdef np.ndarray _read_grid0_array(self, const char *pathname, object gridinfo6, bint retrieve_data):
        """
        Read DSS-6 format grid data as numpy array (internal method).

        This is an internal method. Use the public read_grid2 method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : bytes
            DSS pathname for the grid record (ASCII encoded).
        gridinfo6 : GridInfo6
            Grid information object for version 6 format.
        retrieve_data : bool
            If True, retrieve grid data. If False, retrieve only metadata.

        Returns
        -------
        numpy.ndarray or None
            Grid data as numpy array, or None if retrieval fails.

        Notes
        -----
        This is a low-level method. Use read_grid2 from the public API instead.
        """
        cdef:
             np.ndarray data
        data = read_grid0(self.ifltab, pathname, gridinfo6, retrieve_data)
        return data

    def _get_gridver(self, const char *pathname):
        """
        Get grid version from DSS record (internal method).

        Parameters
        ----------
        pathname : bytes
            DSS pathname for the grid record (ASCII encoded).

        Returns
        -------
        int or None
            Grid version number (0 for DSS-6, 100 for DSS-7), or None if invalid.

        Notes
        -----
        This is an internal method used by read_grid methods.
        """
        ver = get_gridver_from_path(self.ifltab, pathname)
        if ver == -1:
            return
        return ver

    def _get_gridtype(self, const char *pathname):
        """
        Get grid type from DSS record (internal method).

        Parameters
        ----------
        pathname : bytes
            DSS pathname for the grid record (ASCII encoded).

        Returns
        -------
        int or None
            Grid type code, or None if invalid.

        Notes
        -----
        This is an internal method used by read_grid methods.
        """
        grid_type = get_gridtype_from_path(self.ifltab, pathname)
        if grid_type == -1:
            return
        return grid_type

    cpdef void _put_grid(self, str pathname, float[:,::1] data, object gridinfo) except *:
        """
        Write DSS-7 format (version 100) grid data (internal method).

        This is an internal method. Use the public put_grid method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : str
            DSS pathname for the grid record.
        data : float[:,::1]
            Grid data as 2D C-contiguous float array.
        gridinfo : GridInfo
            Grid information object for version 7 format.

        Notes
        -----
        This is a low-level method. Use put_grid from the public API instead.
        """
        # TODO: Error check
        save_grid7(self.ifltab, pathname, data, gridinfo)

    cpdef void _put_grid0(self, str pathname, float[:,::1] data, object gridinfo6) except *:
        """
        Write DSS-6 format (version 0) grid data (internal method).

        This is an internal method. Use the public put_grid0 method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : str
            DSS pathname for the grid record.
        data : float[:,::1]
            Grid data as 2D C-contiguous float array.
        gridinfo6 : GridInfo6
            Grid information object for version 6 format.

        Notes
        -----
        This is a low-level method. Use put_grid0 from the public API instead.
        """
        # TODO: Error check
        save_grid0(self.ifltab, pathname, data, gridinfo6)

    cpdef dict _dss_info(self, str pathname):
        """
        Get DSS record information (internal method).

        Parameters
        ----------
        pathname : str
            DSS pathname to query.

        Returns
        -------
        dict
            Dictionary containing DSS record information.

        Notes
        -----
        This is an internal method.
        """
        return dss_info(self, pathname)

    cpdef dict _pd_info(self, str pathname):
        """
        Get paired data record information (internal method).

        This is an internal method. Use the public pd_info method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : str
            DSS pathname for the paired data record.

        Returns
        -------
        dict
            Dictionary with keys:

            - 'curve_no' : int - Number of curves
            - 'data_no' : int - Number of data points
            - 'dtype' : int - Data type code
            - 'label_size' : int - Average label size

        Notes
        -----
        This is a low-level method. Use pd_info from the public API instead.
        """
        result = pd_size(self, pathname)
        data = {}
        data['curve_no'] = result[0]
        data['data_no'] = result[1]
        data['dtype'] = result[3]
        data['label_size'] = result[4]
        logging.debug(f"Paired data queried info: {data}")
        return data

    cpdef int _record_type_code(self, str pathname):
        """
        Get record type code for a DSS pathname (internal method).

        Parameters
        ----------
        pathname : str
            DSS pathname to query.

        Returns
        -------
        int
            Record type code.

        Notes
        -----
        This is an internal method.
        """
        cdef int typecode
        typecode = zdataType(self.ifltab, pathname)
        return typecode

    cpdef str _record_type_name(self, str pathname, bint abbr=False):
        """
        Get record type name for a DSS pathname (internal method).

        This is an internal method. Use the public path_dict method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : str
            DSS pathname to query.
        abbr : bool, optional
            If True, return abbreviated name. If False, return full name.
            Default is False.

        Returns
        -------
        str or None
            Record type name, or None if unknown.

        Notes
        -----
        This includes bug fixes for file, image, and gridded data types that
        may be reported as undefined by zdataType.
        """
        cdef:
            const char* cname
            str name
            int typecode

        name = None
        typecode = zdataType(self.ifltab, pathname)
        logging.debug(f"dss record typecode:{typecode}")

        # cname is static char* and shouldn't be freed manually
        cname = ztypeName(typecode, abbr)
        if cname != NULL:
            name = (<bytes>cname).decode("ascii", "strict")

        # bugfix for file, image and gridded data since it is undefined according to zdataType
        if typecode == 600:
                if abbr:
                    name = "FILE"
                else:
                    cname = DATA_TYPE_600
                    name = (<bytes>cname).decode("ascii", "strict")
        elif typecode == 610:
                if abbr:
                    name = "IMAGE"
                else:
                    cname = DATA_TYPE_610
                    name = (<bytes>cname).decode("ascii", "strict")
        elif typecode >= 400 and typecode <= 431:
            if typecode == 400:
                if abbr:
                    name = "UGT"
                else:
                    cname = DATA_TYPE_400
                    name = (<bytes>cname).decode("ascii", "strict")
            elif typecode == 401:
                if abbr:
                    name = "UG"
                else:
                    cname = DATA_TYPE_401
                    name = (<bytes>cname).decode("ascii", "strict")
            elif typecode == 410:
                if abbr:
                    name = "HGT"
                else:
                    cname = DATA_TYPE_410
                    name = (<bytes>cname).decode("ascii", "strict")
            elif typecode == 411:
                if abbr:
                    name = "HG"
                else:
                    cname = DATA_TYPE_411
                    name = (<bytes>cname).decode("ascii", "strict")
            elif typecode == 420:
                if abbr:
                    name = "AGT"
                else:
                    cname = DATA_TYPE_420
                    name = (<bytes>cname).decode("ascii", "strict")
            elif typecode == 421:
                if abbr:
                    name = "AG"
                else:
                    cname = DATA_TYPE_421
                    name = (<bytes>cname).decode("ascii", "strict")
            elif typecode == 430:
                if abbr:
                    name = "SGT"
                else:
                    cname = DATA_TYPE_430
                    name = (<bytes>cname).decode("ascii", "strict")
            elif typecode == 431:
                if abbr:
                    name = "SG"
                else:
                    cname = DATA_TYPE_431
                    name = (<bytes>cname).decode("ascii", "strict")
            else:
                raise ValueError(f"Unknown record data type code: {typecode}.")

        return name


    cpdef int _ts_type_from_pathname(self, char* pathname):
        """
        Determine time series type from pathname (internal method).

        This is an internal method. Use the public read_ts or put_ts methods from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : bytes
            DSS pathname to analyze (ASCII encoded).

        Returns
        -------
        int
            Time series type indicator:

            - 0 : Not a time series pathname
            - 1 : Regular time series
            - -1 : Irregular time series

        Notes
        -----
        This is a low-level method. The public API methods handle type detection
        automatically.
        """
        cdef:
            path_len = strlen(pathname)
            int cresult
            int interval

        cresult = ztsPathCheckInterval(self.ifltab, pathname, path_len)
        logging.debug(f"path interval check returned {cresult}.")

        if cresult == nok: #-1
            # not a timeseries pathname
            interval = 0
        elif cresult == 0:
            # regular timeseries pathname
            interval = 1
        else:
            # = 1
            # irregular timeseries pathname
            interval = -1
        return interval

    cpdef int _delete_pathname(self, str pathname):
        """
        Delete a DSS record by pathname (internal method).

        This is an internal method. Use the public del_path method from
        pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : str
            DSS pathname to delete.

        Returns
        -------
        int
            Status code of the delete operation.

        Notes
        -----
        This is a low-level method. Use del_path from the public API instead.
        """
        cdef int status
        status = delete_pathname(self, pathname)
        return status

    cpdef CatalogStruct _get_catalog(self,
                                    str pathname,
                                    bint sort=0,
                                    int max_count=0,
                                    int status_wanted=0,
                                    int record_type_code_start=0,
                                    int record_type_code_end=0,
                                    int last_write_time_search=0,
                                    int last_write_time_search_flag=0,
                                    bint include_dates=0
                                    ):
        """
        Get DSS file catalog (internal method).

        This is an internal method. Use the public search_path or path_dict methods
        from pydsstools.heclib.dss.HecDss.Open instead.

        Parameters
        ----------
        pathname : str
            Pathname pattern to search (supports wildcards).
        sort : bool, optional
            If True, sort the catalog. Default is False.
        max_count : int, optional
            Maximum number of records to retrieve. Default is 0 (all).
        status_wanted : int, optional
            Filter by record status. Default is 0.
        record_type_code_start : int, optional
            Start of record type code range filter. Default is 0.
        record_type_code_end : int, optional
            End of record type code range filter. Default is 0.
        last_write_time_search : int, optional
            Filter by last write time. Default is 0.
        last_write_time_search_flag : int, optional
            Flag for last write time search. Default is 0.
        include_dates : bool, optional
            If True, include date information in catalog. Default is False.

        Returns
        -------
        CatalogStruct
            Catalog structure containing matching pathnames.

        Notes
        -----
        This is a low-level method. Use search_path or path_dict from the public
        API instead.
        """
        return CatalogStruct.new(self, pathname, sort, max_count, status_wanted, last_write_time_search, last_write_time_search_flag, include_dates)

    cpdef object _read_location(self, str pathname):
        cdef:
            zStructLocation *zloc = NULL
            bytes _bpath = pathname.encode("ascii")
            const char *cpath = _bpath
        zloc = zstructLocationNew(cpath)
        try:
            self.read_status = zlocationRetrieve(self.ifltab, zloc)
            isError(self.read_status)
            return _location_struct_to_info(zloc)
        finally:
            if zloc != NULL:
                zstructFree(zloc)

    cpdef void _put_location(self, object loc, int storageFlag=0) except *:
        from pydsstools.core.location import LocationInfo
        cdef:
            zStructLocation *zloc = NULL
            bytes _bpath
            const char *cpath
            bytes _btz
            bytes _bsupp

        if not isinstance(loc, LocationInfo):
            raise TypeError(f"Expected LocationInfo, got {type(loc).__name__}")

        _bpath = loc.pathname.text().encode("ascii")
        cpath = _bpath
        zloc = zstructLocationNew(cpath)
        try:
            zloc[0].xOrdinate        = loc.x
            zloc[0].yOrdinate        = loc.y
            zloc[0].zOrdinate        = loc.z
            zloc[0].coordinateSystem = int(loc.coordinate_system)
            zloc[0].coordinateID     = loc.coordinate_id
            zloc[0].horizontalUnits  = int(loc.horizontal_units)
            zloc[0].horizontalDatum  = int(loc.horizontal_datum)
            zloc[0].verticalUnits    = int(loc.vertical_units)
            zloc[0].verticalDatum    = int(loc.vertical_datum)
            if loc.time_zone:
                _btz = loc.time_zone.encode("ascii")
                zloc[0].timeZoneName = PyBytes_AS_STRING(_btz)
            if loc.supplemental:
                _bsupp = "\n".join(loc.supplemental).encode("ascii")
                zloc[0].supplemental = PyBytes_AS_STRING(_bsupp)
            self.write_status = zlocationStore(self.ifltab, zloc, storageFlag)
            isError(self.write_status)
        finally:
            if zloc != NULL:
                zstructFree(zloc)

    def __dealloc__(self):
        if self.ifltab != NULL:
            zclose(self.ifltab)
