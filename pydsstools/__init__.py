"""
Copyright (c) 2017 Gyan Basyal

"""
import ctypes
import os
import sys
import logging

__version__ = '0.3'

__all__ = ["_heclib","str2ascii","__version__"]

from ._libdll import _heclib

def str2ascii(file):
    if isinstance(file,str):
        return file.encode('ascii')
    elif isinstance(file,bytes):
        return file
    else:
        logging.error("Wrong filename or encoding (not ascii or byte) ")


del ctypes,os
