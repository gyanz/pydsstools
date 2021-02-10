#include "pch.h"
#include "DSSGridInfoFlat.h"
DSSGridInfoFlat::DSSGridInfoFlat() :
  _gridType(INT_MIN),
  _infoSize(INT_MIN),
  _gridInfoSize(INT_MIN),
  _startTime(INT_MIN),
  _endTime(INT_MIN),
  _dataType(INT_MIN),
  _lowerLeftCellX(INT_MIN),
  _lowerLeftCellY(INT_MIN),
  _numberOfCellsX(INT_MIN),
  _numberOfCellsY(INT_MIN),
  _cellSize(UNDEFINED_FLOAT),
  _compressionMethod(INT_MIN),
  _sizeofCompressedElements(INT_MIN),
  _compressionScaleFactor(UNDEFINED_FLOAT),
  _compressionBase(UNDEFINED_FLOAT),
  _maxDataValue(UNDEFINED_FLOAT),
  _minDataValue(UNDEFINED_FLOAT),
  _meanDataValue(UNDEFINED_FLOAT),
  _numberOfRanges(0)
{
  int i;
  for (i = 0; i<3; i++)
    _dataUnits[i] = 0;
  _infoFlatSize = sizeof(DSSGridInfoFlat);
  for (i = 0; i<20; i++) {
    _rangeLimitTable[i] = 0.0;
    _numberEqualOrExceedingRangeLimit[i] = 0;
  }
}

DSSGridInfoFlat::~DSSGridInfoFlat()
{
}


void DSSGridInfoFlat::show()
{
  std::cout << std::endl << " = = = GridInfoFlat = = =" << std::endl;
  std::cout << "infoFlatSize: " << _infoFlatSize << std::endl;
  std::cout << "gridType: " << _gridType << std::endl;
  std::cout << "infoSize: " << _infoSize << std::endl;
  std::cout << "gridInfoSize: " << _gridInfoSize << std::endl;
  std::cout << "startTime: " << _startTime << std::endl;
  std::cout << "endTime: " << _endTime << std::endl;
  char temp[13];
  temp[12] = '\0';
  int one = 1;
  int tweleve = 12;
  holchr_(_dataUnits, &one, &tweleve, temp, &one, (sizeof(temp) - 1));
  std::cout << "dataUnits: " << temp << std::endl;
  std::cout << "dataType: " << _dataType << std::endl;
  std::cout << "lowerLeftCellX: " << _lowerLeftCellX << std::endl;
  std::cout << "lowerLeftCellY: " << _lowerLeftCellY << std::endl;
  std::cout << "numberOfCellsX: " << _numberOfCellsX << std::endl;
  std::cout << "numberOfCellsY: " << _numberOfCellsY << std::endl;
  std::cout << "cellSize: " << _cellSize << std::endl;
  std::cout << "compressionMethod: " << _compressionMethod << std::endl;
  std::cout << "sizeofCompressedElements: " << _sizeofCompressedElements << std::endl;
  std::cout << "compressionScaleFactor: " << _compressionScaleFactor << std::endl;
  std::cout << "compressionBase: " << _compressionBase << std::endl;
  std::cout << "maxDataValue: " << _maxDataValue << std::endl;
  std::cout << "minDataValue: " << _minDataValue << std::endl;
  std::cout << "meanDataValue: " << _meanDataValue << std::endl;
  std::cout << "numberOfRanges: " << _numberOfRanges << std::endl;
  std::cout << "      RangeLimit       numberEqualOrExceedingRangeLimit " << std::endl;
  for (int i = 0; i<_numberOfRanges; i++) {
    std::cout << "  " << i << "   " << _rangeLimitTable[i] << "   "
      << _numberEqualOrExceedingRangeLimit[i] << std::endl;
  }
  std::cout << "====================================================" << std::endl;
}


