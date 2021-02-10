
// GridData.C


#include "pch.h"
#include <iomanip>
#include <iostream>
#include <string>
#include "DSSGridData.h"
#include "DSSGridInfo.h"
#include "assert.h"
DSSGridData::DSSGridData() {
  _data = NULL;
  _gridInfo = NULL;
}

DSSGridData::~DSSGridData() {
  if ( _data) 
    delete[] _data;
}

DSSGridData::DSSGridData(float *array, DSSGridInfo *gridInfo, bool deleteData = true) {
  _data = array;
  _gridInfo = gridInfo;
}

int
DSSGridData::initGridData(float *array, DSSGridInfo *gridInfo) {
	if( _data)
    delete[] _data;
  _data = array;
  _gridInfo = gridInfo;
  return 0;
}

void DSSGridData::show() {
  if (_data == NULL)  return;

  int x, y, nx, ny;
  x = _gridInfo->lowerLeftCellX();
  y = _gridInfo->lowerLeftCellY();
  nx = _gridInfo->numberOfCellsX();
  ny = _gridInfo->numberOfCellsY();

  std::cout << "Grid X base = " << x << std::endl;
  std::cout << "Grid Y base = " << y << std::endl;
  std::cout << "Grid X size = " << nx << std::endl;
  std::cout << "Grid Y size = " << ny << std::endl;
  std::cout << "Grid total size = " << nx*ny << std::endl << std::endl;
  std::cout << " X index | Y index |     Value" << std::endl;

  float v;

  for (int j = 0; j<ny; j++) {
    for (int i = 0; i<nx; i++) {
      v = _data[j*nx + i];
      std::cout << std::setw(8) << i + x
        << std::setw(10) << j + y;
      if (v == UNDEFINED_FLOAT)
        std::cout << "        NULL" << std::endl;
      else
        std::cout << std::setw(12) << v << std::endl;

    }
  }
  return;
}

void DSSGridData::showGraphic(int widthInCells) {

  int width;
  width = 72;
  if (widthInCells > 0) width = widthInCells;
  int x, y, nx, ny;
  x = _gridInfo->lowerLeftCellX();
  y = _gridInfo->lowerLeftCellY();
  nx = _gridInfo->numberOfCellsX();
  ny = _gridInfo->numberOfCellsY();

  std::cout << "Grid X base = " << x << std::endl;
  std::cout << "Grid Y base = " << y << std::endl;
  std::cout << "Grid X size = " << nx << std::endl;
  std::cout << "Grid Y size = " << ny << std::endl;
  std::cout << "Grid total size = " << nx*ny << std::endl << std::endl;

  int n, l, f;
  n = (nx - 1) / width + 1;
  nx = (nx / n) * n;
  ny = (ny / n) * n;

  float max, v;

  std::cout << "========================================" << std::endl;
  std::cout << "--- ";
  for (f = x; f<x + nx; f += n * 5) {
    std::cout << std::setw(5) << f;
  }
  std::cout << std::endl;

  std::cout << "hrapY";
  for (f = x; f<x + nx; f += n * 5) {
    std::cout << "  |  ";
  }
  std::cout << std::endl;





  for (int j = ny - n; j >= 0; j -= n) {
    std::cout << std::setw(5) << j + y << "  ";
    for (int i = 0; i<nx; i += n) {
      max = -2.0e38f;
      for (int jj = 0; jj<n; jj++) {
        for (int ii = 0; ii<n; ii++) {
          l = (j + jj)*nx + i + ii;
          //    if ( l > nx*ny ) std::cerr << std::endl << "l= " << l << std::endl;
          v = _data[l];
          if (v == UNDEFINED_FLOAT) v = -10.0f;
          if (v > max) max = v;
        }
      }
      int m;
      m = int(max);
      if (m < 0)             std::cout << ".";
      else if (m + 48 > 122)   std::cout << "#";
      else                     std::cout << (char)(m + 48);

    }
    std::cout << std::endl;
  }
  std::cout << "hrapY";
  for (f = x; f<x + nx; f += n * 5) {
    std::cout << "  |  ";
  }
  std::cout << std::endl;

  std::cout << "--- ";
  for (f = x; f<x + nx; f += n * 5) {
    std::cout << std::setw(5) << f;
  }
  std::cout << std::endl;


  std::cout << "========================================" << std::endl;

  return;
}

float DSSGridData::getGriddedValue(int xCoord, int yCoord,
  GridDataStatus *status) {
  if (_gridInfo == NULL) {
    *status = GRID_DATA_NO_RECORD;
    return UNDEFINED_FLOAT;
  }
  int position, x, y;
  x = xCoord - _gridInfo->lowerLeftCellX();
  y = yCoord - _gridInfo->lowerLeftCellY();

  if (x >= 0 && x < _gridInfo->numberOfCellsX() &&
    y >= 0 && y < _gridInfo->numberOfCellsY()) {
    position = y * _gridInfo->numberOfCellsX() + x;
    if (_data == NULL || _data[position] == UNDEFINED_FLOAT) {
      *status = GRID_DATA_NO_VALUE;
      return UNDEFINED_FLOAT;
    }
    else {
      *status = GRID_DATA_EXISTS;
    }
    return _data[position];
  }
  else {
    *status = GRID_DATA_NOT_WITHIN_RECORD;
    return UNDEFINED_FLOAT;
  }
}

float DSSGridData::getGriddedValue(float desiredCellSize, int xC, int yC,
  GridDataStatus *status) {
  if (_gridInfo == NULL) {
    *status = GRID_DATA_NO_RECORD;
    return UNDEFINED_FLOAT;
  }

  // Convert from grid coordinates at desired spacing to those
  //    at current spacing

  float ratio, xCoord, yCoord;

  ratio = desiredCellSize / _gridInfo->cellSize();

  xCoord =(float) int(((xC - 1) * ratio) + .001) + 1;
  yCoord =(float) int(((yC - 1) * ratio) + .001) + 1;

  int position, x, y;
  x = (int)xCoord - (int)_gridInfo->lowerLeftCellX();
  y = (int)yCoord - (int)_gridInfo->lowerLeftCellY();

  // Deal with all cells covered by desired cell size

  int istep;
  float sum;
  sum = 0.0;
  istep = int(ratio + .001);

  for (int iy = y; iy < y + istep; iy++) {
    for (int ix = x; ix < x + istep; ix++) {

      if (ix >= 0 && ix < _gridInfo->numberOfCellsX() &&
        iy >= 0 && iy < _gridInfo->numberOfCellsY()) {
        position = iy * _gridInfo->numberOfCellsX() + ix;
        if (_data == NULL || _data[position] == UNDEFINED_FLOAT) {
          *status = GRID_DATA_NO_VALUE;
          return UNDEFINED_FLOAT;
        }
        else {
          *status = GRID_DATA_EXISTS;
        }
        sum += _data[position];
      }
      else {
        *status = GRID_DATA_NOT_WITHIN_RECORD;
        return UNDEFINED_FLOAT;
      }
    }
  }
  if (istep < 1) istep = 1;
  return sum / (istep*istep);
}

float* DSSGridData::getAllGriddedValues(int *status) {

  *status = 0;
  return _data;
}

int DSSGridData::setGriddedValue(int xCoord, int yCoord, float value) {
  int position, x, y;
  x = xCoord - _gridInfo->lowerLeftCellX();
  y = yCoord - _gridInfo->lowerLeftCellY();

  if (x >= 0 && x < _gridInfo->numberOfCellsX() &&
    y >= 0 && y < _gridInfo->numberOfCellsY()) {
    position = y * _gridInfo->numberOfCellsX() + x;
    _data[position] = value;
    return 0;
  }
  else {
    return -1;
  }
}

int DSSGridData::updateStatistics() {

  int numDefined;
  float max, min, mean, sum;
  max = -2.0e38f;
  min = 2.0e38f;
  mean = UNDEFINED_FLOAT;
  sum = 0.0f;

  int i, j, k, n, m;
  int *count;
  float *range;

  m = _gridInfo->numberOfRanges();
  count = new int[m];
  range = _gridInfo->rangeLimitTable();
  for (n = 0; n<m; n++)
    count[n] = 0;
  numDefined = 0;

  int x, y;
  x = _gridInfo->numberOfCellsX();
  y = _gridInfo->numberOfCellsY();

  for (i = 0; i<x; i++) {
    for (j = 0; j<y; j++) {
      k = j * x + i;

      if (_data[k] != UNDEFINED_FLOAT) {
        numDefined++;
        sum += _data[k];
        if (_data[k] > max)  max = _data[k];
        if (_data[k] < min)  min = _data[k];
      }

      for (n = 0; n<m; n++)
        if (_data[k] >= range[n]) count[n]++;

    }
  }
  if (numDefined > 0) mean = sum / numDefined;
  else {
    max = UNDEFINED_FLOAT;
    min = UNDEFINED_FLOAT;
    mean = UNDEFINED_FLOAT;
  }

  _gridInfo->setDataInfo(max, min, mean);
  _gridInfo->setRangeInfo(m, range, count);
  delete[] count;
  return 0;
}

