#pragma once
#ifndef DSS_SPECIFIED_GRID_INFO_FLAT_H
#define DSS_SPECIFIED_GRID_INFO_FLAT_H

#include "DSSGridInfoFlat.h"

class DSSSpecifiedGridInfo;

class DSSSpecifiedGridInfoFlat : public DSSGridInfoFlat {

public:

  friend class DSSSpecifiedGridInfo;

  DSSSpecifiedGridInfoFlat();
  ~DSSSpecifiedGridInfoFlat();

  void            show();
  int* getInfoAsInts();
  void setInfoFromInts(int* array);


private:

  int _version;
  int _srsNameLength; // # of ints in hol representation
  int *_srsNameAsHol;
  int _srsDefinitionType;
  int _srsDefinitionLength; // # of ints in hol representation
  int *_srsDefinitionAsHol;
  float _xCoordinateOfGridCellZero;
  float _yCoordinateOfGridCellZero;
  float _nullValue;
  int _timeZoneIdLength; // # of ints in hol representation
  int *_timeZoneIdAsHol;
  int _timeZoneRawOffset;
  int _isInterval;
  int _isTimeStamped;

};
#endif // SPECIFIED_GRID_INFO_FLAT_H