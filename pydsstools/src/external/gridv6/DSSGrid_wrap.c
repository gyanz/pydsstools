#include "heclib.h"
int _RetrieveGriddedData(long long * ifltab, zStructSpatialGrid * gs, int boolRetrieveData);

int RetrieveGriddedData_wrap(long long * ifltab, zStructSpatialGrid * gs, int boolRetrieveData) {
    int status;
    status = _RetrieveGriddedData(ifltab,gs,boolRetrieveData);
    return status; 
}
