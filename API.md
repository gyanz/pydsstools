API
===
* pydsstools.heclib.dss.HecDss
  * Open(**kwargs) Class
    * read_pd_df(pathname,dtype,copy)
    * read_pd (alias for read_pd_df)
	* read_grid(pathname)
    * getPathnameList(pathname,sort)
    * deletePathname(pathname)
    * members inherited from core.Open class
* pydsstools.core
  * Time-Series
    * TimeSeriesStruct 
      (Object returned when time-series data is read)
      * numberValues
      * times
      * values
      * type
      * units
      * pathname
      * granularity       
      * startDate
      * endDate
      * dtype
    * TimeSeriesContainer(**kwargs) 
      (Container used to store time-series data before writing to file)
      * pathname
      * interval
      * granularity_value
      * numberValues
      * times
      * startDateTime
      * units
      * type
      * values
      * values (setter)
  * Paired Data Series
    * PairedDataStruct 
      (Object returned when paired data series is read)
      * curve_no()
      * data_no()
      * get_data() 
        (Returns tuple  consisting of ordinates,curves and labels)
        * labels
        * dataType
    * PairedDataContainer 
      (Container used to store paired data series before writing to file)
      * pathname
      * curve_no
      * data_no
      * curve_mv 
        (2-D numpy array object with each row representing a curve of length data_no. The total number of rows must be equal to curve_no.)
      * independent_units 
        (feet, ...)
      * independent_type 
        (linear, ...)
      * dependent_units 
        (feet, ...)
      * independent_axis 
        (1-D python or numpy array containing independent axis values whose length must be equal to data_no.)
      * dependent_type
      * labels_list
      * curves
  * Spatial Grid
    * SpatialGridStruct
		* read() - returns (cached) numpy array with grid origin at upper left corner
		* xy(row,col,offset='center') - returns x,y coordinate of z pixel at row and col (same as rasterio)
		* index (x,y,op=math.floor,precision=None) - returns row,col for pixel containing x,y coordinate (same as rasterio)
		* crs - coordinate reference system string
		* dtype - numpy array data type which is np.float32
		* nodata
		* bounds - gives extent of the grid
		* units - unit of array data
		* transform - affine transform matrix of form (dx, 0, xmin, 0, -dy, ymax)
		* profile - dictionary of various attributes
    * SpatialGridContainer 
    * get_grid_version(Open fid,pathname)
  * Open(**kwargs) Class
    * read_path(pathname)
    * read_window(pathname,startDate,startTime,endDate,endTime)
    * put(TimeSeriesContainer tsc, storageFlag=0)  
    * copyRecordsFrom(Open copyFrom, pathnameFrom, pathnameTo="")
    * copyRecordsTo(Open copyTo, pathnameFrom, pathnameTo="")
    * read_pd(pathname)
    * prealloc_pd(PairedDataContainer pdc, label_size)
    * put_one_pd(PairedDataContainer pdc, curve_no)
    * put_pd(PairedDataContainer pdc)
    * read_grid(pathname)
    * put_grid(pathname,grid_array,profile_dict,flipud=1)
  * HecTime(datetimeString,granularity_value=60) Class
    * granularity_value
    * datetimeValue
    * python_datetime 
    * formatDate(format = "%d%b%Y %H:%M")
    * dateString()
    * timeString()
    * addTime(**kwargs)
    * clone()
    * following staticmethods ...
    * parse_datetime_string(datetimeString,granularity_value)
    * getDateTimeStringTuple(dateValue,granularity_value=60)
    * getPyDateTimeFromString(dateString)
    * getPyDateTimeFromValue(dateValue,granularity_value=60)
    * getDateTimeValueTuple(dateValue,granularity_value=60)
