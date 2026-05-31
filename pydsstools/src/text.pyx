cdef TextStruct createTextStruct(zStructText *ztxt):
    txt_st = TextStruct()
    if ztxt:
        txt_st.ztxt = ztxt
    else:
        zstructFree(ztxt)
        ztxt = NULL
    return txt_st


cdef class TextStruct:
    """Low-level wrapper around a C zStructText returned by ztextRetrieve."""

    cdef:
        zStructText *ztxt

    def __cinit__(self):
        self.ztxt = NULL

    def __dealloc__(self):
        if self.ztxt:
            zstructFree(self.ztxt)

    @property
    def text(self):
        """str for a simple text record, or None if this is a table record."""
        cdef:
            int n
            bytes raw
        if self.ztxt and self.ztxt[0].textString != NULL and self.ztxt[0].numberTextChars > 0:
            n = self.ztxt[0].numberTextChars
            raw = <bytes>self.ztxt[0].textString[:n]
            return raw.rstrip(b'\x00').decode('ascii', errors='replace')
        return None

    @property
    def table(self):
        """list[list[str]] for a text table/list record, or None if this is a simple text record.

        Outer list is rows, inner list is columns.  The C library stores cells
        row-major (all columns of row 0, then row 1, …), so this property reads
        them back in that same order.
        """
        cdef:
            int nrows, ncols
            bytes raw
            list cells, result
        if self.ztxt and self.ztxt[0].textTable != NULL and self.ztxt[0].numberTableChars > 0:
            nrows = self.ztxt[0].numberRows
            ncols = self.ztxt[0].numberColumns
            raw = <bytes>self.ztxt[0].textTable[:self.ztxt[0].numberTableChars]
            cells = raw.split(b'\x00')
            while cells and cells[-1] == b'':
                cells.pop()
            cells = [c.decode('ascii', errors='replace') for c in cells]
            # Storage is row-major: cells[row*ncols + col]
            result = [cells[row * ncols:(row + 1) * ncols] for row in range(nrows)]
            return result
        return None

    @property
    def labels(self):
        """list[str] of column labels, or [] if none."""
        cdef:
            bytes raw
            list parts
        if self.ztxt and self.ztxt[0].labels != NULL and self.ztxt[0].numberLabelChars > 0:
            raw = <bytes>self.ztxt[0].labels[:self.ztxt[0].numberLabelChars]
            parts = raw.split(b'\x00')
            while parts and parts[-1] == b'':
                parts.pop()
            return [p.decode('ascii', errors='replace') for p in parts]
        return []

    @property
    def data_type(self):
        if self.ztxt:
            return self.ztxt[0].dataType
        return None

    @property
    def dtype(self):
        """Subtype string describing the text content actually present.

        Returns one of:

        ``'text'``
            A plain text string is populated (``textString`` field).
            Always the case for DSS-6 records.
        ``'text_list'``
            A single-column text table is populated (``textTable`` field,
            ``numberColumns <= 1``).  ``dataType`` is 300 for this case.
        ``'text_table'``
            A multi-column text table is populated (``textTable`` field,
            ``numberColumns > 1``).  ``dataType`` is 310.  DSS-7 only.
        ``None``
            The struct is empty or unrecognised.

        Notes
        -----
        When a DSS-7 record holds both a text string and a text table
        simultaneously, the table type takes precedence here.  Both
        ``text`` and ``table`` properties remain independently accessible.
        """
        if not self.ztxt:
            return None
        cdef bint has_table = (self.ztxt[0].textTable != NULL and
                                self.ztxt[0].numberTableChars > 0)
        if has_table:
            if self.ztxt[0].numberColumns > 1:
                return 'text_table'
            return 'text_list'
        if self.ztxt[0].textString != NULL and self.ztxt[0].numberTextChars > 0:
            return 'text'
        return None

    @property
    def rows(self):
        """Number of rows in the text table, or 0 for a plain text record."""
        if self.ztxt:
            return self.ztxt[0].numberRows
        return 0

    @property
    def cols(self):
        """Number of columns in the text table, or 0 for a plain text record."""
        if self.ztxt:
            return self.ztxt[0].numberColumns
        return 0

    @property
    def pathname(self):
        if self.ztxt and self.ztxt[0].pathname:
            return self.ztxt[0].pathname
        return None


cdef class TextContainer:
    """Container for text data to be written to a DSS text record.

    Parameters
    ----------
    pathname : str
        DSS pathname for the record.
    text : str or None, optional
        Plain text string to store.
    table : list of list of str or None, optional
        Table data as rows x columns.
    labels : list of str or None, optional
        Column labels (one per column).  Length must match the number of columns.

    Notes
    -----
    At least one of ``text`` or ``table`` must be provided.
    """

    cdef:
        str _pathname
        object _text    # str | None
        object _table   # list[list[str]] | None
        object _labels  # list[str]

    def __init__(self, pathname, text=None, table=None, labels=None):
        if not isinstance(pathname, str):
            raise TypeError(f'Expected str for pathname, got {type(pathname).__name__}')
        if text is None and table is None:
            raise ValueError('At least one of text or table must be provided')
        if table is not None:
            if isinstance(table, np.ndarray):
                if table.ndim != 2:
                    raise ValueError(
                        f'numpy table array must be 2-dimensional, got {table.ndim}d'
                    )
                if table.dtype.kind == 'S':
                    table = [[cell.decode('ascii') for cell in row] for row in table]
                else:
                    table = [[str(cell) for cell in row] for row in table]
            if not table or not isinstance(table[0], (list, tuple)):
                raise ValueError('table must be a non-empty list of lists')
            if labels is not None:
                ncols = max(len(row) for row in table)
                if len(labels) != ncols:
                    raise ValueError(
                        f'labels length {len(labels)} does not match '
                        f'number of columns {ncols}'
                    )
        self._pathname = pathname
        self._text = text
        self._table = table
        self._labels = list(labels) if labels is not None else []

    @property
    def pathname(self):
        return self._pathname

    @property
    def text(self):
        """str to store as the plain text field, or None."""
        return self._text

    @property
    def table(self):
        """list[list[str]] table data, or None."""
        return self._table

    @property
    def labels(self):
        """list[str] of column labels (empty list if none)."""
        return self._labels

    @property
    def rows(self):
        """Number of rows in the table, or 0 if no table is set."""
        if self._table is not None:
            return len(self._table)
        return 0

    @property
    def cols(self):
        """Number of columns in the table, or 0 if no table is set."""
        if self._table is not None:
            return len(self._table[0]) if self._table else 0
        return 0
