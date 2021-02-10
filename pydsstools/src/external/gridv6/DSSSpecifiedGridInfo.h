#pragma once
/*
* The SpecifiedGridInfo class inherits from GridInfo, extending the grid metadata to support
* any coordinate system, and adding new metadata fields that HEC has determined would
* be useful since the original GridInfo was defined in 1994.
*
* The new data fields are:
*   _srsName (String) The name of the spatial reference system (SRS) for the grid.
*   _srsDefinition (String) A complete spatial reference identifier in a text
*         of arbitrary length.  For present use, we are populating this field
*         with a Spatial Reference Identifier in well-known text (WKT) format.
*   _xCoordOfGridCellZero (float) The x coordinate value, in the SRS, of the
*         lower left corner (not the center) of cell (0, 0).
*   _yCoordOfGridCellZero (float) The y coordinate value, in the SRS, of the
*         lower left corner (not the center) of cell (0, 0).
*   _nullValue (float) the value used in the grid's data array to represent a "no data"
*         cell.
*   _timeZoneID (String) a name for the time zone that applies to the data in the grid.
*   _timeZoneRawOffset (int) Offset in milliseconds from UTC.
*   _isTimeStamped (boolean) false for data that is time-invariant (e.g. grids of
*         stable parameters, like ground elevation).
*   _isTSElement (boolean) false for data that is time-invariant (e.g. grids of
*         stable parameters, like ground elevation).
*   _isInterval (boolean) false for instantaneous values, true for period data.
*
* In addition, the GridInfo version number is explicitly stored in the header of the
* DSS record, and the compression method defaults to ZLIB's deflate method
*
* @author Tom Evans November 2011
*
*/

#ifndef SPECIFIED_GRID_INFO_H
#define SPECIFIED_GRID_INFO_H

#include "DSSGridInfo.h"
class DSSSpecifiedGridInfoFlat;

class DSSSpecifiedGridInfo : public DSSGridInfo {

public:

  DSSSpecifiedGridInfo();
  DSSSpecifiedGridInfo(int gridType);
  ~DSSSpecifiedGridInfo();
  void show();
  int setSpatialReference(
    std::string srsName,
    std::string srsDefinition,
    float xOrigin,
    float yOrigin
  );

  float   xCoordinateOfGridCellZero() { return       _xCoordinateOfGridCellZero; }
  float   yCoordinateOfGridCellZero() { return       _yCoordinateOfGridCellZero; }
  float   getNullValue() { return       _nullValue; }
  std::string srsName() { return       _srsName; };
  std::string srsDefinition() { return       _srsDefinition; };
  int srsDefinitionType() { return       _srsDefinitionType; };
  std::string timeZoneID() { return       _timeZoneID; };
  int timeZoneRawOffset() { return _timeZoneRawOffset; };
  bool isInterval() { return (_isInterval ); };
  bool isTimeStamped() { return (_isTimeStamped ); };

  DSSSpecifiedGridInfoFlat* makeGridInfoFlat();
  int loadFlatData(DSSSpecifiedGridInfoFlat* SpecifiedGridInfoFlat);
  int convertToGridInfo(DSSGridInfoFlat* SpecifiedGridInfoFlat);

  

protected:
  static const int SPECIFIED_GRID_INFO_VERSION = 2; //
  int _version;
  std::string _srsName;
  // for now we're using WKT strings for the SRS definitions, but
  // here's a placeholder for future options like proj4 or GML
  int _srsDefinitionType;
  std::string _srsDefinition;
  float _xCoordinateOfGridCellZero;
  float _yCoordinateOfGridCellZero;
  float _nullValue;
  std::string _timeZoneID;
  int _timeZoneRawOffset;
  bool _isInterval;
  bool _isTimeStamped;

};
#endif // SPECIFIED_GRID_INFO_H
