#include "pch.h"
#include "DSSAlbersInfo.h"
#include <string>
#include <iostream>
#include "DSSAlbersInfoFlat.h"
#include "DssUtility.h"
extern "C"
{
  #include "heclib.h"
}

using namespace std;

DSSAlbersInfo::DSSAlbersInfo() :DSSGridInfo(DATA_TYPE_AGT) {

  _infoSize = 164;
  _gridInfoSize = 124;
  _projectionDatum = UNDEFINED_PROJECTION_DATUM;
  _firstStandardParallel = UNDEFINED_FLOAT;
  _secondStandardParallel = UNDEFINED_FLOAT;
  _centralMeridian = UNDEFINED_FLOAT;
  _latitudeOfProjectionOrigin = UNDEFINED_FLOAT;
  _falseEasting = UNDEFINED_FLOAT;
  _falseNorthing = UNDEFINED_FLOAT;
  _xCoordOfGridCellZero = UNDEFINED_FLOAT;
  _yCoordOfGridCellZero = UNDEFINED_FLOAT;

}

DSSAlbersInfo::DSSAlbersInfo(int gridType) : DSSGridInfo(gridType)
{
}

DSSAlbersInfo::~DSSAlbersInfo()
{
}

void DSSAlbersInfo::show()
{

  std::cout << std::endl << " = = = AlbersInfo = = =" << std::endl;
  std::cout << "projectionDatum: " << (int)_projectionDatum << std::endl;
  std::cout << "projectionUnits: " << _projectionUnits << std::endl;
  std::cout << "firstStandardParallel: " << _firstStandardParallel << std::endl;
  std::cout << "secondStandardParallel: " << _secondStandardParallel << std::endl;
  std::cout << "centralMeridian: " << _centralMeridian << std::endl;
  std::cout << "latitudeOfProjectionOrigin: " << _latitudeOfProjectionOrigin << std::endl;
  std::cout << "falseEasting: " << _falseEasting << std::endl;
  std::cout << "falseNorthing: " << _falseNorthing << std::endl;
  std::cout << "xCoordOfGridCellZero: " << _xCoordOfGridCellZero << std::endl;
  std::cout << "yCoordOfGridCellZero: " << _yCoordOfGridCellZero << std::endl;

  DSSGridInfo::show();
}

int DSSAlbersInfo::setProjectionInfo(
  ProjectionDatum projectionDatum,
  std::string projectionUnits,
  float firstStandardParallel,
  float secondStandardParallel,
  float centralMeridian,
  float latitudeOfProjectionOrigin,
  float falseEasting,
  float falseNorthing,
  float xCoordOfGridCellZero,
  float yCoordOfGridCellZero) {


  _projectionDatum = projectionDatum;
  _projectionUnits = projectionUnits;
  _firstStandardParallel = firstStandardParallel;
  _secondStandardParallel = secondStandardParallel;
  _centralMeridian = centralMeridian;
  _latitudeOfProjectionOrigin = latitudeOfProjectionOrigin;
  _falseEasting = falseEasting;
  _falseNorthing = falseNorthing;
  _xCoordOfGridCellZero = xCoordOfGridCellZero;
  _yCoordOfGridCellZero = yCoordOfGridCellZero;

  return 0;

}

int DSSAlbersInfo::copyProjectionInfo(
  DSSAlbersInfo inInfo) {


  _projectionDatum = inInfo.projectionDatum();
  _projectionUnits = inInfo.projectionUnits();
  _firstStandardParallel = inInfo.firstStandardParallel();
  _secondStandardParallel = inInfo.secondStandardParallel();
  _centralMeridian = inInfo.centralMeridian();
  _latitudeOfProjectionOrigin = inInfo.latitudeOfProjectionOrigin();
  _falseEasting = inInfo.falseEasting();
  _falseNorthing = inInfo.falseNorthing();
  _xCoordOfGridCellZero = inInfo.xCoordOfGridCellZero();
  _yCoordOfGridCellZero = inInfo.yCoordOfGridCellZero();

  return 0;

}


DSSAlbersInfoFlat* DSSAlbersInfo::makeGridInfoFlat() {

  DSSAlbersInfoFlat *a;
  a = new DSSAlbersInfoFlat();

  DSSGridInfo::loadFlatData(a);
  DSSAlbersInfo::loadFlatData(a);

  return a;
}

int DSSAlbersInfo::loadFlatData(DSSAlbersInfoFlat* a) {

  a->_projectionDatum = _projectionDatum;

  char  * temp = new char[13];
  for (int i = 0; i<13; i++)
    temp[i] = '\0';
  strncpy(temp, _projectionUnits.c_str(), 12);
  int one = 1;
  int tweleve = 12;
  chrhol_(temp, &one, &tweleve, a->_projectionUnits, &one, (sizeof(temp) - 1));


  a->_firstStandardParallel = _firstStandardParallel;
  a->_secondStandardParallel = _secondStandardParallel;
  a->_centralMeridian = _centralMeridian;
  a->_latitudeOfProjectionOrigin = _latitudeOfProjectionOrigin;
  a->_falseEasting = _falseEasting;
  a->_falseNorthing = _falseNorthing;
  a->_xCoordOfGridCellZero = _xCoordOfGridCellZero;
  a->_yCoordOfGridCellZero = _yCoordOfGridCellZero;

  return 0;
}

int DSSAlbersInfo::convertToGridInfo(DSSGridInfoFlat* a1) {
  DSSGridInfo::convertToGridInfo(a1);

  DSSAlbersInfoFlat *a = (DSSAlbersInfoFlat*)a1;

  _projectionDatum = (ProjectionDatum)a->_projectionDatum;

  char temp[13];
  temp[12] = '\0';
  int one = 1;
  int tweleve = 12;
  holchr_(a->_projectionUnits, &one, &tweleve, temp, &one, (sizeof(temp) - 1));

  _projectionUnits = temp;
  _firstStandardParallel = a->_firstStandardParallel;
  _secondStandardParallel = a->_secondStandardParallel;
  _centralMeridian = a->_centralMeridian;
  _latitudeOfProjectionOrigin = a->_latitudeOfProjectionOrigin;
  _falseEasting = a->_falseEasting;
  _falseNorthing = a->_falseNorthing;
  _xCoordOfGridCellZero = a->_xCoordOfGridCellZero;
  _yCoordOfGridCellZero = a->_yCoordOfGridCellZero;
  //show();//not getting here for some reason
  return 0;
}
bool DSSAlbersInfo::sameGISframework(DSSAlbersInfo* a) {


	return DSSGridInfo::sameGISframework(a)
		&& _projectionDatum == a->projectionDatum()
		&& _projectionUnits == a->projectionUnits()
		&& _firstStandardParallel == a->firstStandardParallel()
		&& _secondStandardParallel == a->secondStandardParallel()
		&& _centralMeridian == a->centralMeridian()
		&& _latitudeOfProjectionOrigin == a->latitudeOfProjectionOrigin()
		&& _falseEasting == a->falseEasting()
		&& _falseNorthing == a->falseNorthing()
		&& _xCoordOfGridCellZero == a->xCoordOfGridCellZero()
		&& _yCoordOfGridCellZero == a->yCoordOfGridCellZero();
}


string DSSAlbersInfo::getSpatialReferenceSystem() {
	string temp;
	bool isSHG = false;
	
	if (_projectionDatum ==NAD_83 && DssUtility::StringsEqualIgnoreCase( _projectionUnits,"meters")
		&& _firstStandardParallel == 29.5f && _secondStandardParallel == 45.5f
		&&  _centralMeridian == -96.0f && _latitudeOfProjectionOrigin == 23.0f
		&& _falseEasting == 0.0f && _falseNorthing == 0.0f
		&& _xCoordOfGridCellZero == 0.0 && _yCoordOfGridCellZero == 0.0f)
		isSHG = true;

	if (isSHG) {
		return SHG_SRC_DEFINITION;
	}
	else {
		return "";
	}
}
