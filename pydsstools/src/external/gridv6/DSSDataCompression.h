#pragma once
#include <fstream>
#include <stdlib.h>
#include "zlib.h"

#include "heclib.h"

class DSSDataCompression {

public:

  DSSDataCompression();

  virtual    ~DSSDataCompression();

  int     compress(short arrayin[], int sizein, short arrayout[],
    int &sizeout);

  int     uncompress(short arrayin[], int sizein, short *arrayout[],
    int &sizeout);

  int     compress(float *arrayin, int sizein,
    double compressionScaleFactor,
    double compressionBase,
    short * arrayout,
    int *sizeout) {
    for (int i = 0; i<sizein; i++) {
      if (arrayin[i] == UNDEFINED_FLOAT) {
        arrayout[i] = SHRT_MAX;
      }
      else {
        arrayout[i] = short((double(arrayin[i]) - compressionBase)
          * compressionScaleFactor);
      }
    }
    *sizeout = sizein * 4;
    return 0;
  };

  int     uncompress(short * arrayin, int sizein,
    double compressionScaleFactor,
    double compressionBase,
    float *arrayout,
    int *sizeout) {
    for (int i = 0; i<(sizein / 4); i++)
      if (arrayin[i] == SHRT_MAX) {
        arrayout[i] = UNDEFINED_FLOAT;
      }
      else {
        arrayout[i] =(float)( double(arrayin[i])*compressionScaleFactor
          + compressionBase);
      }
      *sizeout = sizein / 4;
      return 0;
  };

  int     compress(float *arrayin, int sizein,
    double compressionScaleFactor,
    double compressionBase,
    int *arrayout, int &bytesout);

  int     uncompress(int *arrayin, int bytesout,
    double compressionScaleFactor,
    double compressionBase,
    float *arrayout, int &sizeout);


  int     zcompress(float *arrayin, int sizein,
    int *arrayout, int &sizeout);

  int     zuncompress(int *arrayin, int sizein,
    float *arrayout, int &sizeout);

  int     zcompress(float *arrayin, int sizein,
    double compressionScaleFactor,
    double compressionBase,
    int *arrayout, int &sizeout);

  int     zuncompress(int *arrayin, int sizein,
    double compressionScaleFactor,
    double compressionBase,
    float *arrayout, int sizeout);

  static void   swapShorts(int* inArray, int intCount);

  static void   reverseByteOrder(int* inArray, int intCount);

  int     setLogFileName(std::ofstream *lfile);

  int     status();


protected:

private:

  std::ofstream *lfile;
  char logfilename[80];
  int trace;

};
