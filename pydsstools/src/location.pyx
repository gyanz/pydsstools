cdef object _location_struct_to_info(zStructLocation *zloc):
    from pydsstools.core.location import LocationInfo
    cdef:
        str pathname_str = ""
        str time_zone_str = ""
        str supp_str
        list supplemental

    if zloc[0].pathname != NULL:
        pathname_str = zloc[0].pathname
    if zloc[0].timeZoneName != NULL:
        time_zone_str = zloc[0].timeZoneName
    if zloc[0].supplemental != NULL:
        supp_str = zloc[0].supplemental
        supplemental = [s for s in supp_str.split("\n") if s]
    else:
        supplemental = []

    return LocationInfo(
        pathname=pathname_str,
        x=zloc[0].xOrdinate,
        y=zloc[0].yOrdinate,
        z=zloc[0].zOrdinate,
        coordinate_system=zloc[0].coordinateSystem,
        coordinate_id=zloc[0].coordinateID,
        horizontal_units=zloc[0].horizontalUnits,
        horizontal_datum=zloc[0].horizontalDatum,
        vertical_units=zloc[0].verticalUnits,
        vertical_datum=zloc[0].verticalDatum,
        time_zone=time_zone_str,
        supplemental=supplemental,
    )


cdef object _read_location_dss6(long long *ifltab, const char *pathname, int ts_type):
    """Read location metadata from a DSS-6 time-series internal header.

    DSS-6 does not have a standalone location record.  zlocationRetrieve
    is DSS-7 only (it rejects DSS-6 files with INCOMPATIBLE_VERSION).
    Location metadata — coordinates, timezone, supplemental info — is
    embedded in the time-series record internal header (IIHEAD words).
    The equivalent of zlocationRetrieve for DSS-6 is to call zrrtsc_
    (regular TS) or zritsc_ (irregular TS) with kvals=1 and read the
    output arguments: coords, icdesc, ctzone, csupp.

    Implementation notes
    --------------------
    1. Why not ztsinfo_?
       ztsinfo_ requires a full pathname with a non-empty D-part.
       The public API passes condensed pathnames (empty D-part, e.g.
       "//A/B//1HOUR/RUN:/").  ztsinfo_ returns lfound=0 for these.
       Solution: use zcatalog to find the first matching block, extract
       the D-part from pathnameList[0], and convert it via dateToJulian.

    2. Why not use boolIncludeDates on the catalog struct?
       The DSS-6 library does NOT allocate startDates/endDates even when
       boolIncludeDates=1; accessing them causes a null-pointer crash.
       The D-part string is parsed from pathnameList[0] instead.

    3. DSS period-average midnight convention (istime=720):
       In DSS-6 period-average regular TS, the timestamp 00:00 on day N
       is treated as the end of the last period of day N-1 and therefore
       falls in the previous block.  Using istime=0 (midnight) causes
       zrrtsc_ to return istat=5 (block not found) when the D-part is the
       block that logically contains noon of that day.  Using istime=720
       (noon) avoids this and reliably lands in the correct block.

    4. LCOORDS is a Fortran LOGICAL, not an integer count:
       In zrrtsi.f: "IF (COORDS(I).NE.0.0) LCOORDS = .TRUE."
       Fortran .TRUE. maps to -1 in C (all bits set), .FALSE. to 0.
       The original plan described lcoords as "0, 2, or 3" — that is
       wrong.  The correct check is (lcoords != 0), not (lcoords >= 1).

    5. Fortran blank-padding of character buffers:
       Fortran CHARACTER variables are blank-padded to their declared
       length without a null terminator.  Cython's <bytes>ptr uses
       strlen, which would read past the array boundary into adjacent
       stack memory.  Both ctzone and csupp are force-null-terminated at
       their last byte before any <bytes> cast.  The decode uses
       errors="replace" (not "strict") so stray non-ASCII bytes never
       raise an exception, and .rstrip() removes trailing Fortran spaces
       before splitting supplemental lines.

    6. DSS-6 vs DSS-7 enum equivalence (no conversion needed):
       icdesc[] integer encodings are identical in DSS-6 and DSS-7.
       Verified against zStructLocation.h (authoritative) and zrrtsi.f:
         icdesc[0]  coordinateSystem   0-5   LocCoordSystem    exact match
         icdesc[1]  coordinateID       int   plain int         exact match
         icdesc[2]  horizontalUnits    0-4   LocHorizUnits     exact match
         icdesc[3]  horizontalDatum    0-5   LocHorizDatum     exact match
         icdesc[4]  verticalUnits      0-2   LocVertUnits      exact match
         icdesc[5]  verticalDatum      0-3   LocVertDatum      exact match
       Note: zlocationRetrieve.c comments mention horizontalUnits=5 as
       "Local", but zStructLocation.h only defines 0-4.  The comment is
       a documentation error; DSS-6 Fortran stores icdesc raw from IIHEAD
       without remapping, confirming identical encodings.

    Returns None if no matching record is found (zcatalog returns 0
    blocks) or if zrrtsc_/zritsc_ returns a non-zero istat.
    """
    from pydsstools.core.location import LocationInfo

    cdef:
        # Catalog lookup to obtain a valid Julian start/end date
        zStructCatalog *zcat = NULL
        int juls = 0, istime = 0, jule = 9999999, ietime = 1440

        # Date/time strings for the regular TS call
        char date_str[40]
        char time_str[20]

        # Minimal data buffers (kvals=1 — metadata is always returned)
        int kvals = 1, nvals = 0
        int lgetdob = 0, lfildob = 0
        float svalue[1]
        double dvalue[1]
        int jqual[1]
        int lqual = 0, lqread = 0
        char cunits[40]
        char ctype[40]
        char csupp[512]
        int iofset = 0, jcomp = 0
        int itzone = 0
        char ctzone[64]
        double coords[3]
        int icdesc[6]
        int lcoords = 0
        int istat = 0

        # Irregular TS extras
        int itimes[1]
        int ibdate = 0, inflag = 0

        int i
        str pathname_str = (<bytes>pathname).decode("ascii", "strict")
        str tz_str = ""
        str supp_str
        list supplemental

    # Initialise output buffers
    for i in range(3):
        coords[i] = 0.0
    for i in range(6):
        icdesc[i] = 0
    cunits[0] = ctype[0] = csupp[0] = ctzone[0] = 0
    date_str[0] = 0
    time_str[0] = 0

    # Step 1: catalog lookup.
    # A condensed pathname has an empty D-part ("//") which zcatalog treats as
    # a literal match (no D-part), not a wildcard.  Replace it with '*' so the
    # search returns all time blocks.  A pathname that already has a D-part is
    # left unchanged.
    parts = pathname_str.split('/')
    if len(parts) == 8 and parts[4] == '':
        parts[4] = '*'
    wildcard_bytes = '/'.join(parts).encode('ascii')

    zcat = zstructCatalogNew()
    # Do NOT set boolIncludeDates: the DSS-6 library does not allocate
    # startDates/endDates for version-6 files, which would cause a crash.
    # Instead, extract the D-part from pathnameList[0] and parse it manually.
    zcatalog(ifltab, wildcard_bytes, zcat, 0)

    logging.debug(
        f"read_location dss6: catalog found {zcat[0].numberPathnames} "
        f"block(s) for {pathname_str!r}"
    )

    if zcat[0].numberPathnames == 0:
        zstructFree(zcat)
        logging.debug(
            f"read_location dss6: no records found for {pathname_str!r}, returning None"
        )
        return None

    # Copy the first full pathname before freeing the catalog struct
    first_path_bytes = <bytes>zcat[0].pathnameList[0]
    zstructFree(zcat)
    zcat = NULL

    # Extract D-part (index 4) from the full pathname and convert to Julian
    first_path_parts = first_path_bytes.decode('ascii', 'replace').split('/')
    d_part = first_path_parts[4] if len(first_path_parts) == 8 else ''
    if not d_part:
        logging.debug(
            f"read_location dss6: could not extract D-part from {first_path_bytes!r}, returning None"
        )
        return None

    juls = dateToJulian(d_part.encode('ascii'))
    logging.debug(f"read_location dss6: D-part={d_part!r} -> juls={juls} jule={jule}")

    # Step 2: fetch internal header (location) metadata
    if ts_type == 1:
        # Regular time series — zrrtsc_ needs a date/time string.
        # Use noon (720 min) instead of midnight: in DSS period-average
        # convention, 00:00 on day N is the last period of day N-1 and
        # falls in the previous block, causing a "block not found" error.
        istime = 720
        julianToDate(juls, 4, date_str, sizeof(date_str))    # style 4 = "DDmmmYYYY"
        minutesToHourMin(istime, time_str, sizeof(time_str))

        logging.debug(
            f"read_location dss6: zrrtsc_ "
            f"date={(<bytes>date_str).decode()} time={(<bytes>time_str).decode()}"
        )

        zrrtsc_(ifltab, pathname, date_str, time_str,
                &kvals, &nvals,
                &lgetdob, &lfildob,
                svalue, dvalue,
                jqual, &lqual, &lqread,
                cunits, ctype,
                csupp,
                &iofset, &jcomp,
                &itzone, ctzone,
                coords, icdesc, &lcoords,
                &istat,
                strlen(pathname), strlen(date_str), strlen(time_str),
                sizeof(cunits), sizeof(ctype),
                sizeof(csupp), sizeof(ctzone))

    else:
        # Irregular time series — zritsc_ takes Julian bounds directly
        logging.debug(
            f"read_location dss6: zritsc_ "
            f"juls={juls} istime={istime} jule={jule} ietime={ietime}"
        )

        zritsc_(ifltab, pathname,
                &juls, &istime, &jule, &ietime,
                &lgetdob, &lfildob,
                itimes, svalue, dvalue,
                &kvals, &nvals, &ibdate,
                jqual, &lqual, &lqread,
                cunits, ctype,
                csupp,
                &itzone, ctzone,
                coords, icdesc, &lcoords,
                &inflag, &istat,
                strlen(pathname),
                sizeof(cunits), sizeof(ctype),
                sizeof(csupp), sizeof(ctzone))

    # Fortran blank-pads character buffers to their full declared length without
    # adding a null terminator.  <bytes> uses strlen, which would read past the
    # array boundary into adjacent stack memory.  Force a null at the last byte
    # so strlen stops within bounds regardless of what the Fortran code wrote.
    ctzone[sizeof(ctzone) - 1] = 0
    csupp[sizeof(csupp) - 1] = 0

    logging.debug(
        f"read_location dss6: istat={istat} lcoords={lcoords} "
        f"coords=({coords[0]:.6g}, {coords[1]:.6g}, {coords[2]:.6g}) "
        f"icdesc={[icdesc[i] for i in range(6)]} "
        f"ctzone={(<bytes>ctzone).decode('ascii', 'replace').rstrip()!r}"
    )

    if istat != 0:
        logging.debug(
            f"read_location dss6: zrrtsc_/zritsc_ istat={istat} for {pathname_str!r}, returning None"
        )
        return None

    # Map outputs to LocationInfo.
    # Both ctzone and csupp are Fortran character buffers: blank-padded to
    # their declared length with no null terminator (already guarded above).
    # Use "replace" so stray non-ASCII bytes in the user header never crash
    # the decode.  rstrip() removes the Fortran blank-padding so that
    # trailing whitespace-only lines don't appear in the supplemental list.
    if ctzone[0] != 0:
        tz_str = (<bytes>ctzone).decode("ascii", "replace").rstrip()
    if csupp[0] != 0:
        supp_str = (<bytes>csupp).decode("ascii", "replace").rstrip()
        supplemental = [s for s in supp_str.split("\n") if s]
    else:
        supplemental = []

    # -----------------------------------------------------------------------
    # DSS-6 vs DSS-7 enum compatibility (verified against zStructLocation.h
    # and zrrtsi.f — no conversion required):
    #
    # icdesc field      DSS-6 range   DSS-7 range   Python enum        Match
    # ─────────────     ───────────   ───────────   ─────────────────  ─────
    # [0] coord system  0-5           0-5           LocCoordSystem     exact
    # [1] coord id      any int       any int       plain int          exact
    # [2] horiz units   0-4           0-4           LocHorizUnits      exact
    # [3] horiz datum   0-5           0-5           LocHorizDatum      exact
    # [4] vert units    0-2           0-2           LocVertUnits       exact
    # [5] vert datum    0-3           0-3           LocVertDatum       exact
    #
    # Note: zlocationRetrieve.c comments list horizontalUnits 5="Local"
    # but the authoritative zStructLocation.h header defines only 0-4.
    # DSS-6 Fortran (zrrtsi.f) stores icdesc raw from IIHEAD without
    # re-mapping, so the integer encodings are identical in both versions.
    #
    # LCOORDS is a Fortran LOGICAL, not a coordinate count:
    #   .TRUE.  → -1 in C (at least one coord non-zero) → use buffer values
    #   .FALSE. → 0  in C (all coords zero / not stored) → return 0.0
    # z remains 0.0 from buffer initialisation when no vertical datum stored.
    # -----------------------------------------------------------------------
    return LocationInfo(
        pathname=pathname_str,
        x=coords[0] if lcoords != 0 else 0.0,
        y=coords[1] if lcoords != 0 else 0.0,
        z=coords[2] if lcoords != 0 else 0.0,
        coordinate_system=icdesc[0],
        coordinate_id=icdesc[1],
        horizontal_units=icdesc[2],
        horizontal_datum=icdesc[3],
        vertical_units=icdesc[4],
        vertical_datum=icdesc[5],
        time_zone=tz_str,
        supplemental=supplemental,
    )
