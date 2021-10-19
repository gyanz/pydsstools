#include "pch.h"
#include "DSSHrapInfo.h"
#include "DSSHrapInfoFlat.h"
#include <string>
#include <iostream>
extern "C"
{
  #include "heclib.h"
}
// HrapInfo.C




DSSHrapInfo::DSSHrapInfo() :DSSGridInfo(DATA_TYPE_HGT) {

  _infoSize = 128;
  _gridInfoSize = 124;
}

DSSHrapInfo::~DSSHrapInfo()
{
}

int DSSHrapInfo::setCellInfo(int lowerLeftCellX, int lowerLeftCellY,
  int numberOfCellsX, int numberOfCellsY,
  float cellSize)
{

  cellSize = 4762.5;
  DSSGridInfo::setCellInfo(lowerLeftCellX, lowerLeftCellY,
    numberOfCellsX, numberOfCellsY,
    cellSize);
  return 0;
}


void DSSHrapInfo::show()
{

  std::cout << std::endl << " = = = HrapInfo = = =" << std::endl;
  std::cout << "dataSource: " << _dataSource << std::endl;

  DSSGridInfo::show();
}

int DSSHrapInfo::setDataSource(std::string dataSource) {

  _dataSource = dataSource;

  return 0;

}

DSSHrapInfoFlat* DSSHrapInfo::makeGridInfoFlat() {

  DSSHrapInfoFlat *a;
  a = new DSSHrapInfoFlat();

  DSSGridInfo::loadFlatData(a);
  DSSHrapInfo::loadFlatData(a);

  return a;
}

int DSSHrapInfo::loadFlatData(DSSHrapInfoFlat* hrapInfoFlat) {

  char  * temp = new char[13];
  for (int i = 0; i<13; i++)
    temp[i] = '\0';
  strncpy(temp, _dataSource.c_str(), 12);
  int one = 1;
  int tweleve = 12;
  chrhol_(temp, &one, &tweleve, hrapInfoFlat->_dataSource, &one,
    (sizeof(temp) - 1));


  return 0;
}

int DSSHrapInfo::convertToGridInfo(DSSGridInfoFlat* a) {

  DSSGridInfo::convertToGridInfo(a);

  char temp[13];
  temp[12] = '\0';
  int one = 1;
  int tweleve = 12;
  holchr_(((DSSHrapInfoFlat *)a)->_dataSource, &one, &tweleve,
    temp, &one, (sizeof(temp) - 1));
  _dataSource = temp;
  return 0;
}

std::ostream& operator<<(std::ostream& os, DSSHrapInfo& h) {
  os << std::endl << " = = = HrapInfo = = =" << std::endl;
  os << "Data Source: " << h._dataSource << std::endl;
  h.DSSGridInfo::print(os);
  return os;
}


