"""
This module is copied from from rasterio project:

@Misc{,
  author =    {Sean Gillies and others},
  organization = {Mapbox},
  title =     {Rasterio: geospatial raster I/O for {Python} programmers},
  year =      {2013--},
  url = "https://github.com/mapbox/rasterio"
  }
"""

from __future__ import division

import collections
import math

from affine import Affine


IDENTITY = Affine.identity()
GDAL_IDENTITY = IDENTITY.to_gdal()


class TransformMethodsMixin(object):
    """Mixin providing methods for calculations related
    to transforming between rows and columns of the raster
    array and the coordinates.
    These methods are wrappers for the functionality in
    `rasterio.transform` module.
    A subclass with this mixin MUST provide a `transform`
    property.
    """

    def xy(self, row, col, offset="center"):
        """Returns the coordinates ``(x, y)`` of a pixel at `row` and `col`.
        The pixel's center is returned by default, but a corner can be returned
        by setting `offset` to one of `ul, ur, ll, lr`.
        Parameters
        ----------
        row : int
            Pixel row.
        col : int
            Pixel column.
        offset : str, optional
            Determines if the returned coordinates are for the center of the
            pixel or for a corner.
        Returns
        -------
        tuple
            ``(x, y)``
        """
        return xy(self.transform, row, col, offset=offset)

    def index(self, x, y, op=math.floor, precision=None):
        """
        Returns the (row, col) index of the pixel containing (x, y) given a
        coordinate reference system.
        Use an epsilon, magnitude determined by the precision parameter
        and sign determined by the op function:
            positive for floor, negative for ceil.
        Parameters
        ----------
        x : float
            x value in coordinate reference system
        y : float
            y value in coordinate reference system
        op : function, optional (default: math.floor)
            Function to convert fractional pixels to whole numbers (floor,
            ceiling, round)
        precision : int, optional (default: None)
            Decimal places of precision in indexing, as in `round()`.
        Returns
        -------
        tuple
            (row index, col index)
        """
        return rowcol(self.transform, x, y, op=op, precision=precision)


def tastes_like_gdal(seq):
    """Return True if `seq` matches the GDAL geotransform pattern."""
    return tuple(seq) == GDAL_IDENTITY or (
        seq[2] == seq[4] == 0.0 and seq[1] > 0 and seq[5] < 0
    )


def guard_transform(transform):
    """Return an Affine transformation instance."""
    if not isinstance(transform, Affine):
        if tastes_like_gdal(transform):
            raise TypeError(
                "GDAL-style transforms have been deprecated.  This "
                "exception will be raised for a period of time to highlight "
                "potentially confusing errors, but will eventually be removed."
            )
        else:
            transform = Affine(*transform)
    return transform


def from_origin(west, north, xsize, ysize):
    """Return an Affine transformation given upper left and pixel sizes.
    Return an Affine transformation for a georeferenced raster given
    the coordinates of its upper left corner `west`, `north` and pixel
    sizes `xsize`, `ysize`.
    """
    return Affine.translation(west, north) * Affine.scale(xsize, -ysize)


def from_bounds(west, south, east, north, width, height):
    """Return an Affine transformation given bounds, width and height.
    Return an Affine transformation for a georeferenced raster given
    its bounds `west`, `south`, `east`, `north` and its `width` and
    `height` in number of pixels.
    """
    return Affine.translation(west, north) * Affine.scale(
        (east - west) / width, (south - north) / height
    )


def array_bounds(height, width, transform):
    """Return the bounds of an array given height, width, and a transform.
    Return the `west, south, east, north` bounds of an array given
    its height, width, and an affine transform.
    """
    w, n = transform.xoff, transform.yoff
    e, s = transform * (width, height)
    return w, s, e, n


def xy(transform, rows, cols, offset="center"):
    """Returns the x and y coordinates of pixels at `rows` and `cols`.
    The pixel's center is returned by default, but a corner can be returned
    by setting `offset` to one of `ul, ur, ll, lr`.
    Parameters
    ----------
    transform : affine.Affine
        Transformation from pixel coordinates to coordinate reference system.
    rows : list or int
        Pixel rows.
    cols : list or int
        Pixel columns.
    offset : str, optional
        Determines if the returned coordinates are for the center of the
        pixel or for a corner.
    Returns
    -------
    xs : list
        x coordinates in coordinate reference system
    ys : list
        y coordinates in coordinate reference system
    """

    single_col = False
    single_row = False
    if not isinstance(cols, collections.Iterable):
        cols = [cols]
        single_col = True
    if not isinstance(rows, collections.Iterable):
        rows = [rows]
        single_row = True

    if offset == "center":
        coff, roff = (0.5, 0.5)
    elif offset == "ul":
        coff, roff = (0, 0)
    elif offset == "ur":
        coff, roff = (1, 0)
    elif offset == "ll":
        coff, roff = (0, 1)
    elif offset == "lr":
        coff, roff = (1, 1)
    else:
        raise ValueError("Invalid offset")

    xs = []
    ys = []
    for col, row in zip(cols, rows):
        x, y = transform * transform.translation(coff, roff) * (col, row)
        xs.append(x)
        ys.append(y)

    if single_row:
        ys = ys[0]
    if single_col:
        xs = xs[0]

    return xs, ys


def rowcol(transform, xs, ys, op=math.floor, precision=None):
    """
    Returns the rows and cols of the pixels containing (x, y) given a
    coordinate reference system.
    Use an epsilon, magnitude determined by the precision parameter
    and sign determined by the op function:
        positive for floor, negative for ceil.
    Parameters
    ----------
    transform : Affine
        Coefficients mapping pixel coordinates to coordinate reference system.
    xs : list or float
        x values in coordinate reference system
    ys : list or float
        y values in coordinate reference system
    op : function
        Function to convert fractional pixels to whole numbers (floor, ceiling,
        round)
    precision : int, optional
        Decimal places of precision in indexing, as in `round()`.
    Returns
    -------
    rows : list of ints
        list of row indices
    cols : list of ints
        list of column indices
    """

    single_x = False
    single_y = False
    if not isinstance(xs, collections.Iterable):
        xs = [xs]
        single_x = True
    if not isinstance(ys, collections.Iterable):
        ys = [ys]
        single_y = True

    if precision is None:
        eps = 0.0
    else:
        eps = 10.0**-precision * (1.0 - 2.0 * op(0.1))

    invtransform = ~transform

    rows = []
    cols = []
    for x, y in zip(xs, ys):
        fcol, frow = invtransform * (x + eps, y - eps)
        cols.append(op(fcol))
        rows.append(op(frow))

    if single_x:
        cols = cols[0]
    if single_y:
        rows = rows[0]

    return rows, cols
