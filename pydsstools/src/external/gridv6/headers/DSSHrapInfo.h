#pragma once
#include "DSSGridInfo.h"

class DSSHrapInfoFlat;

class DSSHrapInfo : public DSSGridInfo {

public:

  DSSHrapInfo();
  ~DSSHrapInfo();
  void show();
  void setDataSource(const char *source) { _dataSource.erase(0); _dataSource.append(source); }
  const char *getDataSource() { return _dataSource.data(); }
  int setDataSource(std::string dataSource);
  int setCellInfo(int lowerLeftCellX, int lowerLeftCellY,
    int numberOfCellsX, int numberOfCellsY,
    float cellSize);

  std::string   dataSource() { return  _dataSource; };

  DSSHrapInfoFlat* makeGridInfoFlat();
  int loadFlatData(DSSHrapInfoFlat* hrapInfoFlat);
  int convertToGridInfo(DSSGridInfoFlat* hrapInfoFlat);

  bool sameGISframework(DSSHrapInfo* a, bool showWhyNot);
  bool sameDataParameter(DSSHrapInfo* a, bool showWhyNot);
  bool sameCellCoverage(DSSHrapInfo* a, bool showWhyNot);
  bool canMosaic(DSSHrapInfo* a, bool showWhyNot);
  bool canAddCells(DSSHrapInfo* a, bool showWhyNot);
  bool canOverlayCells(DSSHrapInfo* a, bool showWhyNot);

  friend std::ostream& operator<<(std::ostream&, DSSHrapInfo&);

protected:

  std::string   _dataSource;

private:

};
