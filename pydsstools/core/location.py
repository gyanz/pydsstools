from dataclasses import dataclass, field
from .enums import LocCoordSystem, LocHorizUnits, LocHorizDatum, LocVertUnits, LocVertDatum
from .._lib import DssPathName


def _coerce_enum(value, enum_cls):
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, int):
        try:
            return enum_cls(value)
        except ValueError:
            valid = ", ".join(f"{m.name}={m.value}" for m in enum_cls)
            raise ValueError(
                f"{value!r} is not a valid {enum_cls.__name__}. Valid values: {valid}"
            )
    raise TypeError(f"Expected {enum_cls.__name__} or int, got {type(value).__name__}")


@dataclass
class LocationInfo:
    pathname: DssPathName
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    coordinate_system: LocCoordSystem = LocCoordSystem.none
    coordinate_id: int = 0
    horizontal_units: LocHorizUnits = LocHorizUnits.unspecified
    horizontal_datum: LocHorizDatum = LocHorizDatum.unset
    vertical_units: LocVertUnits = LocVertUnits.unspecified
    vertical_datum: LocVertDatum = LocVertDatum.unset
    time_zone: str = ""
    supplemental: list = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.pathname, (str, DssPathName)):
            self.pathname = DssPathName(self.pathname)
        else:
            raise TypeError(
                f"Expected str or DssPathName for pathname, got {type(self.pathname).__name__}"
            )

        for attr in ("x", "y", "z"):
            val = getattr(self, attr)
            if isinstance(val, (int, float)):
                setattr(self, attr, float(val))
            else:
                raise TypeError(
                    f"Expected int or float for '{attr}', got {type(val).__name__}"
                )

        if not isinstance(self.coordinate_id, int):
            raise TypeError(
                f"Expected int for 'coordinate_id', got {type(self.coordinate_id).__name__}"
            )

        self.coordinate_system = _coerce_enum(self.coordinate_system, LocCoordSystem)
        self.horizontal_units  = _coerce_enum(self.horizontal_units,  LocHorizUnits)
        self.horizontal_datum  = _coerce_enum(self.horizontal_datum,  LocHorizDatum)
        self.vertical_units    = _coerce_enum(self.vertical_units,    LocVertUnits)
        self.vertical_datum    = _coerce_enum(self.vertical_datum,    LocVertDatum)

        if not isinstance(self.time_zone, str):
            raise TypeError(
                f"Expected str for 'time_zone', got {type(self.time_zone).__name__}"
            )

        if isinstance(self.supplemental, str):
            self.supplemental = [self.supplemental] if self.supplemental else []
        elif isinstance(self.supplemental, list):
            for i, item in enumerate(self.supplemental):
                if isinstance(item, (int, float)):
                    self.supplemental[i] = str(item)
                elif not isinstance(item, str):
                    raise TypeError(
                        f"Expected str, int, or float in 'supplemental' at index {i}, got {type(item).__name__}"
                    )
        else:
            raise TypeError(
                f"Expected str or list[str] for 'supplemental', got {type(self.supplemental).__name__}"
            )

    @property
    def vdi(self):
        """Return :class:`~pydsstools.core.vdi.VerticalDatumInfo` parsed from
        the ``supplemental`` list, or ``None`` if no VDI entry is found.

        Old-style DSS-6 files written by HEC tools store vertical datum info
        as a ``verticalDatumInfo:<compressed_xml>`` entry in the CSUPP field,
        which is surfaced here via ``LocationInfo.supplemental``.  Use this
        when ``TimeSeriesStruct.vdi`` returns ``None`` and you know the record
        originated from an old DSS-6 file.

        .. note::
            **Not yet validated against a real DSS-6 file written by old HEC
            tools.**  Confirm correctness once such a test file is available.
        """
        from pydsstools._lib import vdi_from_location
        return vdi_from_location(self)

    def update_from_crs(self, crs_input):
        """Update coordinate attributes from a CRS string or object (WKT, EPSG, PROJ, etc.).

        Sets ``coordinate_system``, ``horizontal_units``, ``horizontal_datum``,
        and ``coordinate_id`` derived from the CRS.  All other fields are
        unchanged.  Raises ValueError if the CRS cannot be parsed.

        Returns self to allow chaining.
        """
        from .crs import crs_to_location_attrs
        attrs = crs_to_location_attrs(crs_input)
        if attrs is None:
            raise ValueError(f"Could not parse CRS: {crs_input!r}")
        self.coordinate_system = attrs["coordinate_system"]
        self.horizontal_units  = attrs["horizontal_units"]
        self.horizontal_datum  = attrs["horizontal_datum"]
        self.coordinate_id     = attrs["coordinate_id"]
        return self
