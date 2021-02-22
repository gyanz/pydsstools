#pragma once
#include "DSSGridInfo.h"

class DSSAlbersInfoFlat;

class DSSAlbersInfo : public DSSGridInfo {

public:

  DSSAlbersInfo();
  DSSAlbersInfo(int gridType);
  ~DSSAlbersInfo();
  void show();
  int setProjectionInfo(
    ProjectionDatum projectionDatum,
    std::string projectionUnits,
    float firstStandardParallel,
    float secondStandardParallel,
    float centralMeridian,
    float latitudeOfProjectionOrigin,
    float falseEasting,
    float falseNorthing,
    float xCoordOfGridCellZero,
    float yCoordOfGridCellZero);
  int copyProjectionInfo(DSSAlbersInfo);


  int projectionDatum() { return         _projectionDatum; };
  std::string   projectionUnits() { return            _projectionUnits; };
  float   firstStandardParallel() { return      _firstStandardParallel; };
  float   secondStandardParallel() { return     _secondStandardParallel; };
  float   centralMeridian() { return            _centralMeridian; };
  float   latitudeOfProjectionOrigin() { return _latitudeOfProjectionOrigin; };
  float   falseEasting() { return               _falseEasting; }
  float   falseNorthing() { return              _falseNorthing; }
  float   xCoordOfGridCellZero() { return       _xCoordOfGridCellZero; }
  float   yCoordOfGridCellZero() { return       _yCoordOfGridCellZero; }

  DSSAlbersInfoFlat* makeGridInfoFlat();
  int loadFlatData(DSSAlbersInfoFlat* albersInfoFlat);
  int convertToGridInfo(DSSGridInfoFlat* albersInfoFlat);

  bool sameGISframework(DSSAlbersInfo* a);

 std::string getSpatialReferenceSystem();

protected:
  int _projectionDatum;
  std::string   _projectionUnits;
  float   _firstStandardParallel;
  float   _secondStandardParallel;
  float   _centralMeridian;
  float   _latitudeOfProjectionOrigin;
  float   _falseEasting;
  float   _falseNorthing;
  float   _xCoordOfGridCellZero;
  float   _yCoordOfGridCellZero;


};
