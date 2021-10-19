#include "pch.h"
#include "DSSDataCompression.h"
#include <string>
#include <iostream>

//
//=============================================================================
// Name: DataCompression ()
//
// Description: Class to compress and uncompress spatial precipitation
//              data retrieved from Stage I and Stage III radar products
//
//
// Author: Carl Franke
// Date: 08 Aug. 1994
//=============================================================================
//

DSSDataCompression::DSSDataCompression()
{
#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_1)
  //     std::cerr << "===>Entering DataCompression::DataCompression()" << std::endl;
#endif
  //  *lfile << "DataCompression - constructer member function" << std::endl;

  trace = 0;

}

//
//=============================================================================
// Name: ~DataCompression()
//
// Description: Destructor for Data Compression class
//
//
// Author: Carl Franke
// Date: 08 Aug. 1994
//=============================================================================
//

DSSDataCompression::~DSSDataCompression()
{
#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_1)
  //      std::cerr << "===>Entering DataCompression::~DataCompression ()" << std::endl;
#endif
  if (trace == 1) {
    *lfile << "DataCompression - destructer member function" << std::endl;
  }
}



//=============================================================================
// Name: compress ( short arrayin[], int sizein, short arrayout[],
//                  int &sizeout )
//
// Description: Compress Stage I and Stage III Spatial Precipitation Data
//
// Arguments:
//
//
// Author: Carl Franke
// Date: 08 Aug 1994
//=============================================================================
//

int
DSSDataCompression::compress(short arrayin[], int sizein, short arrayout[],
  int &sizeout)
{
#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_2) {
  //      std::cerr << "===>Entering DataCompression::compress ()" << std::endl;
  //  }
#endif

  if (trace == 1) {
    *lfile << "DataCompression - compress member function" << std::endl << std::endl;
    *lfile << "size of int:       " << sizeof(int) << std::endl;
    *lfile << "size of short:     " << sizeof(short) << std::endl;
    *lfile << "size of char:      " << sizeof(char) << std::endl << std::endl;
  }

  /* The PRECIP_2_BYTE method is messy on PCs because we're reading an array of
  shorts (two bytes each) that was stored as an array of ints (four bytes
  each) in DSS.  The method was developed on a UNIX (big endian) system,
  and since DSS reverses the order of the bytes in ints when they're stored,
  this causes some problems when they're read out of DSS on a PC.  If you
  look at two shorts in hex they look like this

  UNIX: 0x01E9 0x023C (2 shorts, big endian)
  UNIX: 0x01E9023C    (1 int, big endian)
  PC:   0xC3209E10    (1 int, little endian)
  PC:   0xC320 0x9E10 (2 shorts, little endian, order reversed)

  On little endian (PC) systems, the shorts have the correct values, but
  the order of the shorts within an int is reversed.  We have to swap bytes
  0 and 1 with bytes 2 and three to get them out in the correct order. */

  // This only happens on PCs
#ifdef _MSC_VER
  swapShorts((int*)arrayin, (sizein + 3) / 4);
#endif

  // Declare all counters used by the "compress" member function

  // zerocount  - running count of one or more sequential 0's
  // minuscount - running count of one or more sequential -1's
  // totalzeros - total number of 0's found in data array
  // totalones  - total number of -1's found in data array
  // totalvals  - total number of non-zero data values found in data array
  // count      - counter used to increment through array elements


  int count, newcount, repeatvals;
  int totalzeros, totalones, totalvals, totalsize;

  count = 0;
  newcount = 0;
  totalzeros = 0;
  totalones = 0;
  totalvals = 0;

  while (count < sizein) {

    *lfile << "sizein: " << sizein << std::endl;

    if (arrayin[count] == 0) {
      repeatvals = 0;
      while (arrayin[count] == 0 && count < sizein) {
        repeatvals++;
        count++;
      }
      if (repeatvals < 16000) {
        totalzeros = totalzeros + repeatvals;
        arrayout[newcount] = repeatvals | 0x8000;
        if (trace == 1) {
          *lfile << "#" << newcount << "   0's: " << repeatvals << std::endl;
        }
      }
      else {
        *lfile << "Caution - " << repeatvals << " repeated 0's" << std::endl;

        while (repeatvals >= 16000) {
          totalzeros = totalzeros + 16000;
          arrayout[newcount] = short(16000 | 0x8000);
          if (trace == 1) {
            *lfile << "#" << newcount << "   0's: " << "16000" << std::endl;
          }
          newcount++;
          repeatvals = repeatvals - 16000;
        }

        totalzeros = totalzeros + repeatvals;
        arrayout[newcount] = repeatvals | 0x8000;
        if (trace == 1) {
          *lfile << "#" << newcount << "   0's: " << repeatvals << std::endl;
        }
      }
    }

    else if (arrayin[count] == -1) {
      repeatvals = 0;
      while (arrayin[count] == -1 && count < sizein) {
        repeatvals++;
        count++;
      }
      if (repeatvals < 16000) {
        totalones = totalones + repeatvals;
        arrayout[newcount] = repeatvals | 0xC000;
        if (trace == 1) {
          *lfile << "#" << newcount << "  -1's: " << repeatvals << std::endl;
        }
      }
      else {
        if (trace == 1) {
          *lfile << "Caution - " << repeatvals << " repeated -1's";
          *lfile << std::endl;
        }

        while (repeatvals >= 16000) {
          totalones = totalones + 16000;
          arrayout[newcount] = short(16000 | 0xC000);
          if (trace == 1) {
            *lfile << "#" << newcount << "  -1's: " << "16000" << std::endl;
          }
          newcount++;
          repeatvals = repeatvals - 16000;
        }

        totalones = totalones + repeatvals;
        arrayout[newcount] = repeatvals | 0xC000;
        if (trace == 1) {
          *lfile << "#" << newcount << "  -1's: " << repeatvals << std::endl;
        }
      }
    }

    else {
      arrayout[newcount] = arrayin[count];
      if (trace == 1) {
        *lfile << "#" << newcount << "   val: " << arrayin[count] << std::endl;
      }
      count++;
      totalvals++;
    }
    newcount++;
  }

  sizeout = newcount;
  totalsize = totalzeros + totalones + totalvals;

  if (trace == 1) {

    *lfile << std::endl;
    *lfile << "Total    0's found: " << totalzeros << std::endl;
    *lfile << "Total   -1's found: " << totalones << std::endl;
    *lfile << "Total values found: " << totalvals << std::endl;
    *lfile << "-----               " << "------" << std::endl;
    *lfile << "Total:              " << totalsize << std::endl;
    *lfile << std::endl;

    if (totalsize != sizein) {
      *lfile << "Caution - totalzise and sizein do not agree" << std::endl;
    }

    *lfile << "size of input array (uncompressed): " << sizein << std::endl;
    *lfile << "size of output array (compressed):  " << sizeout << std::endl;
    *lfile << std::endl;

    //     *lfile << "Compressed integer array follows: " << std::endl << std::endl;
    //     for ( count = 0 ; count < sizeout ; count++ ) {
    //        *lfile << "arrayout[" << count << "]  "<< arrayout[count] << std::endl;
    //     }
    //     *lfile << std::endl;

  }

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_3)
  //     std::cerr << "===>Exiting  DataCompression::compress ()" << std::endl;
#endif
  return 0;
}


//=============================================================================
// Name: uncompress ( short arrayin[], int sizein, short *arrayout[],
//                    int &sizeout )
//
// Description: Uncompress Stage I and Stage III Spatial Precipitation Data
//
// Arguments:
//
//
// Author: Carl Franke
// Date: 08 Aug. 1994
//=============================================================================
//

int
DSSDataCompression::uncompress(short arrayin[], int sizein, short *arryptr[],
  int &sizeout)
{

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_2) {
  //      std::cerr << "===>Entering DataCompression::uncompress ()" << std::endl;
  //  }
#endif

  trace = 1;
  if (trace == 1) {
    *lfile << "DataCompression - uncompress member function" << std::endl << std::endl;
    *lfile << "size of int:       " << sizeof(int) << std::endl;
    *lfile << "size of short:     " << sizeof(short) << std::endl;
    *lfile << "size of char:      " << sizeof(char) << std::endl << std::endl;
  }

  /* The PRECIP_2_BYTE method is messy on PCs because we're reading an array of
  shorts (two bytes each) that was stored as an array of ints (four bytes
  each) in DSS.  The method was developed on a UNIX (big endian) system,
  and since DSS reverses the order of the bytes in ints when they're stored,
  this causes some problems when they're read out of DSS on a PC.  If you
  look at two shorts in hex they look like this

  UNIX: 0x01E9 0x023C (2 shorts, big endian)
  UNIX: 0x01E9023C    (1 int, big endian)
  PC:   0xC3209E10    (1 int, little endian)
  PC:   0xC320 0x9E10 (2 shorts, little endian, order reversed)

  On little endian (PC) systems, the shorts have the correct values, but
  the order of the shorts within an int is reversed.  We have to swap bytes
  0 and 1 with bytes 2 and three to get them out in the correct order.*/

  // This only happens on PCs
#ifdef _MSC_VER
  swapShorts((int*)arrayin, (sizein + 3) / 4);
#endif

  int totalzeros, totalones, totalvals, totalsize;
  int count, newcount, k;
  int istat;

  short repeatvals, *arrayout;

  totalzeros = 0;
  totalones = 0;
  totalvals = 0;
  newcount = 0;
  count = 0;

  arrayout = new short[100000];

  if (trace == 1) {
    *lfile << "Starting to uncompress Data: " << std::endl;
    *lfile << "Sizein:  " << sizein << std::endl << std::endl;
  }

  while (count < sizein) {

    if (trace == 1) {
      *lfile << arrayin[count] << std::endl;
    }

    if ((arrayin[count] & 0xC000) == 0x0000) {
      arrayout[newcount] = arrayin[count];
      totalvals++;
      if (trace == 1) {
        *lfile << "#" << count << "   Data: " << arrayout[newcount];
        *lfile << std::endl;
      }
      newcount++;
    }
    else if ((arrayin[count] & 0xC000) == 0x8000) {
      repeatvals = arrayin[count] & 0x3FFF;
      totalzeros = totalzeros + repeatvals;
      if (trace == 1) {
        *lfile << "#" << count << "    0's: " << repeatvals << std::endl;
      }
      for (k = newcount; k < newcount + repeatvals; k++) {
        arrayout[k] = 0;
      }
      newcount = newcount + repeatvals;
    }
    else if ((arrayin[count] & 0xC000) == 0xC000) {
      repeatvals = arrayin[count] & 0x3FFF;
      totalones = totalones + repeatvals;
      if (trace == 1) {
        *lfile << "#" << count << "   -1's: " << repeatvals << std::endl;
      }
      for (k = newcount; k < newcount + repeatvals; k++) {
        arrayout[k] = -1;
      }
      newcount = newcount + repeatvals;
    }
    else {
      if (trace == 1) {
        *lfile << "error uncompressing data" << std::endl;
      }
    }
    count++;
  }

  sizeout = newcount;
  totalsize = totalzeros + totalones + totalvals;

  if (trace == 1) {

    *lfile << std::endl;
    *lfile << "Total    0's found: " << totalzeros << std::endl;
    *lfile << "Total   -1's found: " << totalones << std::endl;
    *lfile << "Total values found: " << totalvals << std::endl;
    *lfile << "-----               " << "------" << std::endl;
    *lfile << "Total:              " << totalsize << std::endl;
    *lfile << std::endl;

    //     for ( count = 0 ; count < newcount ; count++ ) {
    //        *lfile << "arrayout[" << count << "]  " << arrayout[count] << std::endl;
    //     }

  }

  sizeout = totalzeros + totalones + totalvals;

  if (trace == 1) {
    *lfile << "uncompress - sizeout: " << sizeout << std::endl;
  }

  if (sizeout > 20 && trace == 1) {

    *lfile << "Uncompressed integer array follows: " << std::endl << std::endl;
    for (count = 0; count < 11; count++) {
      *lfile << "arrayout[" << count << "]: " << arrayout[count] << std::endl;
    }
    *lfile << " ........." << std::endl;
    for (count = sizeout - 10; count < sizeout; count++) {
      *lfile << "arrayout[" << count << "]: " << arrayout[count] << std::endl;
    }
    *lfile << std::endl;

  }

  if (trace == 1) {
    //     *lfile << "size of input array (compressed):    " << s3 << std::endl;
    //     *lfile << "size of output array (uncompressed): " << s4 << std::endl;
  }

  *arryptr = arrayout;

  if (trace == 1) {
    *lfile << "DataCompression - uncompress arryptr: " << arryptr << std::endl;
    *lfile << "DataCompression - uncompress *arryptr: " << *arryptr << std::endl;
    *lfile << std::endl << std::endl;
  }

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_3)
  //      std::cerr << "===>Exiting  DataCompression::uncompress ()" << std::endl;
#endif

  istat = 0;
  return istat;
}


//=============================================================================
// Name: setLogFileName ( ofstream &tracefilename )
//
//
// Description:
//
// Arguments:
//
//
// Author: Carl Franke
// Date: 06 October 1994
//=============================================================================
//

int
DSSDataCompression::setLogFileName(std::ofstream *tracefilename)
{
#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_2) {
  //      std::cerr << "===>Entering DataCompression::setLogFileName ()" << std::endl;
  //  }
#endif

  lfile = tracefilename;
  *lfile << "DataCompression - setLogFileName member function" << std::endl;
  *lfile << std::endl;

  int istat;

  istat = 0;
  trace = 1;

  if (istat) {
    fprintf(stderr, "Status: %d\n", istat);
  }

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_3)
  //     std::cerr << "===>Exiting  DataCompression::setLogFileName ()" << std::endl;
#endif
  return istat;
}


//=============================================================================
// Name: status ( void )
//
// Description:  Display status of DataCompression object
//
// Arguments:
//
//
// Author: Carl Franke
// Date: 06 October 1994
//=============================================================================
//

int
DSSDataCompression::status(void)
{
#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_2) {
  //      std::cerr << "===>Entering DataCompression::status ()" << std::endl;
  //  }
#endif

  if (trace == 1) {
    *lfile << "DataCompression - status member function" << std::endl << std::endl;
  }

  int istat;

  istat = 0;

  // Introduce program

  if (trace == 1) {
    *lfile << "--- DataCompression Status Function ---" << std::endl;
    *lfile << std::endl;
    //     *lfile << "# Elements in Compressed Array:   " << numberElements << std::endl;
    //     *lfile << "First Element in Compressed Array: "<< precip[0] << std::endl;
    //     *lfile << "Last Element in Compressed Array:  "<< precip[last] << std::endl;
    *lfile << std::endl;
    //     *lfile << "# Elements in Uncompressed Array: " << sizeout << std::endl;
    //     *lfile << "First Element in Uncompressed Array: "<< arrayout[0] << std::endl;
    //     *lfile << "Last Element in Uncompressed Array:  "<< arrayout[53264];
    *lfile << std::endl << std::endl;
  }

  if (istat) {
    fprintf(stderr, "Status: %d\n", istat);
  }

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_3)
  //     std::cerr << "===>Exiting  DataCompression::status ()" << std::endl;
#endif
  return istat;
}


//=============================================================================
// Name: compress ( float *arrayin, int sizein, double compressionScaleFactor,
//                  double compressionBase, int *intarrayout, int &bytesout )
//
// Description: Data compression routine to compress float data where there
//              are repeated zero's.  The input float array can have positive
//              values, zero's, and -1.'s for undefined data. Repeated sequences
//              of zeros are counted and stored as a single value.
//
// Arguments: float *arrayout - pointer to input float array
//            int sizein - number elements in input float array
//            double compressionScaleFactor - scale factor for each value
//            double compressionBase - base offset for each value
//            int *intarrayout - pointer to integer array out
//            int &bytesout - number of bytes of integer array out
//
//
// Author: Carl Franke
// Date: 08 Aug 1994
// Revised: 05 Dec 1995
//=============================================================================
//

int
DSSDataCompression::compress(float *arrayin, int sizein,
  double compressionScaleFactor,
  double compressionBase,
  int *intarrayout, int &bytesout)

{

  // Declare all counters used by the "compress" member function

  // zerocount  - running count of one or more sequential 0's
  // minuscount - running count of one or more sequential -1's
  // totalzeros - total number of 0's found in data array
  // totalones  - total number of -1's found in data array
  // totalvals  - total number of non-zero data values found in data array
  // count      - counter used to increment through array elements

  short *shortval = new short[sizein];
  short *arrayout;
  arrayout = (short *)intarrayout;

  int count, newcount, repeatvals, longval;
  int totalzeros, totalones, totalvals, totalsize;

  count = 0;
  newcount = 0;
  totalzeros = 0;
  totalones = 0;
  totalvals = 0;


  while (count < sizein) {

    if (arrayin[count] <  compressionBase) {
      shortval[count] = -1;
    }
    else {

      longval = int((arrayin[count] - compressionBase) *
        compressionScaleFactor + .0001);

      if (longval > 32768) {
        std::cout << "Data Compression Overflow * * * * * * * * * " << std::endl;
        std::cout << "Array position: " << count << std::endl;
        std::cout << "Value: " << arrayin[count] << " set to Undefined" << std::endl;
        shortval[count] = -1;
      }
      else {
        shortval[count] = longval;
      }
    }

    //     std::cout << "#" << count << "  " << shortval[count] << std::endl;
    count++;

  }

  count = 0;

  while (count < sizein) {

    //     std::cout << "#" << count << "  " << shortval[count] << std::endl;

    if (shortval[count] == 0) {
      repeatvals = 0;
      while ((count < sizein) && (shortval[count] == 0)) {
        repeatvals++;
        //           std::cout << "#" << count << "  " << shortval[count] << std::endl;
        count++;
      }
      if (repeatvals < 16000) {
        totalzeros = totalzeros + repeatvals;
        arrayout[newcount] = repeatvals | 0x8000;
      }
      else {

        while (repeatvals >= 16000) {
          totalzeros = totalzeros + 16000;
          arrayout[newcount] =(short)( 16000 | 0x8000);
          newcount++;
          repeatvals = repeatvals - 16000;
        }

        totalzeros = totalzeros + repeatvals;
        arrayout[newcount] = repeatvals | 0x8000;
      }
    }

    else if (shortval[count] == -1) {
      repeatvals = 0;
      while ((count < sizein) && (shortval[count] == -1)) {
        repeatvals++;
        count++;
      }
      if (repeatvals < 16000) {
        totalones = totalones + repeatvals;
        arrayout[newcount] = repeatvals | 0xC000;
      }
      else {

        while (repeatvals >= 16000) {
          totalones = totalones + 16000;
          arrayout[newcount] =(short) (16000 | 0xC000);
          newcount++;
          repeatvals = repeatvals - 16000;
        }

        totalones = totalones + repeatvals;
        arrayout[newcount] = repeatvals | 0xC000;
      }
    }

    else {
      arrayout[newcount] = shortval[count];
      count++;
      totalvals++;
    }
    newcount++;
  }

  bytesout = newcount * 2;
  totalsize = totalzeros + totalones + totalvals;

  /* When we use PRECIP_2_BYTE compression, we're actually storing
  an array of shorts, but we're writing them to DSS with a method
  that expects an array of ints.  On little endian machines, this
  reverses the order of pairs of shorts.  (For an explanation, see
  comments in the compress function.)  To fix this problem we have
  to change the order of shorts within each int. */

#ifdef _MSC_VER // this only happens on PCs
  swapShorts((int*)arrayout, (bytesout + 3) / 4);
#endif



  delete[] shortval;

  //  std::cout << "totalzeros: " << totalzeros << std::endl;
  //  std::cout << "totalones:  " << totalones  << std::endl;
  //  std::cout << "totalvals:  " << totalvals  << std::endl;
  //  std::cout << "totalsize:  " << totalsize  << std::endl;

  return 0;

}


//=============================================================================
// Name: uncompress ( short arrayin[], int sizein, short *arrayout[],
//                    int &sizeout )
//
// Description: Uncompress Stage I and Stage III Spatial Precipitation Data
//
// Arguments:
//
//
// Author: Carl Franke
// Date: 08 Aug. 1994
//=============================================================================
//

int
DSSDataCompression::uncompress(int *intarrayin, int bytesin,
  double compressionScaleFactor,
  double compressionBase,
  float *arrayout, int &sizeout)

{

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_2) {
  //      std::cerr << "===>Entering DataCompression::uncompress ()" << std::endl;
  //  }
#endif

  /* The PRECIP_2_BYTE method is messy on PCs because we're reading an array of
  shorts (two bytes each) that was stored as an array of ints (four bytes
  each) in DSS.  The method was developed on a UNIX (big endian) system,
  and since DSS reverses the order of the bytes in ints when they're stored,
  this causes some problems when they're read out of DSS on a PC.  If you
  look at two shorts in hex they look like this

  UNIX: 0x01E9 0x023C (2 shorts, big endian)
  UNIX: 0x01E9023C    (1 int, big endian)
  PC:   0xC3209E10    (1 int, little endian)
  PC:   0xC320 0x9E10 (2 shorts, little endian, order reversed)

  On little endian (PC) systems, the shorts have the correct values, but
  the order of the shorts within an int is reversed.  We have to swap bytes
  0 and 1 with bytes 2 and three to get them out in the correct order.*/

  // This only happens on PCs
#ifdef _MSC_VER
  swapShorts(intarrayin, (bytesin + 3) / 4);
#endif

  int totalzeros, totalones, totalvals, totalsize;
  int count, newcount, k, sizein;
  int istat;

  short repeatvals, *arrayin;

  totalzeros = 0;
  totalones = 0;
  totalvals = 0;
  newcount = 0;
  count = 0;

  arrayin = (short *)intarrayin;

  sizein = bytesin / 2;

  while (count < sizein) {


    if ((arrayin[count] & 0x8000) == 0x0000) {
      arrayout[newcount] = arrayin[count];
      totalvals++;
      newcount++;
    }
    else if ((arrayin[count] & 0xC000) == 0x8000) {
      repeatvals = arrayin[count] & 0x3FFF;
      totalzeros = totalzeros + repeatvals;
      for (k = newcount; k < newcount + repeatvals; k++) {
        arrayout[k] = 0.0f;
      }
      newcount = newcount + repeatvals;
    }
    else if ((arrayin[count] & 0xC000) == 0xC000) {
      repeatvals = arrayin[count] & 0x3FFF;
      totalones = totalones + repeatvals;
      for (k = newcount; k < newcount + repeatvals; k++) {
        arrayout[k] = -1.0f;
      }
      newcount = newcount + repeatvals;
    }
    else {
    }
    count++;
  }

  sizeout = newcount;
  totalsize = totalzeros + totalones + totalvals;


  for (count = 0; count < newcount; count++) {
    if (arrayout[count] < 0) {
      arrayout[count] = UNDEFINED_FLOAT;
    }
    else {
      arrayout[count] = float(arrayout[count] / compressionScaleFactor
        + compressionBase);
    }
  }

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_3)
  //      std::cerr << "===>Exiting  DataCompression::uncompress ()" << std::endl;
#endif

  istat = 0;
  return istat;
}


//=============================================================================
// Name: zcompress ( float* arrayin,  int sizein, 
//                   int* arrayout, int &sizeout )
//
// Description: Compress data using zlib deflate
//
// Arguments:  arrayin - uncompressed data
//             sizein - length (number of floats) in input array
//             arrayout - compressed data
//             sizeout - at call, sizeout is the length (number of ints) 
//                       available in the output array.
//                       at exit, sizeout is set to the number of bytes
//                       in the output array
//
//  Note that the data can be of any type.  The output array is a collection
//  of bytes, padded out to fit in the space occupied by an array of ints.
//  
//
// Author: Tom Evans
// Date: 01 Jul. 1998
//=============================================================================
//

int
DSSDataCompression::zcompress(float *arrayin, int sizein,
  int *arrayout, int &sizeout)

{

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_2) {
  //      std::cerr << "===>Entering DataCompression::zcompress ()" << std::endl;
  //  }
#endif

  /* DSS byte order is little endian.  On UNIX, the floats are
  big endian, so we reverse the byte order of each float before
  we compress the array, so that when we uncompress it it will
  look the same as an uncompressed DSS array.*/

#ifndef _MSC_VER //This only happens in UNIX
  reverseByteOrder((int*)arrayin, sizein);
#endif


  //check version of zlib
  if (zlibVersion()[0] != ZLIB_VERSION[0]) {
    fprintf(stderr, "incompatible zlib version\n");
    exit(1);
  }
  else if (strcmp(zlibVersion(), ZLIB_VERSION) != 0) {
    fprintf(stderr, "warning: different zlib version\n");
  }

  //Most of what follows is copied verbatim from the compress function
  //in the zlib package.  Type definitions, for example, are in zlib.h 
  //or zconf.h.  In the original compress, destLen is a pointer.  Here
  //it's a value, because it's not an argument and pass-by-reference is
  //not needed. 

  Bytef *dest;
  uLongf destLen;
  const Bytef *source;
  uLong sourceLen;

  //this added at HEC
  source = (Bytef*)arrayin;
  dest = (Bytef*)arrayout;
  sourceLen = sizeof(float)*sizein; //length of uncompressed data in bytes
  destLen = sizeof(int)*sizeout;    //ditto compressed

                                    //back to zlib's compress
  z_stream stream;
  int err;

  stream.next_in = (Bytef*)source;
  stream.avail_in = (uInt)sourceLen;
#ifdef MAXSEG_64K
  /* Check for source > 64K on 16-bit machine: */
  if ((uLong)stream.avail_in != sourceLen) return Z_BUF_ERROR;
#endif
  stream.next_out = dest;
  stream.avail_out = (uInt)destLen;
  if ((uLong)stream.avail_out != destLen) return Z_BUF_ERROR;

  stream.zalloc = (alloc_func)0;
  stream.zfree = (free_func)0;
  stream.opaque = (voidpf)0;

  err = deflateInit(&stream, Z_DEFAULT_COMPRESSION);
  if (err != Z_OK) return err;

  err = deflate(&stream, Z_FINISH);
  if (err != Z_STREAM_END) {
    deflateEnd(&stream);
    return err == Z_OK ? Z_BUF_ERROR : err;
  }
  destLen = stream.total_out;

  // more HEC stuff
  sizeout = (int)destLen;

  /* zcompress produces a byte array which we store in DSS as an
  array of ints.  DSS byte order is little endian, so UNIX ints
  are byte-swapped as they're written to DSS.  We're really
  storing an array of bytes, which should have the same order on
  any platform, so on UNIX systems, we reverse the byte order
  of the ints before sending them to DSS, so that they'll come out
  in the right order in the DSS record.  There is probably a more
  elegant way to do this.  */

#ifndef _MSC_VER //This only happens in UNIX
  reverseByteOrder(arrayout, (sizeout + 3) / 4);
#endif


  err = deflateEnd(&stream);
  return err;
}

//=============================================================================
// Name: zuncompress ( int* arrayin,  int sizein, 
//                     float* arrayout, int &sizeout )
//
// Description: Uncompress data using zlib inflate
//
// Arguments:  arrayin - compressed data
//             sizein - length (number of ints) of input array
//             arrayout - uncompressed data
//             sizeout - at call, sizeout is the length (number of floats) 
//                       available in the output array.
//                       at exit, sizeout is set to the number of floats
//                       in the output array
//
//
//
// Author: Tom Evans
// Date: 01 Jul. 1998
//=============================================================================
//

int
DSSDataCompression::zuncompress(int *arrayin, int sizein,
  float *arrayout, int &sizeout)

{

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_2) {
  //      std::cerr << "===>Entering DataCompression::zuncompress ()" << std::endl;
  //  }
#endif

  //check version of zlib
  if (zlibVersion()[0] != ZLIB_VERSION[0]) {
    fprintf(stderr, "incompatible zlib version\n");
    exit(1);
  }
  else if (strcmp(zlibVersion(), ZLIB_VERSION) != 0) {
    fprintf(stderr, "warning: different zlib version\n");
  }

  /* The compressed byte array is stored as PC-style (little endian)
  integers.  On Unix, DSS reverses the byte order when it reads
  the array out of the record, so we have to re-reverse the order
  of the bytes so that ZLIB can make sense of them */

  // This doesn't happen on PCs
#ifndef _MSC_VER
  reverseByteOrder(arrayin, sizein);
#endif

  //Most of what follows is copied verbatim from the uncompress function
  //in the zlib package.  Type definitions, for example, are in zlib.h 
  //or zconf.h.  In the original compress, destLen is a pointer.  Here
  //it's a value, because it's not an argument and pass-by-reference is
  //not needed. 

  Bytef *dest;
  uLongf destLen;
  const Bytef *source;
  uLong sourceLen;

  // added at HEC
  dest = (Bytef*)arrayout;
  destLen = (uLongf)(sizeof(float)*sizeout);
  source = (const Bytef*)arrayin;
  sourceLen = (uLong)(sizeof(int)*sizein);

  z_stream stream;
  int err;

  stream.next_in = (Bytef*)source;
  stream.avail_in = (uInt)sourceLen;
  /* Check for source > 64K on 16-bit machine: */
  if ((uLong)stream.avail_in != sourceLen) return Z_BUF_ERROR;

  stream.next_out = dest;
  stream.avail_out = (uInt)destLen;
  if ((uLong)stream.avail_out != destLen) return Z_BUF_ERROR;

  stream.zalloc = (alloc_func)0;
  stream.zfree = (free_func)0;

  err = inflateInit(&stream);
  if (err != Z_OK) return err;

  err = inflate(&stream, Z_FINISH);
  if (err != Z_STREAM_END) {
    inflateEnd(&stream);
    return err;
  }
  destLen = stream.total_out;

  sizeout = destLen / sizeof(float);
  if (destLen % sizeof(float) != 0) {
    std::cerr << "Error in DataCompression::zuncompress.\n"
      << destLen << " is not a legal byte count." << std::endl;
  }

  /* Now we've uncompressed the 4-byte floats. They're in little-endian
  byte order.  That's backwards on UNIX, so we have to reverse them.*/

  // This doesn't happen on PCs
#ifndef _MSC_VER
  reverseByteOrder((int*)arrayout, sizeout);
#endif


  err = inflateEnd(&stream);
  return err;
}

//=============================================================================
// Name: zcompress ( float* arrayin,  int sizein, 
//                   double compressionScaleFactor,
//                   double compressionBase,
//                   int* arrayout, int &sizeout )
//
// Description: Compress in two stages: first convert floats to
//         shorts by subtracting an offset and multiplying by a scale
//         factor, then compress the shorts by using zlib deflate
//
// NOTES: This method involves loss of precision, and SHOULD NOT BE
//         USED on data that falls outside the range of -32768 to 
//         32767 after the offset and scaling.
//
// Arguments:  arrayin - uncompressed data
//             sizein - length (number of floats) in input array
//             compressionScaleFactor - see Description
//             compressionBase - see Description
//             arrayout - compressed data
//             sizeout - at call, sizeout is the length (number of ints) 
//                       available in the output array.
//                       at exit, sizeout is set to the number of bytes
//                       in the output array
//
//
// Author: Tom Evans
// Date: 15 Jul. 1998
//=============================================================================
//

int
DSSDataCompression::zcompress(float *arrayin, int sizein,
  double compressionScaleFactor,
  double compressionBase,
  int *arrayout, int &sizeout)

{

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_2) {
  //      std::cerr << "===>Entering DataCompression::zcompress ()" << std::endl;
  //  }
#endif

  int err;

  // create an array of shorts (2 bytes each) to store offset
  // and scaled data.  The array needs an even number of members.
  short *shortval;
  int shortarraylength;
  if ((sizein % 2) == 0) {
    shortval = new short[sizein];
    shortarraylength = sizein;
  }
  else {
    shortval = new short[sizein + 1];
    shortval[sizein] = SHRT_MAX;  // fill in pad value if needed
    shortarraylength = sizein + 1;
  }

  // convert floats to shorts by offset and scale
  int longval;
  for (int i = 0; i<sizein; i++) {
    if (arrayin[i] == UNDEFINED_FLOAT) {
      shortval[i] = SHRT_MAX;
    }
    else {
      longval = (int)((arrayin[i] - compressionBase) *
        compressionScaleFactor + .0001);

      if (longval > 32768) {
        std::cout << "Data Compression Overflow * * * * * * * * * " << std::endl;
        std::cout << "Array position: " << i << std::endl;
        std::cout << "Value: " << arrayin[i] << " set to Undefined" << std::endl;
        shortval[i] = SHRT_MAX;
      }
      else {
        shortval[i] = longval;
      }
    }
  }
  err = zcompress((float*)shortval, shortarraylength / 2,
    arrayout, sizeout);

  return err;

}

//=============================================================================
// Name: zuncompress ( int* arrayin,  int sizein, 
//                     double compressionScaleFactor,
//                     double compressionBase,
//                     float* arrayout, int &sizeout )
//
// Description: Uncompressed data compressed with the two-stage method 
//         of zcompress(float*, double, double, int*, &int).  Uncompression
//         reverses the steps, i.e. inflate an array of shorts from 
//         the data file, then divide by the scale factor and add 
//         the offset to arrive at floats.
//
// NOTES: This method involves loss of precision, and SHOULD NOT BE
//         USED on data that falls outside the range of -32768 to 
//         32767 after the offset and scaling.
//
// Arguments:  arrayin - compressed data
//             sizein - length (number of ints) in input array
//             compressionScaleFactor - see Description
//             compressionBase - see Description
//             arrayout - uncompressed data
//             sizeout - the number of elements to be written to the 
//                       out data array 
//
//
//
// Author: Tom Evans
// Date: 15 Jul. 1998
//=============================================================================
//

int
DSSDataCompression::zuncompress(int* arrayin, int sizein,
  double compressionScaleFactor,
  double compressionBase,
  float *arrayout, int sizeout)

{

#ifdef DEBUG
  //  if (dBug[DB_DataCompression] & DB_2) {
  //      std::cerr << "===>Entering DataCompression::zuncompress ()" << std::endl;
  //  }
#endif

  int err;
  short *shortval;
  shortval = new short[sizeout];

  int lengthAsFloats;
  if ((sizeout % 2) == 0) {
    lengthAsFloats = sizeout / 2;
  }
  else {
    lengthAsFloats = (sizeout + 1) / 2;
  }

  err = zuncompress(arrayin, sizein, (float*)shortval, lengthAsFloats);

  if (err != 0) {
    delete[] shortval;
    return err;
  }

  for (int i = 0; i<(sizeout); i++) {
    if (shortval[i] == SHRT_MAX) {
      arrayout[i] = UNDEFINED_FLOAT;
    }
    else {
      arrayout[i] = (float)((double)shortval[i] / compressionScaleFactor
        + compressionBase);
    }
  }
  delete[] shortval;
  return err;


}


void
DSSDataCompression::swapShorts(int* inArray, int intCount) {
  //  Utility function to swap short ints inside long ints
  //  to match big endians and little endians (e.g., swap on pc)

  //  Point to ints as shorts and swap ends
  short *array, swap;

  int icount = 0;
  array = (short*)inArray;

  for (int i = 0; i<intCount; i++) {
    swap = array[icount];
    array[icount] = array[icount + 1];
    icount++;
    array[icount] = swap;
    icount++;
  }
}

void
DSSDataCompression::reverseByteOrder(int* inArray, int intCount) {
  //  Utility function to reverse the order of bytes inside four-byte ints

  //  Point to ints as bytes and swap ends
  char *array, swap;

  int icount = 0;
  array = (char*)inArray;

  for (int i = 0; i<intCount; i++) {
    swap = array[icount];
    array[icount] = array[icount + 3];
    array[icount + 3] = swap;
    icount++;
    swap = array[icount];
    array[icount] = array[icount + 1];
    icount++;
    array[icount] = swap;
    icount++;
    icount++;
  }
}


