"""
HEC-Style Run-Length Encoding (RLE) - Lossless Compression Algorithm
--------------------------------------------------------------------

RLE is a simple form of lossless data compression. The basic idea:

    • Instead of storing each element in a sequence individually, 
      store the value once along with the number of times it repeats.
    • This works best when the data contains long runs of the same 
      value (e.g., large areas of a single color in an image).

Standard RLE encodes every run as (value, count) pairs. 
This HEC-Style implementation uses a hybrid approach to reduce 
overhead for values that do not repeat:

    • Floats are first quantized to 16-bit signed integers (shorts).
    • Runs of zero values are encoded with a special marker (0x8000).
    • Runs of a special "sentinel" value (-1) are encoded with 
      a different marker (0xC000).
    • Each run marker is immediately followed by the run length.
    • All other values (literals) are written directly into the 
      output without further encoding.

Encoding summary:
    zeros   → (count | 0x8000)
    -1's    → (count | 0xC000)
    other   → literal short value
"""

ctypedef float f32
# cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False

cdef inline int16_t _quantize_f32(f32 v, f32 scale, f32 base) nogil:
    """
    Parity for float inputs:
      if v < base -> -1
      else longval = int(((v - base)*scale) + 0.5)
           if longval > 32768 -> -1
           else cast to 16-bit
    """
    cdef int longval
    if v < base:
        return <int16_t>-1
    longval = <int>(((v - base) * scale) + 0.5)
    if longval > 32768:
        return <int16_t>-1
    return <int16_t>longval   # 0..32767 or -1 (already handled)

# ==========================================================
#  Cython-callable (cdef)
# ==========================================================
cdef int hec_compress(const f32[::1] arrayin,             # float32 input (C-contiguous)
                          Py_ssize_t sizein,              # number of elements to read
                          f32 scale,                      # compressionScaleFactor (float32)
                          f32 base,                       # compressionBase (float32)
                          int16_t[::1] arrayout,          # output tokens; capacity >= sizein
                          int32_t[::1] sizeout) nogil:
    """
    HEC-style RLE on a fully C-contiguous 2-D float32 grid.

      zeros  -> (count | 0x8000)
      -1's   -> (count | 0xC000)
      other  -> literal short

    On success: sizeout[0] = unpadded BYTES (= 2 * number_of_tokens), return 0
    On error:   return -1
    """
    cdef:
        Py_ssize_t n = sizein
        Py_ssize_t idx = 0
        Py_ssize_t newcount = 0
        Py_ssize_t repeatvals
        int16_t sv, t

    if sizein < 0 or sizeout.shape[0] < 1:
        return -1
    # Safe upper bound: <= sizein tokens (all literals)
    if arrayout.shape[0] < n:
        return -1

    while idx < n:
        sv = _quantize_f32(arrayin[idx], scale, base)
        idx += 1

        if sv == 0:
            repeatvals = 1
            while idx < n:
                t = _quantize_f32(arrayin[idx], scale, base)
                if t != 0:
                    break
                repeatvals += 1
                idx += 1
            while repeatvals >= 16000:
                arrayout[newcount] = <int16_t>(16000 | 0x8000)
                newcount += 1
                repeatvals -= 16000
            arrayout[newcount] = <int16_t>(repeatvals | 0x8000)
            newcount += 1

        elif sv == <int16_t>-1:
            repeatvals = 1
            while idx < n:
                t = _quantize_f32(arrayin[idx], scale, base)
                if t != <int16_t>-1:
                    break
                repeatvals += 1
                idx += 1
            while repeatvals >= 16000:
                arrayout[newcount] = <int16_t>(16000 | 0xC000)
                newcount += 1
                repeatvals -= 16000
            arrayout[newcount] = <int16_t>(repeatvals | 0xC000)
            newcount += 1

        else:
            arrayout[newcount] = sv
            newcount += 1

    sizeout[0] = <int32_t>(newcount * 2)  # bytes (unpadded)
    return 0


cdef int hec_uncompress(const int16_t[::1] arrayin,   # RLE tokens
                        int bytesin,                  # valid BYTES in stream
                        f32 scale,                    # compressionScaleFactor (float32)
                        f32 base,                     # compressionBase (float32)
                        f32[::1] arrayout,            # decoded floats
                        int32_t[::1] sizeout,         # receives decoded length
                        f32 undefined_float) nogil:   # e.g., -1.0e30f
    """
    HEC-style RLE decoding:
      literal: (val & 0x8000) == 0
      -1 run : (val & 0xC000) == 0xC000
      0  run : (val & 0xC000) == 0x8000
    Post-process:
      tmp < 0 -> undefined_float; else tmp/scale + base
    """
    cdef:
        Py_ssize_t nshorts = bytesin // 2
        Py_ssize_t i = 0
        Py_ssize_t out_i = 0
        int tag, cnt
        int16_t sval
        f32 tmp

    if sizeout.shape[0] < 1:
        return -1
    if nshorts > arrayin.shape[0]:
        nshorts = arrayin.shape[0]

    while i < nshorts:
        sval = arrayin[i]
        i += 1
        tag = (<int>sval) & 0xC000

        if (sval & 0x8000) == 0x0000:
            if out_i >= arrayout.shape[0]:
                return -1
            arrayout[out_i] = <f32>(sval)
            out_i += 1

        elif tag == 0xC000:
            cnt = (<int>sval) & 0x3FFF
            if out_i + cnt > arrayout.shape[0]:
                return -1
            while cnt > 0:
                arrayout[out_i] = <f32>-1.0
                out_i += 1
                cnt -= 1

        elif tag == 0x8000:
            cnt = (<int>sval) & 0x3FFF
            if out_i + cnt > arrayout.shape[0]:
                return -1
            while cnt > 0:
                arrayout[out_i] = <f32>0.0
                out_i += 1
                cnt -= 1

        # else: ignore (shouldn't happen)

    # post-scale
    cdef Py_ssize_t k
    for k in range(out_i):
        tmp = arrayout[k]
        if tmp < <f32>0.0:
            arrayout[k] = undefined_float
        else:
            arrayout[k] = <f32>(tmp / scale + base)

    sizeout[0] = <int32_t>out_i
    return 0