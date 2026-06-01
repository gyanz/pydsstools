
_IMAGE_EXTENSIONS = frozenset({
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'ico', 'svg', 'raw',
})


def _binary_type_from_ext(ext):
    """Infer BinaryType from a file extension string (without leading dot)."""
    if ext.lower() in _IMAGE_EXTENSIONS:
        return BinaryType.IMAGE
    if ext:
        return BinaryType.FILE
    return BinaryType.UNDEFINED


cdef BinaryStruct _createBinaryStruct(zStructTransfer *ptr, str pathname):
    cdef BinaryStruct bs = BinaryStruct()
    if ptr != NULL:
        bs._ptr = ptr
    bs._pathname = pathname
    return bs


cdef class BinaryStruct:
    """Low-level wrapper around a C zStructTransfer returned by zread for binary records.

    Properties
    ----------
    data : bytes
        Raw binary content.  Exact byte count, no int-alignment padding.
    pathname : str
        Full DSS pathname string.
    filename : str
        Filename from the C-part of the pathname.
    extension : str
        File extension from the E-part of the pathname (no leading dot).
    data_type : BinaryType
        BinaryType.FILE, BinaryType.IMAGE, or BinaryType.UNDEFINED.
    is_image : bool
        True when data_type is BinaryType.IMAGE.
    size : int
        Exact byte count of the stored data.
    """

    cdef:
        zStructTransfer *_ptr
        str _pathname

    def __cinit__(self):
        self._ptr = NULL

    def __dealloc__(self):
        if self._ptr != NULL:
            zstructFree(self._ptr)

    @property
    def data(self):
        """Raw bytes of the binary record, exact byte count."""
        cdef int n
        if self._ptr == NULL or self._ptr[0].values1 == NULL:
            return b''
        n = self._ptr[0].logicalNumberValues
        if n <= 0:
            return b''
        return (<char *>self._ptr[0].values1)[:n]

    @property
    def pathname(self):
        """Full DSS pathname."""
        return self._pathname

    @property
    def filename(self):
        """Filename from the C-part of the DSS pathname."""
        if self._pathname:
            return DssPathName(self._pathname).cpart
        return ''

    @property
    def extension(self):
        """File extension from the E-part of the DSS pathname (no leading dot)."""
        if self._pathname:
            return DssPathName(self._pathname).epart
        return ''

    @property
    def data_type(self):
        """BinaryType of this record."""
        if self._ptr == NULL:
            return BinaryType.UNDEFINED
        try:
            return BinaryType(self._ptr[0].dataType)
        except ValueError:
            return BinaryType.UNDEFINED

    @property
    def is_image(self):
        """True if this is an image record (data_type == BinaryType.IMAGE)."""
        return self.data_type == BinaryType.IMAGE

    @property
    def size(self):
        """Exact byte count of the stored binary data."""
        if self._ptr == NULL:
            return 0
        return self._ptr[0].logicalNumberValues

    def save_to(self, path):
        """Write the binary data to a file on disk.

        Parameters
        ----------
        path : str or Path
            Destination file path.  Parent directories are created as needed.

        Returns
        -------
        Path
            Path to the written file.
        """
        import pathlib
        dest = pathlib.Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.data)
        return dest


class BinaryContainer:
    """Container for binary data to be written to a DSS record.

    Parameters
    ----------
    pathname : str
        DSS pathname.  For BinaryType.IMAGE the D-part is forced to
        ``'IMAGE'``; for BinaryType.FILE it is forced to ``'FILE'``.
        For BinaryType.UNDEFINED the D-part is left as provided.
    data : bytes or bytearray
        Raw binary content to store.
    data_type : BinaryType or None, optional
        Type of binary record.  When None the type is inferred in order:

        1. From the D-part of *pathname* if it is ``'IMAGE'`` or ``'FILE'``.
        2. From the E-part (file extension): known image extensions →
           BinaryType.IMAGE; any other extension → BinaryType.FILE;
           no extension → BinaryType.UNDEFINED.

    Raises
    ------
    TypeError
        If *pathname* is not str, *data* is not bytes/bytearray, or
        *data_type* is not a BinaryType member or None.
    """

    def __init__(self, pathname, data, data_type=None):
        if not isinstance(pathname, str):
            raise TypeError(
                'Expected str for pathname, got {!r}'.format(type(pathname).__name__)
            )
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(
                'Expected bytes or bytearray for data, got {!r}'.format(
                    type(data).__name__)
            )
        if data_type is not None and not isinstance(data_type, BinaryType):
            raise TypeError(
                'data_type must be a BinaryType member or None, '
                'got {!r}'.format(type(data_type).__name__)
            )

        path = DssPathName(pathname)
        ext = path.epart.lower()

        if data_type is None:
            d = path.dpart.upper()
            if d == 'IMAGE':
                data_type = BinaryType.IMAGE
            elif d == 'FILE':
                data_type = BinaryType.FILE
            else:
                data_type = _binary_type_from_ext(ext)

        if data_type == BinaryType.IMAGE:
            path.dpart = 'IMAGE'
        elif data_type == BinaryType.FILE:
            path.dpart = 'FILE'
        # UNDEFINED: leave D-part as provided

        self._pathname = path.text()
        self._data = bytes(data)
        self._data_type = data_type

    @classmethod
    def from_file(cls, filepath, pathname=None, a='', b='', f=''):
        """Create a BinaryContainer by reading a file from disk.

        Parameters
        ----------
        filepath : str or Path
            Path to the source file.
        pathname : str or None, optional
            DSS pathname to use.  If None, one is auto-built:
            C-part = filename, D-part = ``'IMAGE'`` or ``'FILE'``,
            E-part = extension without dot.
        a, b, f : str
            A, B, F parts used only when *pathname* is auto-built.

        Returns
        -------
        BinaryContainer
        """
        import pathlib
        fp = pathlib.Path(filepath)
        data = fp.read_bytes()
        if pathname is None:
            name = fp.name
            ext = fp.suffix.lstrip('.')
            bt = _binary_type_from_ext(ext)
            if bt == BinaryType.IMAGE:
                d_part = 'IMAGE'
            elif bt == BinaryType.FILE:
                d_part = 'FILE'
            else:
                d_part = ''
            pathname = '/{}/{}/{}/{}/{}/{}/'.format(a, b, name, d_part, ext, f)
        return cls(pathname, data)

    @property
    def pathname(self):
        """Full DSS pathname with D-part enforced."""
        return self._pathname

    @property
    def data(self):
        """Raw bytes to be written."""
        return self._data

    @property
    def data_type(self):
        """BinaryType for this record."""
        return self._data_type

    @property
    def is_image(self):
        """True when data_type is BinaryType.IMAGE."""
        return self._data_type == BinaryType.IMAGE

    @property
    def filename(self):
        """Filename from the C-part of the DSS pathname."""
        return DssPathName(self._pathname).cpart

    @property
    def extension(self):
        """File extension from the E-part of the DSS pathname (no leading dot)."""
        return DssPathName(self._pathname).epart

    @property
    def size(self):
        """Byte count of the data."""
        return len(self._data)
