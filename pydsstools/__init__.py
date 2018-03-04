"""
Copyright (c) 2017 Gyan Basyal

"""
import ctypes
import os
import sys
import logging

__all__ = ["_heclib","str2ascii"]

_heclib = None

dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"gheclib")

try:
    _heclib = ctypes.cdll.LoadLibrary(dll_path)

except:
    logging.error("Error loading heclib shared library",exc_info=True)
    _heclib = None

else:
    pass


def str2ascii(file):
    if isinstance(file,str):
        return file.encode('ascii')
    elif isinstance(file,bytes):
        return file
    else:
        logging.error("Wrong filename or encoding (not ascii or byte) ")


del ctypes,os
