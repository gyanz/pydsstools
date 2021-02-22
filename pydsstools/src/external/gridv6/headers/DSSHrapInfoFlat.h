#pragma once
// HrapInfoFlat.h

#ifndef DSS_HRAP_INFO_FLAT_H
#define DSS_HRAP_INFO_FLAT_H

#include "DSSGridInfoFlat.h"

class DSSHrapInfo;

class DSSHrapInfoFlat : public DSSGridInfoFlat {

public:

  friend class DSSHrapInfo;

  DSSHrapInfoFlat();
  ~DSSHrapInfoFlat() {};

  void            show();


private:

  int      _dataSource[3];

};
#endif // HRAP_INFO_FLAT_H


