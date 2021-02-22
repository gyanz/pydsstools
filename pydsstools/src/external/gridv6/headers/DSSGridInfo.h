#pragma once
#include <iostream>

extern "C"
{
#include "heclib.h"
}






class DSSGridInfoFlat;

class DSSGridInfo {

public:

  DSSGridInfo(int gridType);
  virtual ~DSSGridInfo();
  virtual void show();
  virtual void showOneLine();
  virtual void showOneLine(bool title);

  bool sameGISframework(DSSGridInfo* a);
  bool sameDataParameter(DSSGridInfo* a);
  bool sameCellCoverage(DSSGridInfo* a);
  bool canMosaic(DSSGridInfo* a);
  bool canAddCells(DSSGridInfo* a);
  bool canOverlayCells(DSSGridInfo* a);

  int setGridInfoTime(int time);
  int setGridInfoTimes(int startTime, int endTime);
  int setParameterInfo(
    std::string dataUnits,
    int dataType);

  virtual int setCellInfo(int lowerLeftCellX, int lowerLeftCellY,
    int numberOfCellsX, int numberOfCellsY,
    float cellSize);
  int setCompressionInfo(CompressionMethod compressionMethod,
    int sizeofCompressedElements,
    float scaleFactor,
    float base);
  int setDataInfo(float maxDataValue, float minDataValue,
    float meanDataValue);
  int setRangeInfo(int numberOfRanges,
    float* rangeLimitTable,
    int* numberEqualOrExceedingRangeLimit);

  int gridType() { return                  _gridType; };
  std::string    gridTypeName();
  int        infoSize() { return                   _infoSize; };
  int        gridInfoSize() { return               _gridInfoSize; };
  int        startTime() { return                 _startTime; };
  int        endTime() { return                   _endTime; };
  std::string dataUnits() { return                 _dataUnits; };
  int       dataType() { return                  _dataType; };
  std::string  dataTypeName();
  int        lowerLeftCellX() { return           _lowerLeftCellX; };
  int        lowerLeftCellY() { return           _lowerLeftCellY; };
  int        numberOfCellsX() { return            _numberOfCellsX; };
  int        numberOfCellsY() { return            _numberOfCellsY; };
  float     cellSize() { return                   _cellSize; };
  CompressionMethod  compressionMethod() { return   _compressionMethod; };
  int        sizeofCompressedElements() { return  _sizeofCompressedElements; };
  float     compressionScaleFactor() { return    _compressionScaleFactor; };
  float     compressionBase() { return           _compressionBase; };
  float      maxDataValue() { return              _maxDataValue; };
  float      minDataValue() { return              _minDataValue; };
  float      meanDataValue() { return             _meanDataValue; };
  int        numberOfRanges() { return            _numberOfRanges; };
  float*     rangeLimitTable() { return           _rangeLimitTable; };
  int*       numberEqualOrExceedingRangeLimit()
  {
    return _numberEqualOrExceedingRangeLimit;
  };

  DSSGridInfoFlat* makeGridInfoFlat();
  int           loadFlatData(DSSGridInfoFlat* gridInfoFlat);
  virtual int           convertToGridInfo(DSSGridInfoFlat* gridInfoFlat);
  void                  print(std::ostream& os); // print helper
  friend std::ostream& operator<<(std::ostream& os, DSSGridInfo g) { g.print(os); return os; };


protected:

  int _gridType;
  int       _infoSize;
  int       _gridInfoSize;
  int       _startTime;
  int       _endTime;
  std::string    _dataUnits;
  int       _dataType;
  int       _lowerLeftCellX;
  int       _lowerLeftCellY;
  int       _numberOfCellsX;
  int       _numberOfCellsY;
  float    _cellSize;
  CompressionMethod _compressionMethod;
  int       _sizeofCompressedElements;
  float    _compressionScaleFactor;
  float    _compressionBase;
  float     _maxDataValue;
  float     _minDataValue;
  float     _meanDataValue;
  int       _numberOfRanges;
  float*    _rangeLimitTable;
  int*      _numberEqualOrExceedingRangeLimit;

  bool _dif(std::string l, std::string a, std::string b, bool y, bool s);
  bool _dif(std::string l, float a, float b, bool y, bool s);
  std::string Info();
  bool _dif(std::string l, int a, int b, bool y, bool s);

private:

};
