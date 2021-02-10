#include "DSSGrid.h"
#include "DssUtility.h"


 int DSSGrid::RetrieveGriddedData(long long *ifltab, zStructSpatialGrid* gs, int boolRetrieveData)
{

	int gridVer = -1; // version 7 returns (100),  version 6 returns zero (0)
	int status = zspatialGridRetrieveVersion(ifltab, gs->pathname, &gridVer);
	if (status != 0)
		return status;

	if (gridVer == 100) // version 7 grid
	{
		status = zspatialGridRetrieve(ifltab, gs, boolRetrieveData);
	}
	else if (gridVer == 0) // version 6
	{
		int type = DATA_TYPE_SGT; //   initilize
		DSSGridInfo* gridInfo = new DSSGridInfo(type);
		DSSGridData * gridData = new DSSGridData();
		status = RetrieveGriddedDataV6(ifltab, gs->pathname, gridInfo, gridData, boolRetrieveData);

		status = CopyToStructSpatialGrid( gridInfo, gridData, gs,boolRetrieveData); 
	}
	else
	{//  unknown grid version 
		status = -1;
	}

	return status;
}

 zStructSpatialGrid* DSSGrid::RetrieveGriddedData(string dssFileName, string dssPathName)
 {
	 long long ifltab[250];
	 zStructSpatialGrid *gridStruct = zstructSpatialGridNew(dssPathName.c_str());
	 int status = zopen(ifltab, dssFileName.c_str());
	 if (status != 0)
	 {
		 string msg = "Error opening" + dssFileName;
		 // cout << msg << std::endl;
		 throw new std::exception();
	 }
	 DSSGrid::RetrieveGriddedData(ifltab, gridStruct, true);
	 return gridStruct;
 }


 float* float_ref(float f)
 {
  float* p = (float*)malloc(sizeof(float));
  *p = f;
  return p;
 }

 // Copies gridInfo and gridData into zStructSpatialGrid
 // i.e. convert from DSS6 grid formats in to more general V7 structure
 int DSSGrid::CopyToStructSpatialGrid(DSSGridInfo *gridInfo, DSSGridData *gridData, zStructSpatialGrid* gs, bool boolRetrieveData)
 {
	 int status = 0;
	 gs->structType = gridInfo->gridType();
	 gs->_version = 1; //  gridInfo->_version;
	 gs->_type = gridInfo->gridType();
	 gs->_dataUnits = mallocAndCopy(gridInfo->dataUnits().c_str());
	 gs->_dataType = gridInfo->dataType();
	 gs->_lowerLeftCellX = gridInfo->lowerLeftCellX();
	 gs->_lowerLeftCellY = gridInfo->lowerLeftCellY();
	 gs->_numberOfCellsX = gridInfo->numberOfCellsX();
	 gs->_numberOfCellsY = gridInfo->numberOfCellsY();
	 gs->_cellSize = gridInfo->cellSize();
	 gs->_compressionMethod = ZLIB_COMPRESSION; // Zlib is the default compression method 
	 gs->_maxDataValue = float_ref(gridInfo->maxDataValue());
	 gs->_minDataValue = float_ref(gridInfo->minDataValue());
	 gs->_meanDataValue = float_ref(gridInfo->meanDataValue());
	 gs->_numberOfRanges = gridInfo->numberOfRanges();
	 gs->_storageDataType = 0; // Deal with float data for now

	 if (boolRetrieveData)
		 gs->_data = gridData->getAllGriddedValues(&status);
	 if (gs->_numberOfRanges > 0) {
		 gs->_rangeLimitTable = calloc(gs->_numberOfRanges, sizeof(float));
		 gs->_numberEqualOrExceedingRangeLimit = (int*)calloc(gs->_numberOfRanges, sizeof(int));
		 memcpy(gs->_rangeLimitTable, gridInfo->rangeLimitTable(), sizeof(float) * gridInfo->numberOfRanges());
		 memcpy(gs->_numberEqualOrExceedingRangeLimit, gridInfo->numberEqualOrExceedingRangeLimit(), sizeof(float) * gridInfo->numberOfRanges());
	 }
		 
	 if (gridInfo->gridType()  == DATA_TYPE_HGT) {
		 gs->_dataSource = mallocAndCopy(((DSSHrapInfo*)gridInfo)->dataSource().c_str());
		 gs->_srsDefinition = mallocAndCopy(HRAP_SRC_DEFINITION);
		 gs->_xCoordOfGridCellZero = 0;
		 gs->_yCoordOfGridCellZero = 0;
		 gs->_srsDefinitionType = 0;
		 gs->_srsName = mallocAndCopy("WKT");
		 gs->_timeZoneID = mallocAndCopy("UTC");
		 gs->_timeZoneRawOffset = 0;
		 gs->_isInterval = 0;
		 gs->_isTimeStamped = 0;

	 }
	 else if (gridInfo->gridType()== DATA_TYPE_AGT) {
		 DSSAlbersInfo* a = (DSSAlbersInfo*)gridInfo;
		 gs->_dataSource = mallocAndCopy("");
		 string s = GetAlbersSpatialReferenceSystem(a);
		 gs->_srsDefinition = mallocAndCopy(s.c_str());
		 gs->_xCoordOfGridCellZero = a->xCoordOfGridCellZero();
		 gs->_yCoordOfGridCellZero = a->yCoordOfGridCellZero();
		 gs->_srsDefinitionType = 0;
		 gs->_srsName = mallocAndCopy("WKT");
		 gs->_timeZoneRawOffset = 0;
		 gs->_isInterval = 0;
		 gs->_isTimeStamped = 0;
	 }
	 else if (gridInfo->gridType() == DATA_TYPE_SGT) {
		DSSSpecifiedGridInfo*  s = (DSSSpecifiedGridInfo*)gridInfo;
		gs->_dataSource = mallocAndCopy("");
		gs->_srsDefinition = mallocAndCopy(s->srsDefinition().c_str());
		gs->_xCoordOfGridCellZero = s->xCoordinateOfGridCellZero();
		gs->_yCoordOfGridCellZero = s->yCoordinateOfGridCellZero();
		gs->_srsDefinitionType = s->srsDefinitionType();
		gs->_srsName =  mallocAndCopy(s->srsName().c_str());
		gs->_timeZoneID = mallocAndCopy(s->timeZoneID().c_str());
		gs->_timeZoneRawOffset = s->timeZoneRawOffset();
		gs->_nullValue = s->getNullValue();
		gs->_isInterval = s->isInterval() ? 1 : 0;
		gs->_isTimeStamped = s->isTimeStamped() ? 1 : 0;
	 }

	 return status;
 }

 
 string DSSGrid::GetAlbersSpatialReferenceSystem(DSSAlbersInfo* ginfo) {
	 string rval = ginfo->getSpatialReferenceSystem();
	 string pu = "";
	 if (rval.length() == 0) {
		 string datum = "UNDEFINED";
		 switch (ginfo->projectionDatum()) {
		 case NAD_83:
			 datum = "North_American_1983";
			 break;
		 case NAD_27:
			 datum = "North_American_1927";
			 break;
		 }

		 if (DssUtility::StringsEqualIgnoreCase(ginfo->projectionUnits(), "meters"))
			 pu = "UNIT[\"" + ginfo->projectionUnits() + "\",1.0]]";
		 else
			 pu = "UNIT[\"" + ginfo->projectionUnits() + "\",0.0]]";

		 rval = "PROJCS[\"USA_Contiguous_Albers_Equal_Area_Conic_USGS_version\",";
		 rval += "GEOGCS[\"GCS_" + datum + "\",DATUM[\"D_" + datum + "\",";
		 rval += "SPHEROID[\"GRS_1980\",6378137.0,298.257222101]],PRIMEM[\"Greenwich\",0.0],";
			 rval += "UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Albers\"],";
			 rval += "PARAMETER[\"False_Easting\"," + DssUtility::Format(ginfo->falseEasting(), 1);
			 rval += "],PARAMETER[\"False_Northing\"," + DssUtility::Format(ginfo->falseNorthing(), 1) + "],";
			 rval += "PARAMETER[\"Central_Meridian\"," + DssUtility::Format(ginfo->centralMeridian(), 1) + "],PARAMETER[\"Standard_Parallel_1\",";
			 rval += DssUtility::Format(ginfo->firstStandardParallel(), 1) + "],";
			 rval += "PARAMETER[\"Standard_Parallel_2\"," + DssUtility::Format(ginfo->secondStandardParallel(), 1) + "],PARAMETER[\"Latitude_Of_Origin\",";
			 rval += DssUtility::Format(ginfo->latitudeOfProjectionOrigin(), 1) + "],";
			 rval += pu;
	 }
	// rval = DssUtility::ReplaceAll(rval, " ", "");
	 return rval;
 }

 /* from Java..
 private float getParameter(String param, String srs) {
	 String ParamP = "PARAMETER\\[\"" + param + "\",(-?\\d*\\.*\\d+)";
	 Pattern pt = Pattern.compile(ParamP);
	 Matcher matcher = pt.matcher(srs);
	 if (matcher.find()) {
		 String match = matcher.group(1);
		 try {
			 return Float.parseFloat(match);
		 }
		 catch (Exception e) {
			 LOGGER.warning("Error Parsing parameter " + param + " from : + " + srs);
		 }
	 }
	 return 0f;
 }

#define HRAP_SRC_DEFINITION "PROJCS[\"Stereographic_CONUS_HRAP\",\
		GEOGCS[\"GCS_Sphere_LFM\",DATUM[\"D_Sphere_LFM\",\
		SPHEROID[\"Shpere_LFM\",6371200.0,0.0]],PRIMEM[\"Greenwich\",0.0],\
		UNIT[\"Degree\",0.0174532925199433]],\
		PROJECTION[\"Stereographic_North_Pole\"],\
		PARAMETER[\"False_Easting\",1909762.5],PARAMETER[\"False_Northing\",7624762.5],\
		PARAMETER[\"Central_Meridian\",-105.0],PARAMETER[\"Standard_Parallel_1\",60.0],\
		UNIT[\"Meter\",1.0]]"

 */
float DSSGrid::GetWKTParameter(string field, string wkt)
 {
	string findMe = field + "\",";
	int indexOfWord = (int)wkt.find(findMe);
	if (indexOfWord < 0)
		return 0.0;
	int indexOfNum = indexOfWord + (int) findMe.length();
	string str = "";
	for (int i = indexOfNum; i<wkt.length(); i++)
	{
		if (isdigit(wkt.at(i)) || wkt.at(i) == '-' || wkt.at(i) == '.')
		{
			str += wkt.at(i);
		}
		else
		{
			break;
		}
	}
	if (str == "")
		return 0.0;
	return (float)atof(str.c_str());

 }



 

//=========================================================================
// setCellValue(int col, int row, HecDouble value);
// getCellValue(int col, int row)
//
// Member functions set or get value in cell (col, row).  If the grid is
//   -------
//   |7|8|9|
//   |4|5|6|   _data = (1, 2, 3, 4, 5, 6, 7, 8, 9)
//   |1|2|3|
//   -------
//
//  then setCellValue(1, 1, 0) changes it to
//   -------
//   |7|8|9|
//   |4|5|6|   _data = (0, 2, 3, 4, 5, 6, 7, 8, 9)
//   |0|2|3|
//   -------
//
//  and setCellValue(3, 2, 0) further changes it to
//   -------
//   |7|8|9|
//   |4|5|0|   _data = (1, 2, 3, 4, 5, 0, 7, 8, 9)
//   |0|2|3|
//   -------
//
//  setCellValue returns 0 if successful, returns 1 if the _data array
//  has not be created or if either index is out of range
//
//  getCellValue(1, 3) returns 7 for all the grids above.
//=========================================================================
int DSSGrid::SetCellValue(zStructSpatialGrid* grid, int col, int row, float value) {

	if (grid->_data == 0 || col > grid->_numberOfCellsX || row > grid->_numberOfCellsY || col < 1 || row < 1) {
		return 1;
	}

 	((float*)grid->_data)[col - 1 + grid->_numberOfCellsX * (row - 1)] = value;

	return 0;
}

float const DSSGrid::GetCellValue(zStructSpatialGrid* grid, int col, int row) {

	if (col > 0 && col <= grid->_numberOfCellsX && row > 0 && row <= grid->_numberOfCellsY)
		return ((float*)grid->_data)[col + (row - 1)*grid->_numberOfCellsX - 1];
	else {
		cerr << "Cell indices (" << col << ", " << row << ") are out of range.";
		return UNDEFINED_FLOAT;
	}
}


int DSSGrid::RetrieveGriddedDataV6(long long *ifltab, char* pathname, DSSGridInfo *&gridInfo,
	DSSGridData * gridData,bool dataWanted)
{
	int numDataCompressed = 0;
	int recordType = 420;
	int exists = 1;
	zStructRecordSize * srsptr = new zStructRecordSize();
	if (srsptr == nullptr)
	{
		return -1;
	}
	srsptr->pathname = pathname;
	exists = zgetRecordSize(ifltab, srsptr);
	if (exists != 0)
		return -1;
	recordType = srsptr->dataType;
	numDataCompressed = srsptr->values1Number;
	delete srsptr;

	DSSGridInfoFlat * gridInfoFlat=0;
	DSSSpecifiedGridInfoFlat *specifiedGridInfoFlat=0;
	int * gridInfoAsInts=0;
	int gridInfoFlatSize = 187;
	int dummy = 0;
	int found = 0;
	int zero = 0;
	if (recordType == 400)
	{//undefined grid type
		gridInfoFlat = new DSSGridInfoFlat();
		gridInfoFlatSize = sizeof(DSSGridInfoFlat);
		gridInfoAsInts = (int *)gridInfoFlat;
	}
	else if (recordType == 410)
	{//hrap
		gridInfo = new DSSHrapInfo();
		gridInfoFlat = new DSSHrapInfoFlat();
		gridInfoFlatSize = sizeof(DSSHrapInfoFlat);
		gridInfoAsInts = (int *)gridInfoFlat;
	}
	else if (recordType == 420)
	{//albers
		gridInfo = new DSSAlbersInfo();
		gridInfoFlat = new DSSAlbersInfoFlat();
		gridInfoFlatSize = sizeof(DSSAlbersInfoFlat);
		gridInfoAsInts = (int *)gridInfoFlat;
	}
	else if (recordType == 430)
	{//specified grid
		gridInfo = new DSSSpecifiedGridInfo();
		gridInfoFlat = new DSSSpecifiedGridInfoFlat();
		specifiedGridInfoFlat = (DSSSpecifiedGridInfoFlat*)gridInfoFlat;
		gridInfoFlat = (DSSGridInfoFlat*)specifiedGridInfoFlat;
		// Use a large fixed-length array of ints to hold the
		// header for the grid. We'll convert it to a GridInfoFlat
		// object in a conditional block after the zreadx below.
		int narray[300];
		gridInfoAsInts = narray;
		gridInfoFlatSize = 1200;
	}
	dummy = 0;
	found = 0;
	zero = 0;
	int * dataCompressed;
	if (gridInfoFlatSize % 4 != 0)
	{
		printf("\nIlegal gridInfoFlatSize!");
		return -2;
	}
	else
	{
		gridInfoFlatSize = gridInfoFlatSize / 4;
	}
	dataCompressed = new int[numDataCompressed];

	zreadx_(ifltab, pathname, gridInfoAsInts, &gridInfoFlatSize, &gridInfoFlatSize, &dummy, &zero, &dummy, &dummy, &zero, &dummy, dataCompressed, &numDataCompressed,
		&numDataCompressed, &zero, &found, strlen(pathname));
	if (found == 0)
	{
		return -1;
	}
	int type;
	type = gridInfoFlat->gridType();
	if (type >= 430)
	{
		specifiedGridInfoFlat->setInfoFromInts(gridInfoAsInts);
		DSSSpecifiedGridInfo * specifiedGridInfo = (DSSSpecifiedGridInfo*)gridInfo;
		specifiedGridInfo->convertToGridInfo((DSSSpecifiedGridInfoFlat*)gridInfoFlat);
	}
	else if (type >= 420)
	{
		DSSAlbersInfo * albersGridInfo = (DSSAlbersInfo*)gridInfo;
		albersGridInfo->convertToGridInfo((DSSAlbersInfoFlat*)gridInfoFlat);
	}
	else if (type >= 410)
	{
		DSSHrapInfo * hrapGridInfo = (DSSHrapInfo*)gridInfo;
		hrapGridInfo->convertToGridInfo((DSSHrapInfoFlat*)gridInfoFlat);
	}
	else
	{
		gridInfo->convertToGridInfo(gridInfoFlat);
	}
	if (dataWanted)
	{
		int numX, numY, sizeXY;
		numX = gridInfo->numberOfCellsX();
		numY = gridInfo->numberOfCellsY();
		sizeXY = numX * numY;

		float *data;
		data = new float[sizeXY];
		int status = 0, sizeofCompressedElements;
		DSSDataCompression d;
		float compressionScaleFactor, compressionBase;

		sizeofCompressedElements = gridInfo->sizeofCompressedElements();
		//printf("%d\n", gridInfo->sizeofCompressedElements());
		compressionScaleFactor = gridInfo->compressionScaleFactor();
		compressionBase = gridInfo->compressionBase();

		if (gridInfo->compressionMethod() == ZLIB_COMPRESSION)
		{
			status = d.zuncompress(dataCompressed, (sizeofCompressedElements + 3) / 4, data, sizeXY);
			// Deflate compresses the whole array of data, even NULLs. If the
			// header contains a _nullValue, we can check for it.
			if (type == 430 || type == 431)
			{
				float testVal = ((DSSSpecifiedGridInfo*)gridInfo)->getNullValue();
				for (int i = 0; i < sizeXY; i++)
				{
					if (data[i] == testVal)
					{
						data[i] = UNDEFINED_FLOAT;
					}
				}
			}
			else
			{
				// Since the UNDEFINED_FLOAT value for the program that wrote this
				// data may not be the as this library's, we assume anything
				// outside the range of reported max/min values in the array is undefined.
				float minValue = gridInfo->minDataValue();
				float maxValue = gridInfo->maxDataValue();
				for (int i = 0; i < sizeXY; i++)
				{
					if (data[i] < minValue || data[i] > maxValue)
					{
						data[i] = UNDEFINED_FLOAT;
					}
				}
			}
		}
		else
		{
			status = d.uncompress(dataCompressed, sizeofCompressedElements, compressionScaleFactor, compressionBase, data, sizeXY);
		}
		gridData->initGridData(data, gridInfo);
	}
	delete gridInfoFlat;
	delete[] dataCompressed;
	//std::cout << " *gridInfo: " << *gridInfo << std::endl;
	return 0;
}

 

