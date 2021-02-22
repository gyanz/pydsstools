#pragma once
#include "pch.h"
#include "DSSGridInfo.h"
#include "DSSGridData.h"
#include "DSSSpecifiedGridInfoFlat.h"
#include "DSSHrapInfo.h"
#include "DSSSpecifiedGridInfo.h"
#include "DSSAlbersInfo.h"
#include "DSSAlbersInfoFlat.h"
#include "DSSHrapInfoFlat.h"
#include "DSSDataCompression.h"

using std::string;

extern "C"
{
#include "heclib.h"
}

namespace DSSGrid {

	int  RetrieveGriddedData(long long * ifltab, zStructSpatialGrid * gs, int boolRetrieveData);
	zStructSpatialGrid* RetrieveGriddedData(string dssFileName, string dssPathName);

	int RetrieveGriddedDataV6(long long * ifltab, char * pathname, DSSGridInfo *&gridInfo, DSSGridData * gridData, bool dataWanted);
	float GetWKTParameter(string field, string wkt);

	int CopyToStructSpatialGrid(DSSGridInfo *gridInfo, DSSGridData *gridData, zStructSpatialGrid* gs, bool boolRetrieveData);
	string GetAlbersSpatialReferenceSystem(DSSAlbersInfo* ginfo);
	
	float const GetCellValue(zStructSpatialGrid* grid,int col, int row);
	int SetCellValue(zStructSpatialGrid* grid, int col, int row, float value);
	 
}
