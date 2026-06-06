cdef object _location_struct_to_info(zStructLocation *zloc):
    from pydsstools.core.location import LocationInfo
    cdef:
        str pathname_str = ""
        str time_zone_str = ""
        str supp_str

    if zloc[0].pathname != NULL:
        pathname_str = zloc[0].pathname
    if zloc[0].timeZoneName != NULL:
        time_zone_str = zloc[0].timeZoneName
    if zloc[0].supplemental != NULL:
        supp_str = zloc[0].supplemental
        supplemental = {k: v for k, _, v in
                        (line.partition(":") for line in supp_str.split("\n") if line)}
    else:
        supplemental = {}

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

    3. zcatalog sort argument (last arg = 0) and D-part wildcard:
       The D-part is always replaced with '*' before calling zcatalog,
       regardless of what the caller passed:
         - empty D-part (condensed): zcatalog treats "" literally → 0 hits
         - date-range D-part ("01JAN2017 - 31DEC2017"): zcatalog treats the
           full range string as a literal and finds 0 blocks
         - specific block D-part ("01SEP2017"): would find only one block
       Using '*' unconditionally handles all three cases uniformly, since
       all blocks carry identical location metadata and any block is valid.
       sort arg 0 = unsorted (fastest); confirmed in zcatalog.c source.
       zcatalog retrieves all matching blocks (numberWanted is not exposed
       by the public API); only pathnameList[0] is used.  Intentionally
       inefficient for API stability: see note 8.

    4. zlocationPath is DSS-7 only — no pathname transformation needed:
       In DSS-7, zlocationRetrieve calls zlocationPath internally to
       convert any data pathname /A/B/C/D/E/F/ into the location record
       path /A/B/Location Info////.  That transformation happens inside
       the library and is transparent to callers.  For DSS-6 there is no
       separate location record — we use the original TS data pathname
       directly with zcatalog and zrrtsc_/zritsc_.  No conversion needed.

    5. DSS period-average midnight convention (istime=720):
       In DSS-6 period-average regular TS, the timestamp 00:00 on day N
       is treated as the end of the last period of day N-1 and therefore
       falls in the previous block.  Using istime=0 (midnight) causes
       zrrtsc_ to return istat=5 (block not found) when the D-part is the
       block that logically contains noon of that day.  Using istime=720
       (noon) avoids this and reliably lands in the correct block.

    6. LCOORDS is a Fortran LOGICAL, not an integer count:
       In zrrtsi.f: "IF (COORDS(I).NE.0.0) LCOORDS = .TRUE."
       Fortran .TRUE. maps to -1 in C (all bits set), .FALSE. to 0.
       The original plan described lcoords as "0, 2, or 3" — that is
       wrong.  The correct check is (lcoords != 0), not (lcoords >= 1).

    7. Fortran blank-padding of character buffers:
       Fortran CHARACTER variables are blank-padded to their declared
       length without a null terminator.  Cython's <bytes>ptr uses
       strlen, which would read past the array boundary into adjacent
       stack memory.  Both ctzone and csupp are force-null-terminated at
       their last byte before any <bytes> cast.  The decode uses
       errors="replace" (not "strict") so stray non-ASCII bytes never
       raise an exception, and .rstrip() removes trailing Fortran spaces
       before splitting supplemental lines.

    8. Why not use ztsends_ or ztsrange_ instead of zcatalog?
       ztsends_ returns Julian start/end dates directly (no D-part
       string parsing), and ztsrange_ returns the first/last full
       pathnames.  Both accept condensed pathnames and would be more
       efficient than zcatalog for long TS records (many blocks).
       However, ztsends_ is marked deprecated in ztsends_.c ("Use
       ztsGetDateRange() instead"), and ztsGetDateRange only supports
       DSS-7.  ztsrange_ is a DSS-6 Fortran function not exposed through
       a versioned C wrapper, making its long-term availability uncertain.
       zcatalog is the stable, public, version-agnostic API for both
       DSS-6 and DSS-7, so it is used here even though it retrieves all
       matching blocks when only one is needed.

    9. DSS-6 vs DSS-7 enum equivalence (no conversion needed):
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
    blocks). Raises RuntimeError for any unrecognised non-zero istat via
    _check_dss6_istat. istat=1 and istat=4 are non-fatal (debug-logged):
    the location header is populated before either condition terminates the
    Fortran routine. istat=1 means missing value sentinels for zrrtsc_, or
    nvals exceeded kvals (data truncated) for zritsc_.
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
        dict supplemental

    # Initialise output buffers
    for i in range(3):
        coords[i] = 0.0
    for i in range(6):
        icdesc[i] = 0
    cunits[0] = ctype[0] = csupp[0] = ctzone[0] = 0
    date_str[0] = 0
    time_str[0] = 0

    # Step 1: catalog lookup.
    # Always replace the D-part with '*' so zcatalog returns all time blocks
    # regardless of what was passed in the input pathname.  Three cases:
    #   - condensed pathname (empty D-part "//"):  zcatalog would treat "" as a
    #     literal, matching nothing; '*' makes it match all blocks.
    #   - date-range D-part ("01JAN2017 - 31DEC2017"):  zcatalog treats this as
    #     a literal string and finds 0 matching blocks (no block carries that
    #     exact D-part); '*' makes it match all blocks.
    #   - specific block D-part ("01SEP2017"):  would match only that one block;
    #     '*' matches all blocks equally (correct, since all blocks carry the
    #     same location metadata — we just need any one block).
    parts = pathname_str.split('/')
    if len(parts) == 8:
        parts[4] = '*'
    wildcard_bytes = '/'.join(parts).encode('ascii')

    zcat = zstructCatalogNew()
    # Do NOT set boolIncludeDates: the DSS-6 library does not allocate
    # startDates/endDates for version-6 files, which would cause a crash.
    # Instead, extract the D-part from pathnameList[0] and parse it manually.
    zcatalog(ifltab, wildcard_bytes, zcat, 0)

    logger.debug(
        f"read_location dss6: catalog found {zcat[0].numberPathnames} "
        f"block(s) for {pathname_str!r}"
    )

    if zcat[0].numberPathnames == 0:
        zstructFree(zcat)
        logger.debug(
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
        logger.debug(
            f"read_location dss6: could not extract D-part from {first_path_bytes!r}, returning None"
        )
        return None

    juls = dateToJulian(d_part.encode('ascii'))
    logger.debug(f"read_location dss6: D-part={d_part!r} -> juls={juls} jule={jule}")

    # Step 2: fetch internal header (location) metadata
    if ts_type == 1:
        # Regular time series — zrrtsc_ needs a date/time string.
        # Use noon (720 min) instead of midnight: in DSS period-average
        # convention, 00:00 on day N is the last period of day N-1 and
        # falls in the previous block, causing a "block not found" error.
        istime = 720
        julianToDate(juls, 4, date_str, sizeof(date_str))    # style 4 = "DDmmmYYYY"
        minutesToHourMin(istime, time_str, sizeof(time_str))

        logger.debug(
            f"read_location dss6: zrrtsc_ "
            f"date={(<bytes>date_str).decode()} time={(<bytes>time_str).decode()}"
        )

        func_name = "zrrtsc_"
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
        # Irregular time series — zritsc_ takes Julian bounds directly.
        # Limit jule to juls (the first block's start day) so the read covers
        # only that block.  Without this, jule=9999999 would span all future
        # blocks; with kvals=1, reading a second block overflows the buffer and
        # DSS prints "Number of Data Found Exceeds Dimension Limit".
        # The block is opened whenever juls falls on its D-part date, so the
        # location header is always populated even if no values fall in the
        # narrow [juls 00:00 … juls 24:00] window.
        jule = juls
        logger.debug(
            f"read_location dss6: zritsc_ "
            f"juls={juls} istime={istime} jule={jule} ietime={ietime}"
        )

        func_name = "zritsc_"
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

    logger.debug(
        f"read_location dss6: istat={istat} lcoords={lcoords} "
        f"coords=({coords[0]:.6g}, {coords[1]:.6g}, {coords[2]:.6g}) "
        f"icdesc={[icdesc[i] for i in range(6)]} "
        f"ctzone={(<bytes>ctzone).decode('ascii', 'replace').rstrip()!r}"
    )

    _check_dss6_istat(istat, func_name, pathname_str)

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
        supplemental = {k: v for k, _, v in
                        (line.partition(":") for line in supp_str.split("\n") if line)}
    else:
        supplemental = {}

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


cdef void _write_location_dss6(long long *ifltab, TimeSeriesContainer tsc,
                                object loc, int storageFlag) except *:
    """Write TS data + location metadata to a DSS-6 file via zsrtsc_/zsitsc_.

    DSS-6 stores location in the TS internal header (IIHEAD words), not a
    separate record.  zlocationStore is DSS-7 only.  The only path to embed
    location in DSS-6 is zsrtsc_ (regular) or zsitsc_ (irregular), which
    accept the full TS dataset and all location arguments in a single call.

    No read-modify-write is performed: TimeSeriesContainer already holds the
    complete dataset.  storageFlag (IPLAN/inflag) controls how new data merges
    with any existing blocks, identical to the DSS-7 ztsStore behaviour.

    Error checking uses istat (0=OK, 4=all-missing not stored, >9=bad call).
    DssLastError / isError() are not reliable for these Fortran wrappers.

    Timezone: DSS-6 has one slot per record shared by both the TS and the
    location record.  If loc.time_zone is non-empty it is used; otherwise
    tsc.tzid is used.  When both are non-empty and differ, loc.time_zone wins
    and a warning is logged.

    NCOORDS is always 3 when LocationInfo is provided: this writes X, Y, Z
    and all six ICDESC fields unconditionally.  Zero coordinates are valid
    (e.g., the grid origin) and the caller explicitly requested location
    storage, so we never suppress it.
    """
    from pydsstools.core.location import LocationInfo

    cdef:
        double coords[3]
        int icdesc[6]
        int ncoords = 3     # always 3: write X/Y/Z + all icdesc fields
        int ncdesc = 6
        int itzone = 0      # numeric offset; named zone goes in ctzone
        char ctzone[64]
        char csupp[512]
        char cunits[40]
        char ctype[40]
        int istat = 0
        int ldouble = 0     # 0 = use svalues (float), 1 = use dvalues (double)
        int jcomp = 0
        double basev = 0.0
        int lbasev = 0
        int ldhigh = 0
        int nprec = 0
        double null_dbl = 0.0   # placeholder for unused dvalues argument
        double *null_dbl_ptr = &null_dbl
        int jqual_dummy[1]
        int *jqual_ptr
        int lqual = 0
        int nvals
        int ibdate = 0
        int inflag
        int i
        bytes _bpath, _bdate, _btime, _bunits, _btype, _bsupp, _btz
        const char *cpath

    if not isinstance(loc, LocationInfo):
        raise TypeError(f"Expected LocationInfo, got {type(loc).__name__}")

    _bpath = tsc._pathname.encode("ascii")
    cpath = PyBytes_AS_STRING(_bpath)

    # --- Coordinates and ICDESC ---
    coords[0] = loc.x
    coords[1] = loc.y
    coords[2] = loc.z
    icdesc[0] = int(loc.coordinate_system)
    icdesc[1] = loc.coordinate_id
    icdesc[2] = int(loc.horizontal_units)
    icdesc[3] = int(loc.horizontal_datum)
    icdesc[4] = int(loc.vertical_units)
    icdesc[5] = int(loc.vertical_datum)

    # --- Timezone (single slot; loc.time_zone has priority over tsc.tzid) ---
    ctzone[0] = 0
    tz_str = ""
    if loc.time_zone:
        tz_str = loc.time_zone
        if tsc.tzid and tsc.tzid != loc.time_zone:
            logger.warning(
                "DSS-6 write: one timezone slot per record; using "
                "loc.time_zone=%r (tsc.tzid=%r is ignored)",
                loc.time_zone, tsc.tzid,
            )
    elif tsc.tzid:
        tz_str = tsc.tzid
    if tz_str:
        _btz = tz_str.encode("ascii")
        if len(_btz) >= sizeof(ctzone):
            _btz = _btz[:sizeof(ctzone) - 1]
        memcpy(ctzone, PyBytes_AS_STRING(_btz), len(_btz))
        ctzone[len(_btz)] = 0

    # --- Supplemental ---
    csupp[0] = 0
    if loc.supplemental:
        _bsupp = "\n".join(f"{k}:{v}" for k, v in loc.supplemental.items()).encode("ascii")
        if len(_bsupp) >= sizeof(csupp):
            _bsupp = _bsupp[:sizeof(csupp) - 1]
        memcpy(csupp, PyBytes_AS_STRING(_bsupp), len(_bsupp))
        csupp[len(_bsupp)] = 0

    # --- Units and type (from TimeSeriesContainer) ---
    cunits[0] = ctype[0] = 0
    _bunits = tsc._data_units.encode("ascii")
    _btype  = tsc._data_type.encode("ascii")
    if len(_bunits) >= sizeof(cunits):
        _bunits = _bunits[:sizeof(cunits) - 1]
    if len(_btype) >= sizeof(ctype):
        _btype = _btype[:sizeof(ctype) - 1]
    memcpy(cunits, PyBytes_AS_STRING(_bunits), len(_bunits))
    cunits[len(_bunits)] = 0
    memcpy(ctype, PyBytes_AS_STRING(_btype), len(_btype))
    ctype[len(_btype)] = 0

    # --- Quality (DSS-6: at most one integer quality per value) ---
    jqual_dummy[0] = 0
    if tsc._quality_flags is not None:
        lqual = 1
        jqual_ptr = tsc._quality_ptr
    else:
        lqual = 0
        jqual_ptr = jqual_dummy

    # --- Dispatch on TS type ---
    if tsc._interval > 0:
        # ---- Regular time series via zsrtsc_ ----
        if tsc._start_time is None:
            raise ValueError(
                f"start_time is required for regular TS DSS-6 write: {tsc._pathname!r}"
            )
        nvals = tsc._count
        # zsrtsc_/IHM2M parses time right-to-left into a 4-char HHMM buffer.
        # Passing "HH:MM:SS" (time_style=2) fills the buffer with seconds
        # digits, discarding the hours — returning 0 (midnight) instead of
        # the real time.  Use style 0 ("HHMM") as documented in zsrtsi6.f.
        _bdate = tsc._start_time.date(104).encode("ascii")  # "01JAN2020"
        _btime = tsc._start_time.time(0).encode("ascii")   # "0100"

        logger.debug(
            "write_location dss6: zsrtsc_ path=%r date=%s time=%s nvals=%d iplan=%d",
            tsc._pathname,
            _bdate.decode("ascii"),
            _btime.decode("ascii"),
            nvals,
            storageFlag,
        )

        func_name = "zsrtsc_"
        zsrtsc_(ifltab, cpath,
                PyBytes_AS_STRING(_bdate), PyBytes_AS_STRING(_btime),
                &nvals, &ldouble,
                tsc._values_ptr, null_dbl_ptr,
                jqual_ptr, &lqual,
                cunits, ctype,
                coords, &ncoords, icdesc, &ncdesc,
                csupp, &itzone, ctzone,
                &storageFlag, &jcomp,
                &basev, &lbasev, &ldhigh, &nprec,
                &istat,
                strlen(cpath), len(_bdate), len(_btime),
                sizeof(cunits), sizeof(ctype),
                400, sizeof(ctzone))

    else:
        # ---- Irregular time series via zsitsc_ ----
        if tsc._times is None:
            raise ValueError(
                f"times is required for irregular TS DSS-6 write: {tsc._pathname!r}"
            )
        nvals = tsc._count
        # ibdate=0 (Dec 31 1899 = epoch) so that tsc._times_mv — which stores
        # absolute minutes from that same epoch via HecTime.value() — can be
        # passed directly without any offset adjustment.  This matches what
        # ztsStore does internally for DSS-6 writes: zstructTsNewIrregFloats
        # always receives julian_base=NULL, which leaves startJulian=0 in the
        # struct, so ztsStore also uses ibdate=0 and absolute times.
        ibdate = 0
        inflag = storageFlag

        logger.debug(
            "write_location dss6: zsitsc_ path=%r nvals=%d ibdate=%d inflag=%d",
            tsc._pathname, nvals, ibdate, inflag,
        )

        func_name = "zsitsc_"
        zsitsc_(ifltab, cpath,
                <int *>&tsc._times_mv[0], tsc._values_ptr, null_dbl_ptr,
                &ldouble, &nvals, &ibdate,
                jqual_ptr, &lqual,
                cunits, ctype,
                coords, &ncoords, icdesc, &ncdesc,
                csupp, &itzone, ctzone,
                &inflag, &istat,
                strlen(cpath), sizeof(cunits), sizeof(ctype),
                400, sizeof(ctzone))

    # --- Error check: DssLastError / isError() are not reliable here ---
    _check_dss6_istat(istat, func_name, tsc._pathname)


cpdef object vdi_from_location(object loc):
    """Extract :class:`~pydsstools.core.vdi.VerticalDatumInfo` from a
    :class:`~pydsstools.core.location.LocationInfo` supplemental list.

    DSS-6 tools store VDI in the CSUPP field as a semicolon- or
    newline-delimited entry of the form::

        verticalDatumInfo:<compressed_xml>

    where ``<compressed_xml>`` is the same gzip+base64 XML string used by
    DSS-7.  ``_read_location_dss6`` splits CSUPP by ``\\n`` and stores the
    result in ``LocationInfo.supplemental``, so the VDI entry appears as one
    element in that list.

    Parameters
    ----------
    loc : LocationInfo
        Location record previously returned by ``read_ts(location=True)``
        or ``read_location``.

    Returns
    -------
    VerticalDatumInfo or None
        Parsed VDI, or ``None`` if no ``verticalDatumInfo`` entry was found
        in the supplemental list or if parsing fails.

    .. note::
        **Not yet validated against a real DSS-6 file written by old HEC
        tools.**  The CSUPP format assumed here is based on source-code
        analysis of ``copyVdiFromLocationStructToUserHeader`` in
        ``verticalDatum.c``.  Confirm correctness once a test file with
        DSS-6 native VDI is available.
    """
    from pydsstools.core.vdi import VerticalDatumInfo
    cdef:
        verticalDatumInfo vdi_c
        char *err_msg = NULL
        bytes _b
        double undef = UNDEFINED_VERTICAL_DATUM_VALUE

    vdi_str = loc.supplemental.get("verticalDatumInfo")
    if vdi_str is None:
        return None
    _b = vdi_str.strip().encode("ascii")
    err_msg = stringToVerticalDatumInfo(&vdi_c, _b)
    if err_msg != NULL:
        logger.debug(
            "vdi_from_location: stringToVerticalDatumInfo failed: %s",
            (<bytes>err_msg).decode("ascii", "replace"),
        )
        free(err_msg)
        return None
    return VerticalDatumInfo(
        native_datum=(<bytes>vdi_c.nativeDatum).decode("ascii", "replace").rstrip('\x00').strip(),
        unit=(<bytes>vdi_c.unit).decode("ascii", "replace").rstrip('\x00').strip(),
        offset_to_navd88=(None if vdi_c.offsetToNavd88 == undef
                          else vdi_c.offsetToNavd88),
        navd88_is_estimate=bool(vdi_c.offsetToNavd88IsEstimate),
        offset_to_ngvd29=(None if vdi_c.offsetToNgvd29 == undef
                          else vdi_c.offsetToNgvd29),
        ngvd29_is_estimate=bool(vdi_c.offsetToNgvd29IsEstimate),
    )
