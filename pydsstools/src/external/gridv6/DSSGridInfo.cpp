#include "pch.h"
#include <iomanip>
#include <iostream>
#include <string>
#include "DSSGridInfo.h"
#include "DSSGridInfoFlat.h"



DSSGridInfo::DSSGridInfo(int gridType) {

  _gridType = gridType;
  _infoSize = 124;
  _gridInfoSize = 124;
  _lowerLeftCellX = INT_MIN;
  _lowerLeftCellY = INT_MIN;
  _numberOfCellsX = INT_MIN;
  _numberOfCellsY = INT_MIN;
  _cellSize = UNDEFINED_FLOAT;
  _compressionMethod = UNDEFINED_COMPRESSION_METHOD;
  _sizeofCompressedElements = INT_MIN;
  _compressionScaleFactor = UNDEFINED_FLOAT;
  _compressionBase = UNDEFINED_FLOAT;
  _maxDataValue = UNDEFINED_FLOAT;
  _minDataValue = UNDEFINED_FLOAT;
  _meanDataValue = UNDEFINED_FLOAT;
  _numberOfRanges = 0;
  _rangeLimitTable = NULL;
  _numberEqualOrExceedingRangeLimit = NULL;


}


DSSGridInfo::~DSSGridInfo()
{
  delete[] _rangeLimitTable;
  delete[] _numberEqualOrExceedingRangeLimit;
}

std::string DSSGridInfo::gridTypeName() {
  std::string typeName;
  switch (_gridType) {
  case DATA_TYPE_HGT:
    typeName = "HRAP";
    break;
  case DATA_TYPE_AGT:
    typeName = "ALBERS";
    break;
  case DATA_TYPE_SGT:
    typeName = "SPECIFIED SPATIAL REFERENCE SYSTEM";
    break;
  //case LON_LAT:
  //  typeName = "Longitude-Latitude";
  //  break;
  default:
    typeName = "UNKNOWN";
  }
  return typeName;
}

std::string  DSSGridInfo::dataTypeName() {
  std::string typeName;
  switch (_dataType) {
  case PER_AVER:
    typeName = "PER-AVER";
    break;
  case PER_CUM:
    typeName = "PER-CUM";
    break;
  case INST_VAL:
    typeName = "INST-VAL";
    break;
  case INST_CUM:
    typeName = "INST-CUM";
    break;
  case FREQ:
    typeName = "FREQUENCY";
    break;
  default:
    typeName = "UNKNOWN";
  }
  return typeName;
}


void DSSGridInfo::show()
{
  std::cout << std::endl << std::endl << " = = = GridInfo = = =" << std::endl;
  std::cout << "gridType: " << gridTypeName() << std::endl;
  std::cout << "infoSize: " << _infoSize << std::endl;
  std::cout << "gridInfoSize: " << _gridInfoSize << std::endl;
  std::cout << "startTime: " << _startTime << std::endl;
  std::cout << "endTime:   " << _endTime << std::endl;
  std::cout << "dataUnits: " << _dataUnits << std::endl;
  std::cout << "dataType: " << dataTypeName() << std::endl;
  std::cout << "lowerLeftCellX: " << _lowerLeftCellX << std::endl;
  std::cout << "lowerLeftCellY: " << _lowerLeftCellY << std::endl;
  std::cout << "numberOfCellsX: " << _numberOfCellsX << std::endl;
  std::cout << "numberOfCellsY: " << _numberOfCellsY << std::endl;
  std::cout << "cellSize: " << _cellSize << std::endl;
  std::cout << "compressionMethod: " << (int)_compressionMethod << std::endl;
  std::cout << "sizeofCompressedElements: " << _sizeofCompressedElements << std::endl;
  std::cout << "compressionScaleFactor: " << _compressionScaleFactor << std::endl;
  std::cout << "compressionBase: " << _compressionBase << std::endl;
  std::cout << "maxDataValue: " << _maxDataValue << std::endl;
  std::cout << "minDataValue: " << _minDataValue << std::endl;
  std::cout << "meanDataValue: " << _meanDataValue << std::endl;
  std::cout << "numberOfRanges: " << _numberOfRanges << std::endl;
  std::cout << "           Range        > or =    Incremental Count" << std::endl;
  if (_numberOfRanges > 0) {
    int i;
    for (i = 0; i<_numberOfRanges - 1; i++) {
      std::cout << std::setw(4) << i + 1 << std::setw(14) << _rangeLimitTable[i] << std::setw(12)
        << _numberEqualOrExceedingRangeLimit[i] << std::setw(12)
        << _numberEqualOrExceedingRangeLimit[i] -
        _numberEqualOrExceedingRangeLimit[i + 1] << std::endl;
    }
    i = _numberOfRanges - 1;
    std::cout << std::setw(4) << i + 1 << std::setw(14) << _rangeLimitTable[i] << std::setw(12)
      << _numberEqualOrExceedingRangeLimit[i] << std::setw(12)
      << _numberEqualOrExceedingRangeLimit[i] << std::endl;
  }
  std::cout << "====================================================" << std::endl;
}
void DSSGridInfo::showOneLine() {
  if (_numberOfRanges >= 6) {
    std::cout << _endTime << " "
      << std::setprecision(3) << std::setw(12) << _maxDataValue
      << std::setw(7) << _numberEqualOrExceedingRangeLimit[2]
      << std::setw(5) << _numberEqualOrExceedingRangeLimit[3]
      << std::setw(5) << _numberEqualOrExceedingRangeLimit[4]
      << std::setw(5) << _numberEqualOrExceedingRangeLimit[5]
      << std::setw(5) << _numberEqualOrExceedingRangeLimit[6] << std::endl;
  }
}
void DSSGridInfo::showOneLine(bool title) {
  if (_numberOfRanges >= 6) {
    if (title == true) {
      std::cout << "                             "
        << "Cells equal or exceeding" << std::endl;
    }
    std::cout << "     Time         MaxValue"
      << std::setw(7) << _rangeLimitTable[2]
      << std::setw(5) << _rangeLimitTable[3]
      << std::setw(5) << _rangeLimitTable[4]
      << std::setw(5) << _rangeLimitTable[5]
      << std::setw(5) << _rangeLimitTable[6] << std::endl;
    std::cout << "-----------------------------"
      << "------------------------" << std::endl;
  }
}

int DSSGridInfo::setGridInfoTime(int time) {

  _startTime = time;
  _endTime = INT_MIN;


  return 0;
}

int DSSGridInfo::setGridInfoTimes(int startTime, int endTime) {

  _startTime = startTime;
  _endTime = endTime;


  return 0;
}

int DSSGridInfo::setParameterInfo(
  std::string dataUnits,
  int dataType) {

  _dataUnits = dataUnits;
  _dataType = dataType;

  return 0;
}

int DSSGridInfo::setCellInfo(int lowerLeftCellX, int lowerLeftCellY,
  int numberOfCellsX, int numberOfCellsY,
  float cellSize) {

  _lowerLeftCellX = lowerLeftCellX;
  _lowerLeftCellY = lowerLeftCellY;
  _numberOfCellsX = numberOfCellsX;
  _numberOfCellsY = numberOfCellsY;
  _cellSize = cellSize;

  return 0;
}

int DSSGridInfo::setCompressionInfo(CompressionMethod compressionMethod,
  int sizeofCompressedElements,
  float compressionScaleFactor,
  float compressionBase) {

  _compressionMethod = compressionMethod;
  _sizeofCompressedElements = sizeofCompressedElements;
  _compressionScaleFactor = compressionScaleFactor;
  _compressionBase = compressionBase;

  return 0;
}

int DSSGridInfo::setDataInfo(float maxDataValue, float minDataValue,
  float meanDataValue) {

  _maxDataValue = maxDataValue;
  _minDataValue = minDataValue;
  _meanDataValue = meanDataValue;

  return 0;
}

int DSSGridInfo::setRangeInfo(int numberOfRanges,
  float* rangeLimitTable,
  int* numberEqualOrExceedingRangeLimit) {

  float* newRLT = new float[numberOfRanges];
  int* newEoERLT = new int[numberOfRanges];

  for (int i = 0; i<numberOfRanges; i++) {
    newRLT[i] = rangeLimitTable[i];
    newEoERLT[i] = numberEqualOrExceedingRangeLimit[i];
    // std::cout << "_rangeLimitTable[" << i << "] = " << _rangeLimitTable[i] << std::endl;
  }

  //delete[] _rangeLimitTable;
  //delete[] _numberEqualOrExceedingRangeLimit;
  _numberOfRanges = numberOfRanges;
  _rangeLimitTable = newRLT;
  _numberEqualOrExceedingRangeLimit = newEoERLT;

  return 0;
}

DSSGridInfoFlat* DSSGridInfo::makeGridInfoFlat()
{

  DSSGridInfoFlat *a;
  a = new DSSGridInfoFlat();

  DSSGridInfo::loadFlatData(a);

  return a;
}

int DSSGridInfo::loadFlatData(DSSGridInfoFlat* a) {

  if (_gridType == DATA_TYPE_UGT) {
    a->_gridType = 400;
  }
  else if (_gridType == DATA_TYPE_HGT) {
    a->_gridType = 410;
  }
  else if (_gridType == DATA_TYPE_AGT) {
    a->_gridType = 420;
  }
  else if (_gridType == DATA_TYPE_SGT) {
    a->_gridType = 430;
  }
  a->_infoSize = _infoSize;
  a->_gridInfoSize = _gridInfoSize;

  a->_startTime = _startTime;
  a->_endTime = _endTime;

  char  * temp = new char[13];
  int i;
  for (i = 0; i<13; i++)
    temp[i] = '\0';
  strncpy(temp, _dataUnits.c_str(), 12);
  int one = 1;
  int tweleve = 12;
  chrhol_(temp, &one, &tweleve, a->_dataUnits, &one, (sizeof(temp) - 1));

  a->_dataType = (int)_dataType;
  a->_lowerLeftCellX = _lowerLeftCellX;
  a->_lowerLeftCellY = _lowerLeftCellY;
  a->_numberOfCellsX = _numberOfCellsX;
  a->_numberOfCellsY = _numberOfCellsY;
  a->_cellSize = _cellSize;
  a->_compressionMethod = (int)_compressionMethod;
  a->_sizeofCompressedElements = _sizeofCompressedElements;
  a->_compressionScaleFactor = _compressionScaleFactor;
  a->_compressionBase = _compressionBase;
  a->_maxDataValue = _maxDataValue;
  a->_minDataValue = _minDataValue;
  a->_meanDataValue = _meanDataValue;


  int number = _numberOfRanges;
  if (number > 20)
    number = 20;
  a->_numberOfRanges = number;
  for (i = 0; i<number; i++) {
    a->_rangeLimitTable[i] = _rangeLimitTable[i];
    a->_numberEqualOrExceedingRangeLimit[i] = _numberEqualOrExceedingRangeLimit[i];
  }

  return 0;

}

int DSSGridInfo::convertToGridInfo(DSSGridInfoFlat* b)
{
  /* Differences between 32 and 64 bit implementations of GridInfo objects produce
  * different object sizes. The same DSS record on disk can be different sizes in memory
  * which has produced confusing results for the equality tests on gridInfo objects.
  * I'm  hard-coding the size values in both Java and C++ implementations of grid headers
  * in the GridInfo, AlbersInfo, HrapInfo and SpecifiedGridInfo classes. TAE Dec 2015 */
  _gridInfoSize = 124;

  if (b->_gridType == 400) {
    _gridType = DATA_TYPE_UGT;
    _infoSize = _gridInfoSize;
  }
  else if (b->_gridType == 410) {
    _gridType = DATA_TYPE_HGT;
    _infoSize = 128;
  }
  else if (b->_gridType == 420) {
    _gridType = DATA_TYPE_AGT;
    _infoSize = 164;
  }
  else if (b->_gridType == 430) {
    _gridType = DATA_TYPE_SGT;
    _infoSize = 160;
  }

  _startTime = b->_startTime;
  _endTime = b->_endTime;
  char temp[13];
  temp[12] = '\0';
  int one = 1;
  int tweleve = 12;
  holchr_(b->_dataUnits, &one, &tweleve, temp, &one, (sizeof(temp) - 1));
  _dataUnits = temp;
  _dataType = b->_dataType;
  _lowerLeftCellX = b->_lowerLeftCellX;
  _lowerLeftCellY = b->_lowerLeftCellY;
  _numberOfCellsX = b->_numberOfCellsX;
  _numberOfCellsY = b->_numberOfCellsY;
  _cellSize = b->_cellSize;
  _compressionMethod = (CompressionMethod)b->_compressionMethod;
  _sizeofCompressedElements = b->_sizeofCompressedElements;
  _compressionScaleFactor = b->_compressionScaleFactor;
  _compressionBase = b->_compressionBase;
  _maxDataValue = b->_maxDataValue;
  _minDataValue = b->_minDataValue;
  _meanDataValue = b->_meanDataValue;
  _numberOfRanges = b->_numberOfRanges;

  if (_rangeLimitTable)
    delete[] _rangeLimitTable;
  if (_numberEqualOrExceedingRangeLimit)
    delete[] _numberEqualOrExceedingRangeLimit;

  _rangeLimitTable = new float[_numberOfRanges];

  _numberEqualOrExceedingRangeLimit = new int[_numberOfRanges];

  // _rangeLimitTable            = b->_rangeLimitTable;
  // _numberEqualOrExceedingRangeLimit  = b->_numberEqualOrExceedingRangeLimit;

  for (int i = 0; i<_numberOfRanges; i++) {

    _rangeLimitTable[i] = b->_rangeLimitTable[i];
    _numberEqualOrExceedingRangeLimit[i] = b->_numberEqualOrExceedingRangeLimit[i];
  }

  return 0;

}
bool DSSGridInfo::sameGISframework(DSSGridInfo* a) {
	return _gridType == a->gridType() && _cellSize == a->cellSize();
}

bool DSSGridInfo::sameDataParameter(DSSGridInfo* a) { 
 return  _dataUnits == a->dataUnits() && _dataType == a->dataType();
}

bool DSSGridInfo::sameCellCoverage(DSSGridInfo* a) {

  return sameGISframework(a)
	  && _lowerLeftCellX == a->lowerLeftCellX()
	  && _lowerLeftCellY == a->lowerLeftCellY()
	  && _numberOfCellsX == a->numberOfCellsX()
	  && _numberOfCellsY == a->numberOfCellsY();
}

bool DSSGridInfo::canMosaic(DSSGridInfo* a) {

  return  sameGISframework(a) && sameDataParameter(a);
}

bool DSSGridInfo::canAddCells(DSSGridInfo* a) {
  return sameCellCoverage(a) && sameDataParameter(a);
}

bool DSSGridInfo::canOverlayCells(DSSGridInfo* a) {

  return sameCellCoverage(a);
}

bool DSSGridInfo::_dif(std::string l, std::string a, std::string b, bool y, bool s)
{
  if (a != b) {
    s =false;
    if (y == true) std::cout << l << ": " << a << " :: " << b << " :" << std::endl;
  }
  return s;
}

bool DSSGridInfo::_dif(std::string l, int a, int b, bool y, bool s)
{
  if (a != b) {
    s = false;
    if (y == true) std::cout << l << ": " << a << " :: " << b << " :" << std::endl;
  }
  return s;
}

bool DSSGridInfo::_dif(std::string l, float a, float b, bool y, bool s)
{
  if (a != b) {
    s = false;
    if (y == true) std::cout << l << ": " << a << " :: " << b << " :" << std::endl;
  }
  return s;
}

std::string DSSGridInfo::Info()
{
	std::stringstream ss;
	DSSGridInfo::print(ss);
	return ss.str();
}

void DSSGridInfo::print(std::ostream& os)
{
  os << std::endl << std::endl << " = = = GridInfo = = =" << std::endl;
  os << "Grid Type: " << (int)_gridType << std::endl;
  os << "Info Size: " << _infoSize << std::endl;
  os << "Grid Info Size: " << _gridInfoSize << std::endl;
  os << "Start Time: " << _startTime << std::endl;
  os << "End Time:   " << _endTime << std::endl;
  os << "Data Units: " << _dataUnits << std::endl;
  os << "Data Type: " << (int)_dataType << std::endl;
  os << "Lower Left Cell X: " << _lowerLeftCellX << std::endl;
  os << "Lower Left Cell Y: " << _lowerLeftCellY << std::endl;
  os << "Number Of Cells X: " << _numberOfCellsX << std::endl;
  os << "Number Of Cells Y: " << _numberOfCellsY << std::endl;
  os << "Cell Size: " << _cellSize << std::endl;
  os << "Compression Method: " << (int)_compressionMethod << std::endl;
  os << "Size of Compressed Elements: " << _sizeofCompressedElements << std::endl;
  os << "Compression Scale Factor: " << _compressionScaleFactor << std::endl;
  os << "Compression Base: " << _compressionBase << std::endl;
  os << "Max Data Value: " << _maxDataValue << std::endl;
  os << "Min Data Value: " << _minDataValue << std::endl;
  os << "Mean Data Value: " << _meanDataValue << std::endl;
  os << "Number Of Ranges: " << _numberOfRanges << std::endl;
  os << "           Range        > or =    Incremental Count" << std::endl;
  if (_numberOfRanges > 0) {
    int i;
    for (i = 0; i<_numberOfRanges - 1; i++) {
      os << std::setw(2) << i + 1 << std::setw(14);
      if (_rangeLimitTable[i] == UNDEFINED_FLOAT) { os << "UNDEF"; }
      else os << _rangeLimitTable[i];
      os << std::setw(12) << _numberEqualOrExceedingRangeLimit[i] << std::setw(12)
        << _numberEqualOrExceedingRangeLimit[i] -
        _numberEqualOrExceedingRangeLimit[i + 1] << std::endl;
    }
    i = _numberOfRanges - 1;
    os << std::setw(2) << i + 1 << std::setw(14);
    if (_rangeLimitTable[i] == UNDEFINED_FLOAT) { os << "UNDEF"; }
    else os << _rangeLimitTable[i];
    os << std::setw(12) << _numberEqualOrExceedingRangeLimit[i] << std::setw(12)
      << _numberEqualOrExceedingRangeLimit[i] << std::endl;
  }
  os << "====================================================" << std::endl;
}
