#pragma once
#include "DSSGridInfo.h"

enum GridDataStatus {
  GRID_DATA_EXISTS = 0,
  GRID_DATA_NO_VALUE = -1,
  GRID_DATA_NOT_WITHIN_RECORD = -2,
  GRID_DATA_NO_RECORD = -3,
  GRID_DATA_EST_VALUE = 1
};

class DSSGridData {

public:
  DSSGridData();
  DSSGridData(float *array, DSSGridInfo *gridInfo, bool deleteData);
  virtual ~DSSGridData();
  int initGridData(float *array, DSSGridInfo *gridInfo);
  void show();
  void showGraphic(int widthInCells);
  DSSGridInfo *getGridInfo() { return _gridInfo; };
  float getGriddedValue(int xCoord, int yCoord, GridDataStatus *status);
  float getGriddedValue(float desiredCellSize, int xCoord, int yCoord,
    GridDataStatus *status);
  float* getAllGriddedValues(int *status);
  int setGriddedValue(int xCoord, int yCoord, float value);
  int updateStatistics();

protected:

  float *_data;
  DSSGridInfo *_gridInfo;

private:

};
