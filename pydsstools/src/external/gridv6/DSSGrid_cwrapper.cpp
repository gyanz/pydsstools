#include "DSSGrid.h"

#ifdef __cplusplus
extern "C" {
#endif
int _RetrieveGriddedData(long long * ifltab, zStructSpatialGrid * gs, int boolRetrieveData); 
#ifdef __cplusplus
}
#endif

//using DSSGrid;

int _RetrieveGriddedData(long long * ifltab, zStructSpatialGrid * gs, int boolRetrieveData) {
    int status;
    status = DSSGrid::RetrieveGriddedData(ifltab,gs,boolRetrieveData);
    return status; 
}
