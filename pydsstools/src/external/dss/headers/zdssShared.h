C     ---------------------------------------
C
C     DSS Shared common block between versions 6 and 7
C     (At the Fortran level only - not C level)
C
      CHARACTER CRTYPE(45)*3, CRDESC(45)*50, CINTYP(10)*20
      CHARACTER CEXTYP(10)*20
      COMMON /ZDSS_SHARED/ CRTYPE, CRDESC, CINTYP, CEXTYP
	  INTEGER IRTYPE(45), NRTYPE
	  COMMON /ZDSS_SHAREDI/ NRTYPE, IRTYPE
C
C     ---------------------------------------

