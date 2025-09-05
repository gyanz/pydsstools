"""
Currently unused.

Provides zlib compression and decompression functions equivalent to HEC's
implementations, with additional diagnostic features.

"""

from libc.stdlib cimport malloc, free
from libc.string cimport memset
from libc.stdint cimport uint8_t

cdef extern from "zlib.h":
    ctypedef void* voidpf
    ctypedef unsigned int  uInt
    ctypedef unsigned long uLong
    ctypedef unsigned long uLongf
    ctypedef unsigned char Bytef

    ctypedef void *(*alloc_func)(voidpf opaque, uInt items, uInt size)
    ctypedef void  (*free_func)(voidpf opaque, voidpf address)

    ctypedef struct z_stream_s:
        # zlib uses z_const Bytef*
        const Bytef* next_in        
        uInt   avail_in
        uLong  total_in
        Bytef* next_out
        uInt   avail_out
        uLong  total_out
        const char* msg
        voidpf state
        alloc_func zalloc
        free_func  zfree
        voidpf opaque
        int data_type
        uLong adler
        uLong reserved

    ctypedef z_stream_s z_stream
    ctypedef z_stream_s* z_streamp

    # Use the real underscored entry points + ZLIB_VERSION
    const char* ZLIB_VERSION
    int deflateInit_(z_streamp strm, int level, const char* version, int stream_size)
    int deflate    (z_streamp strm, int flush)
    int deflateEnd (z_streamp strm)

    int inflateInit_(z_streamp strm, const char* version, int stream_size)
    int inflate    (z_streamp strm, int flush)
    int inflateEnd (z_streamp strm)

    uLong       compressBound(uLong sourceLen)
    const char* zError(int)

    # constants
    int Z_OK
    int Z_STREAM_END
    int Z_NO_FLUSH
    int Z_FINISH
    int Z_BUF_ERROR
    int Z_DATA_ERROR
    int Z_MEM_ERROR
    int Z_STREAM_ERROR
    int Z_DEFAULT_COMPRESSION

# Small helpers that mirror the zlib macros
cdef inline int _deflateInit(z_streamp s, int level):
    return deflateInit_(s, level, ZLIB_VERSION, sizeof(z_stream))

cdef inline int _inflateInit(z_streamp s):
    return inflateInit_(s, ZLIB_VERSION, sizeof(z_stream))

cdef struct zlib_diag:
    int init_rc
    int step_rc
    int end_rc
    unsigned long total_in
    unsigned long total_out
    unsigned int  avail_in
    unsigned int  avail_out
    const char*   msg

cdef inline void _zero_diag(zlib_diag* d):
    if d != NULL:
        d.init_rc = d.step_rc = d.end_rc = 0
        d.total_in = d.total_out = 0
        d.avail_in = d.avail_out = 0
        d.msg = NULL

cdef inline void _fill_diag(zlib_diag* d, z_stream* zs,
                            int init_rc, int step_rc, int end_rc):
    if d != NULL:
        d.init_rc   = init_rc
        d.step_rc   = step_rc
        d.end_rc    = end_rc
        d.total_in  = zs.total_in
        d.total_out = zs.total_out
        d.avail_in  = zs.avail_in
        d.avail_out = zs.avail_out
        if step_rc not in (Z_OK, Z_STREAM_END):
            d.msg = zError(step_rc)
        elif init_rc != Z_OK:
            d.msg = zError(init_rc)
        elif end_rc != Z_OK:
            d.msg = zError(end_rc)
        else:
            d.msg = NULL

cdef int GetMaxCompressedLen(int size):
    cdef int n16kBlocks = (size + 16383) // 16384
    return size + 6 + n16kBlocks * 5

cdef const char* zlib_error_string(int rc):
    return zError(rc)

cdef int compress_zlib2(void* array, int size,
                        void** buffer, zlib_diag* diag):
    """
    Preallocates exactly GetMaxCompressedLen(size),
    deflates with Z_DEFAULT_COMPRESSION in a single Z_FINISH step.
    Returns total_out on success; -1 on failure.
    """
    cdef z_stream zInfo
    cdef int init_rc = 0
    cdef int step_rc = 0
    cdef int end_rc  = 0

    _zero_diag(diag)
    memset(&zInfo, 0, sizeof(zInfo))

    cdef int cap = GetMaxCompressedLen(size)
    buffer[0] = malloc(cap)
    if buffer[0] == NULL:
        if diag != NULL:
            diag.init_rc = Z_MEM_ERROR
            diag.msg = zError(Z_MEM_ERROR)
        return -1

    # Only set next_* and avail_*. zlib will maintain total_*
    zInfo.next_in   = <const Bytef*>array
    zInfo.avail_in  = <uInt>size
    zInfo.next_out  = <Bytef*>buffer[0]
    zInfo.avail_out = <uInt>cap
    zInfo.zalloc = <alloc_func>0
    zInfo.zfree  = <free_func>0
    zInfo.opaque = <voidpf>0

    init_rc = _deflateInit(&zInfo, Z_DEFAULT_COMPRESSION)
    if init_rc == Z_OK:
        step_rc = deflate(&zInfo, Z_FINISH)
    else:
        step_rc = 0

    end_rc = deflateEnd(&zInfo)

    if step_rc == Z_STREAM_END:
        _fill_diag(diag, &zInfo, init_rc, step_rc, end_rc)
        return <int>zInfo.total_out

    _fill_diag(diag, &zInfo, init_rc, step_rc, end_rc)
    free(buffer[0])
    buffer[0] = NULL
    return -1

cdef int uncompress_zlib2(const void* buffer, int size,
                          void* data, int dataSize,
                          zlib_diag* diag):
    """
    Uses caller's buffer (data, dataSize).
    Returns total_out on success; -1 on failure.
    """
    cdef z_stream zInfo
    cdef int init_rc = 0
    cdef int step_rc = 0
    cdef int end_rc  = 0

    _zero_diag(diag)
    memset(&zInfo, 0, sizeof(zInfo))

    zInfo.next_in   = <const Bytef*>buffer
    zInfo.avail_in  = <uInt>size
    zInfo.next_out  = <Bytef*>data
    zInfo.avail_out = <uInt>dataSize
    zInfo.zalloc = <alloc_func>0
    zInfo.zfree  = <free_func>0
    zInfo.opaque = <voidpf>0

    init_rc = _inflateInit(&zInfo)
    if init_rc == Z_OK:
        step_rc = inflate(&zInfo, Z_FINISH)
    else:
        step_rc = 0

    end_rc = inflateEnd(&zInfo)

    if step_rc == Z_STREAM_END:
        _fill_diag(diag, &zInfo, init_rc, step_rc, end_rc)
        return <int>zInfo.total_out

    _fill_diag(diag, &zInfo, init_rc, step_rc, end_rc)
    return -1