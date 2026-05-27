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
