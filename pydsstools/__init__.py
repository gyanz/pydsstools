"""
Copyright (c) 2017 Gyan Basyal

"""
import os
import logging

__version__ = '1.6'

__all__ = ["str2ascii","__version__"]

def str2ascii(file):
    if isinstance(file,str):
        return file.encode('ascii')
    elif isinstance(file,bytes):
        return file
    else:
        logging.error("Wrong filename or encoding (not ascii or byte) ")


del os
