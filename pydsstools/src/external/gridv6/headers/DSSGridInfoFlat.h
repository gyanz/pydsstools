#pragma once
#ifndef DSS_GRID_INFO_FLAT_H
#define DSS_GRID_INFO_FLAT_H
#include "DSSGridInfo.h"
class DSSGridInfoFlat {

public:

  friend class DSSGridInfo;

  DSSGridInfoFlat();
  ~DSSGridInfoFlat();

  void            show();

  int             infoFlatSize() { return _infoFlatSize; };
  int             gridType() { return _gridType; };

protected:

  int             _infoFlatSize;
  int             _gridType;
  int             _infoSize;
  int             _gridInfoSize;
  int             _startTime;
  int             _endTime;
  int             _dataUnits[3];
  int             _dataType;
  int             _lowerLeftCellX;
  int             _lowerLeftCellY;
  int             _numberOfCellsX;
  int             _numberOfCellsY;
  float           _cellSize;
  int             _compressionMethod;
  int             _sizeofCompressedElements;
  float           _compressionScaleFactor;
  float           _compressionBase;
  float           _maxDataValue;
  float           _minDataValue;
  float           _meanDataValue;
  int             _numberOfRanges;
  float           _rangeLimitTable[20];
  int             _numberEqualOrExceedingRangeLimit[20];

};
#endif // DSS_GRID INFO_FLAT_H
