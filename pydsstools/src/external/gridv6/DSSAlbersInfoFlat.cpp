#include "pch.h"
#include "DSSAlbersInfoFlat.h"
extern "C"
{
  #include "heclib.h"
}

DSSAlbersInfoFlat::DSSAlbersInfoFlat() : DSSGridInfoFlat(),
_projectionDatum(INT_MIN),
_firstStandardParallel(UNDEFINED_FLOAT),
_secondStandardParallel(UNDEFINED_FLOAT),
_centralMeridian(UNDEFINED_FLOAT),
_latitudeOfProjectionOrigin(UNDEFINED_FLOAT),
_falseEasting(UNDEFINED_FLOAT),
_falseNorthing(UNDEFINED_FLOAT),
_xCoordOfGridCellZero(UNDEFINED_FLOAT),
_yCoordOfGridCellZero(UNDEFINED_FLOAT)

{
  for (int i = 0; i<3; i++)
    _projectionUnits[i] = 0;

  _infoFlatSize = sizeof(DSSAlbersInfoFlat);
}


void DSSAlbersInfoFlat::show()
{

  std::cout << std::endl << " = = = AlbersInfoFlat = = =" << std::endl;
  std::cout << "projectionDatum : " << _projectionDatum << std::endl;
  char temp[13];
  temp[12] = '\0';
  int one = 1;
  int tweleve = 12;
  holchr_(_projectionUnits, &one, &tweleve, temp, &one, (sizeof(temp) - 1));
  std::cout << "projectionUnits: " << temp << std::endl;
  std::cout << "firstStandardParallel: " << _firstStandardParallel << std::endl;
  std::cout << "secondStandardParallel: " << _secondStandardParallel << std::endl;
  std::cout << "centralMeridian: " << _centralMeridian << std::endl;
  std::cout << "latitudeOfProjectionOrigin: " << _latitudeOfProjectionOrigin << std::endl;
  std::cout << "falseEasting: " << _falseEasting << std::endl;
  std::cout << "falseNorthing: " << _falseNorthing << std::endl;
  std::cout << "xCoordOfGridCellZero: " << _xCoordOfGridCellZero << std::endl;
  std::cout << "yCoordOfGridCellZero: " << _yCoordOfGridCellZero << std::endl;

  DSSGridInfoFlat::show();
}

