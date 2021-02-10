#include "pch.h"
#include "DSSSpecifiedGridInfo.h"
#include <string>
#include <iostream>
#include "DSSSpecifiedGridInfoFlat.h"
extern "C"
{
#include "heclib.h"
#include "zStructSpatialGrid.h"

}

DSSSpecifiedGridInfo::DSSSpecifiedGridInfo() :DSSGridInfo(DATA_TYPE_SGT) {

  _infoSize = 160;
  _gridInfoSize = 124;
  _version = SPECIFIED_GRID_INFO_VERSION;
  _srsName = "";
  _srsDefinitionType = 0;
  _srsDefinition = "";
  _xCoordinateOfGridCellZero = 0.0f;
  _yCoordinateOfGridCellZero = 0.0f;
  _nullValue = UNDEFINED_FLOAT;
  _timeZoneID = "UTC";
  _timeZoneRawOffset = 0;
  _isInterval = true;
  _isTimeStamped = true;
  this->setCompressionInfo(ZLIB_COMPRESSION, 0, 1.0f, 0.0f);
}

DSSSpecifiedGridInfo::DSSSpecifiedGridInfo(int gridType) : DSSGridInfo(gridType)
{
}


DSSSpecifiedGridInfo::~DSSSpecifiedGridInfo()
{
}

void DSSSpecifiedGridInfo::show()
{

  std::cout << std::endl << " = = = SpecifiedGridInfo = = =" << std::endl;
  std::cout << "GridInfo version: " << _version << std::endl;
  std::cout << "Spatial Reference: " << _srsName << std::endl;
  std::cout << "xCoordinateOfGridCellZero: " << _xCoordinateOfGridCellZero << std::endl;
  std::cout << "yCoordinateOfGridCellZero: " << _yCoordinateOfGridCellZero << std::endl;
  std::cout << "Nulls stored as: " << _nullValue << std::endl;
  std::cout << "Time Zone: " << _timeZoneID << std::endl;

  DSSGridInfo::show();
}


int DSSSpecifiedGridInfo::setSpatialReference(std::string srsName,
  std::string srsDefinition, float xOrigin, float yOrigin) {
  //_srsName = srsName;
  //_srsDefinition = srsDefinition;
  _srsName.erase(0);
  _srsName.append(srsName);
  _srsDefinition.erase(0);
  _srsDefinition.append(srsDefinition);
  _xCoordinateOfGridCellZero = xOrigin;
  _yCoordinateOfGridCellZero = yOrigin;
  return 0;
}

DSSSpecifiedGridInfoFlat* DSSSpecifiedGridInfo::makeGridInfoFlat() {

  int length, charLength;
  length = sizeof(DSSGridInfoFlat) + 33;
  charLength = (int)strlen(_srsName.data());
  length += charLength / 4;
  if (charLength % 4 != 0) length += 1;
  charLength = (int)strlen(_srsDefinition.data());
  length += charLength / 4;
  if (charLength % 4 != 0) length += 1;
  charLength = (int)strlen(_timeZoneID.data());
  length += charLength / 4;
  if (charLength % 4 != 0) length += 1;

  DSSSpecifiedGridInfoFlat *a;
  a = new DSSSpecifiedGridInfoFlat();

  DSSGridInfo::loadFlatData(a);
  DSSSpecifiedGridInfo::loadFlatData(a);

  return a;
}

int DSSSpecifiedGridInfo::loadFlatData(DSSSpecifiedGridInfoFlat* a) {

  int charLength, intLength;
  int one = 1;
  char* temp; // [500];
  int i = 0;

  a->_version = _version;

  // create Hollerith representation of SRS name
  charLength = (int)strlen(_srsName.data());
  intLength = charLength / 4;
  if (charLength % 4 != 0) intLength += 1;
  a->_srsNameLength = intLength;
  a->_srsNameAsHol = new int[intLength];
  a->_srsNameAsHol[intLength - 1] = 0;
  temp = new char[intLength * 4 + 1];
  for (i = 4 * (intLength - 1); i <= intLength * 4; i++)
    temp[i] = '\0';
  strcpy(temp, _srsName.data());
  chrhol_(temp, &one, &charLength, a->_srsNameAsHol, &one, (sizeof(temp) - 1));
  delete[] temp;

  a->_srsDefinitionType = (int)_srsDefinitionType;

  // create Hollerith representation of SRS definition
  charLength = (int)strlen(_srsDefinition.data());
  intLength = charLength / 4;
  if (charLength % 4 != 0) intLength += 1;
  a->_srsDefinitionLength = intLength;
  a->_srsDefinitionAsHol = new int[intLength];
  a->_srsDefinitionAsHol[intLength - 1] = 0;
  temp = new char[intLength * 4 + 1];
  for (i = 4 * (intLength - 1); i <= intLength * 4; i++)
    temp[i] = '\0';
  strcpy(temp, _srsDefinition.data());
  chrhol_(temp, &one, &charLength, a->_srsDefinitionAsHol, &one, (sizeof(temp) - 1));
  delete[] temp;

  a->_xCoordinateOfGridCellZero = _xCoordinateOfGridCellZero;
  a->_yCoordinateOfGridCellZero = _yCoordinateOfGridCellZero;
  a->_nullValue = _nullValue;

  // create Hollerith representation of Time Zone ID
  charLength = (int)strlen(_timeZoneID.data());
  intLength = charLength / 4;
  if (charLength % 4 != 0) intLength += 1;
  a->_timeZoneIdLength = intLength;
  a->_timeZoneIdAsHol = new int[intLength];
  a->_timeZoneIdAsHol[intLength - 1] = 0;
  temp = new char[intLength * 4 + 1];
  for (i = 4 * (intLength - 1); i <= intLength * 4; i++)
    temp[i] = '\0';
  strcpy(temp, _timeZoneID.data());
  chrhol_(temp, &one, &charLength, a->_timeZoneIdAsHol, &one, (sizeof(temp) - 1));
  delete[] temp;

  a->_timeZoneRawOffset = _timeZoneRawOffset;
  a->_isInterval = _isInterval;
  a->_isTimeStamped = _isTimeStamped;





  return 0;
}

int DSSSpecifiedGridInfo::convertToGridInfo(DSSGridInfoFlat* a1) {

  DSSGridInfo::convertToGridInfo(a1);

  int i;
  int theLength;
  int one = 1;
  char temp[2048];

  DSSSpecifiedGridInfoFlat *a = (DSSSpecifiedGridInfoFlat*)a1;

  _version = a->_version;

  // Process the strings, first: the SRS name
  theLength = a->_srsNameLength * 4;
  if (theLength >= 2048)
	  theLength = 2047; 
  for (i = theLength + 1; i > 0; i--) {
    temp[i] = '\0';
  }
  holchr_(a->_srsNameAsHol, &one, &theLength, temp, &one, (sizeof(temp) - 1));
  _srsName = temp;
  _srsDefinitionType = a->_srsDefinitionType;

  // next: the SRS definition
  theLength = a->_srsDefinitionLength * 4;
  for (i = theLength + 1; i > 0; i--) {
    temp[i] = '\0';
  }
  holchr_(a->_srsDefinitionAsHol, &one, &theLength, temp, &one, (sizeof(temp) - 1));
  _srsDefinition = temp;

  // next: the Time Zone ID
  theLength = a->_timeZoneIdLength * 4;
  for (i = theLength + 1; i > 0; i--) {
    temp[i] = '\0';
  }
  holchr_(a->_timeZoneIdAsHol, &one, &theLength, temp, &one, (sizeof(temp) - 1));
  _timeZoneID = temp;

  _xCoordinateOfGridCellZero = a->_xCoordinateOfGridCellZero;
  _yCoordinateOfGridCellZero = a->_yCoordinateOfGridCellZero;
  _nullValue = a->_nullValue;

  _timeZoneRawOffset = a->_timeZoneRawOffset;
  _isInterval = a->_isInterval;
  _isTimeStamped = a->_isTimeStamped;

  return 0;
}

 

