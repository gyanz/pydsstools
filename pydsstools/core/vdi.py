from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class VerticalDatumInfo:
    """Vertical datum information stored in a DSS time-series user header.

    Describes the datum of the time-series *data values* and the offsets
    needed to convert them to NAVD-88 and/or NGVD-29.

    This is distinct from ``LocationInfo.vertical_datum``, which is the datum
    of the gauge's Z *coordinate* (physical elevation).  VDI describes the
    datum of the *recorded values* plus the shift factors needed to convert
    those values to standard datums.

    Offsets use the same unit as the elevation data (e.g. feet).
    ``None`` means the offset is not known / not stored in the file.

    Parameters
    ----------
    native_datum : str
        Name of the datum the data values are in, e.g. ``"NAVD-88"``,
        ``"NGVD-29"``, or ``"LOCAL"``.  Max 16 characters.
    unit : str
        Unit of the datum offsets, e.g. ``"ft"`` or ``"m"``.  Max 16 chars.
    offset_to_navd88 : float or None
        Offset from *native_datum* to NAVD-88, in *unit*.
    navd88_is_estimate : bool
        ``True`` if *offset_to_navd88* is a rough estimate rather than a
        precisely surveyed value.  Default ``False``.
    offset_to_ngvd29 : float or None
        Offset from *native_datum* to NGVD-29, in *unit*.
    ngvd29_is_estimate : bool
        ``True`` if *offset_to_ngvd29* is a rough estimate.  Default ``False``.
    """

    native_datum: str = ""
    unit: str = ""
    offset_to_navd88: Optional[float] = None
    navd88_is_estimate: bool = False
    offset_to_ngvd29: Optional[float] = None
    ngvd29_is_estimate: bool = False

    def __post_init__(self):
        if not isinstance(self.native_datum, str):
            raise TypeError(
                f"Expected str for 'native_datum', got {type(self.native_datum).__name__}"
            )
        if len(self.native_datum) > 16:
            raise ValueError(
                f"'native_datum' exceeds 16 characters: {self.native_datum!r}"
            )
        if not isinstance(self.unit, str):
            raise TypeError(
                f"Expected str for 'unit', got {type(self.unit).__name__}"
            )
        if len(self.unit) > 16:
            raise ValueError(
                f"'unit' exceeds 16 characters: {self.unit!r}"
            )
        for attr in ("offset_to_navd88", "offset_to_ngvd29"):
            val = getattr(self, attr)
            if val is not None:
                if isinstance(val, int):
                    setattr(self, attr, float(val))
                elif not isinstance(val, float):
                    raise TypeError(
                        f"Expected float or None for '{attr}', got {type(val).__name__}"
                    )
        for attr in ("navd88_is_estimate", "ngvd29_is_estimate"):
            val = getattr(self, attr)
            if not isinstance(val, bool):
                setattr(self, attr, bool(val))
