#include "pch.h"
#include "DSSSpecifiedGridInfoFlat.h"
extern "C"
{
#include "heclib.h"
}

DSSSpecifiedGridInfoFlat::DSSSpecifiedGridInfoFlat() : DSSGridInfoFlat(),
_version(0),
_srsNameLength(0),
_srsNameAsHol(NULL),
_srsDefinitionType(0),
_srsDefinitionLength(0),
_srsDefinitionAsHol(NULL),
_nullValue(0.0f),
_timeZoneIdLength(0),
_timeZoneIdAsHol(NULL),
_xCoordinateOfGridCellZero(0.0f),
_yCoordinateOfGridCellZero(0.0f),
_timeZoneRawOffset(0),
_isInterval(0),
_isTimeStamped(0)
{
  _gridType = 430;
  _infoFlatSize = 160;
}

DSSSpecifiedGridInfoFlat::~DSSSpecifiedGridInfoFlat() {
  delete[] _srsNameAsHol;
  delete[] _srsDefinitionAsHol;
  delete[] _timeZoneIdAsHol;
}

void DSSSpecifiedGridInfoFlat::show()
{

  std::cout << std::endl << " = = = SpecifiedGridInfo = = =" << std::endl;
  std::cout << "GridInfo version: " << _version << std::endl;
  // std::cout << "Spatial Reference: " << _srsName << std::endl;
  std::cout << "xCoordinateOfGridCellZero: " << _xCoordinateOfGridCellZero << std::endl;
  std::cout << "yCoordinateOfGridCellZero: " << _yCoordinateOfGridCellZero << std::endl;
  // std::cout << "Time Zone: " << _timeZoneID << std::endl;

  DSSGridInfoFlat::show();
}

int* DSSSpecifiedGridInfoFlat::getInfoAsInts() {
  /*
  *  This is a kludgey way to get the variable lengths
  *  of the long strings included in the SpecifiedGridInfo
  *  object to fit into an array of integers for loading
  *  into the DSS record header.
  */
  int arrayLength;
  int i = 0, j = 0;
  int * temp;
  _infoFlatSize += 4 * _srsNameLength;
  _infoFlatSize += 4 * _srsDefinitionLength;
  _infoFlatSize += 4 * _timeZoneIdLength;
  _infoFlatSize += 136; // space for counts and units

  arrayLength = _infoFlatSize / 4;
  if (_infoFlatSize % 4 != 0) arrayLength += 1;

  int *theInts = new int[arrayLength];

  theInts[i++] = _infoFlatSize;
  theInts[i++] = _gridType;
  theInts[i++] = _infoSize;
  theInts[i++] = _gridInfoSize;
  theInts[i++] = _startTime;
  theInts[i++] = _endTime;
  theInts[i++] = _dataUnits[0];
  theInts[i++] = _dataUnits[1];
  theInts[i++] = _dataUnits[2];
  theInts[i++] = _dataType;
  theInts[i++] = _lowerLeftCellX;
  theInts[i++] = _lowerLeftCellY;
  theInts[i++] = _numberOfCellsX;
  theInts[i++] = _numberOfCellsY;
  temp = (int*)&_cellSize;
  theInts[i++] = *temp;
  theInts[i++] = _compressionMethod;
  theInts[i++] = _sizeofCompressedElements;
  temp = (int*)&_compressionScaleFactor;
  theInts[i++] = *temp;
  temp = (int*)&_compressionBase;
  theInts[i++] = *temp;
  temp = (int*)&_maxDataValue;
  theInts[i++] = *temp;
  temp = (int*)&_minDataValue;
  theInts[i++] = *temp;
  temp = (int*)&_meanDataValue;
  theInts[i++] = *temp;
  theInts[i++] = _numberOfRanges;
  for (j = 0; j < 20; j++) {
    temp = (int*)_rangeLimitTable + j;
    theInts[i++] = *temp;
  }
  for (j = 0; j < 20; j++)
    theInts[i++] = _numberEqualOrExceedingRangeLimit[j];
  theInts[i++] = _version;
  theInts[i++] = _srsNameLength; // # of ints in hol representation
  for (j = 0; j < _srsNameLength; j++)
    theInts[i++] = _srsNameAsHol[j];
  theInts[i++] = _srsDefinitionType;
  theInts[i++] = _srsDefinitionLength; // # of ints in hol representation
  for (j = 0; j < _srsDefinitionLength; j++)
    theInts[i++] = _srsDefinitionAsHol[j];
  temp = (int*)&_xCoordinateOfGridCellZero;
  theInts[i++] = *temp;
  temp = (int*)&_yCoordinateOfGridCellZero;
  theInts[i++] = *temp;
  temp = (int*)&_nullValue;
  theInts[i++] = *temp;
  theInts[i++] = _timeZoneIdLength; // # of ints in hol representation
  for (j = 0; j < _timeZoneIdLength; j++)
    theInts[i++] = _timeZoneIdAsHol[j];
  theInts[i++] = _timeZoneRawOffset;
  theInts[i++] = _isInterval;
  theInts[i] = _isTimeStamped;

  return theInts;
}


void DSSSpecifiedGridInfoFlat::setInfoFromInts(int* theInts) {
  /*
  *  This is a kludgey way to get the variable lengths
  *  of the long strings included in the SpecifiedGridInfo
  *  object to fit into an array of integers for retrieving
  *  the DSS record header.
  */

  int arrayLength;
  int i = 0, j = 0;
  float * temp;

  arrayLength = _infoFlatSize / 4;
  if (_infoFlatSize % 4 != 0) arrayLength += 1;

  _infoFlatSize = theInts[i++];
  _gridType = theInts[i++];
  _infoSize = theInts[i++];
  _gridInfoSize = theInts[i++];
  _startTime = theInts[i++];
  _endTime = theInts[i++];
  _dataUnits[0] = theInts[i++];
  _dataUnits[1] = theInts[i++];
  _dataUnits[2] = theInts[i++];
  _dataType = theInts[i++];
  _lowerLeftCellX = theInts[i++];
  _lowerLeftCellY = theInts[i++];
  _numberOfCellsX = theInts[i++];
  _numberOfCellsY = theInts[i++];
  temp = (float*)&(theInts[i++]);
  _cellSize = *temp;
  _compressionMethod = theInts[i++];
  _sizeofCompressedElements = theInts[i++];
  temp = (float*)theInts + i++;
  _compressionScaleFactor = *temp;
  temp = (float*)theInts + i++;
  _compressionBase = *temp;
  temp = (float*)theInts + i++;
  _maxDataValue = *temp;
  temp = (float*)theInts + i++;
  _minDataValue = *temp;
  temp = (float*)theInts + i++;
  _meanDataValue = *temp;
  _numberOfRanges = theInts[i++];
  for (j = 0; j < 20; j++) {
    temp = (float*)theInts + i++;
    _rangeLimitTable[j] = *temp;
  }
  for (j = 0; j < 20; j++)
    _numberEqualOrExceedingRangeLimit[j] = theInts[i++];
  _version = theInts[i++];
  _srsNameLength = theInts[i++]; // # of ints in hol representation
  _srsNameAsHol = new int[_srsNameLength];
  for (j = 0; j < _srsNameLength; j++)
    _srsNameAsHol[j] = theInts[i++];
  _srsDefinitionType = theInts[i++];
  _srsDefinitionLength = theInts[i++]; // # of ints in hol representation
  _srsDefinitionAsHol = new int[_srsDefinitionLength];
  for (j = 0; j < _srsDefinitionLength; j++)
    _srsDefinitionAsHol[j] = theInts[i++];
  temp = (float*)theInts + i++;
  _xCoordinateOfGridCellZero = *temp;
  temp = (float*)theInts + i++;
  _yCoordinateOfGridCellZero = *temp;
  temp = (float*)theInts + i++;
  _nullValue = *temp;
  _timeZoneIdLength = theInts[i++]; // # of ints in hol representation
  _timeZoneIdAsHol = new int[_timeZoneIdLength];
  for (j = 0; j < _timeZoneIdLength; j++)
    _timeZoneIdAsHol[j] = theInts[i++];
  _timeZoneRawOffset = theInts[i++];
  _isInterval = theInts[i++];
  _isTimeStamped = theInts[i++];

}

