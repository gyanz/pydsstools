#include "pch.h"
#include "EsriAsciiGrid.h"
#include "DSSGrid.h"
/*
read/write arc info ascii raster 
http://desktop.arcgis.com/en/arcmap/10.3/manage-data/raster-and-images/esri-ascii-raster-format.htm

*/

EsriAsciiGrid::EsriAsciiGrid()
{
}


EsriAsciiGrid::~EsriAsciiGrid()
{
}

//=========================================================================
//  toArc  (copied from FlatGrid.cpp)
//
//  write to an Arc/Info
//  ASCII grid file.
//=========================================================================

int EsriAsciiGrid::WriteArcTextFile(zStructSpatialGrid* grid, string outFileName, int precision)
{
	ofstream arcFile(outFileName, ios::out);
	if (!arcFile) {
		cerr << "Cannot open " << outFileName << " for output." << endl;
		exit(1);
	}

	arcFile << "ncols         " << grid->_numberOfCellsX // _ncols
		<< "\nnrows         " << grid->_numberOfCellsY //_nrows
		<< "\nxllcorner     " << DssUtility::FormatDecimalPlaces(grid->_lowerLeftCellX * grid->_cellSize, precision)
		<< "\nyllcorner     " << DssUtility::FormatDecimalPlaces(grid->_lowerLeftCellY * grid->_cellSize, precision)
		<< "\ncellsize      " << DssUtility::FormatDecimalPlaces(grid->_cellSize, precision)
		<< "\nNODATA_value  -9999\n";

	for (int j = grid->_numberOfCellsY; j > 0; j--) {
		for (int i = 1; i <= grid->_numberOfCellsX; i++) {
			float data = DSSGrid::GetCellValue(grid, i, j);
			if (/*data != grid->_nullValue &&*/ data != -FLT_MAX)
				arcFile << DssUtility::FormatDecimalPlaces(data, precision) << ' ';
			else
				arcFile << "-9999 ";
		}
		arcFile << endl;
	}
	arcFile.close();
	return 0;
}

void ParseArcGridMetaData(string fileName, zStructSpatialGrid *grid) {

	ifstream   file(fileName);
	string token;
	string line;
	while (getline(file, token)) {

		if (!isalpha(token[0]))
		{
			return;
		}
		std::istringstream line(token);

		while (line >> token) {

			string s = DssUtility::ToLower(token);
			if (s == "ncols") {
				line >> grid->_numberOfCellsX;
			}
			else  if (s == "nrows") {
				line >> grid->_numberOfCellsY;
			}
			else  if (s == "xllcorner") {
				line >> grid->_xCoordOfGridCellZero;
			}
			else  if (s == "yllcorner") {
				line >> grid->_yCoordOfGridCellZero;
			}
			//else  if (s == "xllcenter") {
			//	//line >> grid->_
			//}
			//else  if (s == "yllcenter") {
			//	//line >> grid->_
			//}
			else  if (s == "cellsize") {
				line >> grid->_cellSize;
			}
			else  if (s == "nodata_value") {
				line >> grid->_nullValue;
			}
		}
	}

}
 
int EsriAsciiGrid::ReadGridfromArc(string inFile, zStructSpatialGrid *grid) {

	string inToken, value;
	//RWRegexp alpha("[a-zA-Z]+");
	//HecDouble arcNoDataValue = -9999;
	string arcNoDataValue = "-9999";
	float llCellCenterX = (double)UNDEFINED_FLOAT;
	float llCellCenterY = (double)UNDEFINED_FLOAT;


	//	vector<string>  lines = DssUtility::FileReadAllLines(inFile);
	ParseArcGridMetaData(inFile, grid);




	return 0;

	//// read the grid description from the file header
	//// the header contains label (alpha) and value (number) pairs
	//int noValueAssigned = 1;
	//inToken.readToken(inFile);
	//while (inToken.index(alpha) != -1) {
	//	value.readToken(inFile);



	//	if (inToken.compareTo("xllcenter", RWCString::ignoreCase) == 0) {
	//		llCellCenterX = HecDouble(value);
	//		noValueAssigned = 0;
	//	}

	//	if (inToken.compareTo("yllcenter", RWCString::ignoreCase) == 0) {
	//		llCellCenterY = HecDouble(value);
	//		noValueAssigned = 0;
	//	}

	//	if (inToken.compareTo("cellsize", RWCString::ignoreCase) == 0) {
	//		_cellSize = HecDouble(value);
	//		noValueAssigned = 0;
	//	}

	//	if (inToken.compareTo("nodata_value", RWCString::ignoreCase) == 0) {
	//		arcNoDataValue = value; //HecDouble(value);
	//		noValueAssigned = 0;
	//	}

	//	if (noValueAssigned) {
	//		cout << "Unknown ASCII grid header line encountered:\n";
	//		cout << inToken << '\t' << value << endl;
	//	}

	//	noValueAssigned = 1;
	//	inToken.readToken(inFile);
	//	inToken = inToken.strip();
	//}

	//// bail out if there's not enough information to define the grid
	//if ((float)_cellSize == UNDEFINED_FLOAT || _nrows == 0 || _ncols == 0) {
	//	_ncols = 0;
	//	_nrows = 0;
	//	_cellSize = UNDEFINED_FLOAT;
	//	return 1;
	//}

	//// if lower left corner is identified by the center of the cell
	//// find the lower left corner coordinates
	//if ((float)_llXcoord == UNDEFINED_FLOAT && (float)llCellCenterX != UNDEFINED_FLOAT)
	//	_llXcoord = llCellCenterX - (_cellSize / 2.);
	//if ((float)_llYcoord == UNDEFINED_FLOAT && (float)llCellCenterY != UNDEFINED_FLOAT)
	//	_llYcoord = llCellCenterY - (_cellSize / 2.);

	//// assign values to the data in the grid
	//_data = new HecDouble[_nrows*_ncols];
	//HecDouble inVal;
	//for (int j = _nrows; j >= 1; j--) {
	//	for (int i = 1; i <= _ncols; i++) {
	//		//inVal =  HecDouble(inToken);
	//		if (inToken != arcNoDataValue) {
	//			setCellValue(i, j, HecDouble(inToken)); // inVal);
	//		}
	//		else {
	//			setCellValue(i, j, UNDEFINED_FLOAT);
	//		}
	//		inToken.readToken(inFile);
	//	}
	//}

	//return 0;
}
