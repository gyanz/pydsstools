#include "pch.h"
#include "DSSHrapInfoFlat.h"
#include "DSSGridInfoFlat.h"
extern "C"
{
  #include "heclib.h"
}
DSSHrapInfoFlat::DSSHrapInfoFlat() : DSSGridInfoFlat()
{
  for (int i = 0; i<3; i++)
    _dataSource[i] = 0;

  _infoFlatSize = sizeof(DSSHrapInfoFlat);
}


void DSSHrapInfoFlat::show()
{

  std::cout << std::endl << " = = = HrapInfoFlat = = =" << std::endl;
  char temp[13];
  temp[12] = '\0';
  int one = 1;
  int tweleve = 12;
  holchr_(_dataSource, &one, &tweleve, temp, &one, (sizeof(temp) - 1));
  std::cout << "dataSource: " << temp << std::endl;

  DSSGridInfoFlat::show();

}