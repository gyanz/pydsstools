#pragma once
#include "DSSGridInfoFlat.h"

class DSSAlbersInfo;

class DSSAlbersInfoFlat : public DSSGridInfoFlat {

public:

  friend class DSSAlbersInfo;

  DSSAlbersInfoFlat();
  ~DSSAlbersInfoFlat() {};

  void            show();


private:

  int             _projectionDatum;
  int             _projectionUnits[3];
  float           _firstStandardParallel;
  float           _secondStandardParallel;
  float           _centralMeridian;
  float           _latitudeOfProjectionOrigin;
  float           _falseEasting;
  float           _falseNorthing;
  float           _xCoordOfGridCellZero;
  float           _yCoordOfGridCellZero;

};

