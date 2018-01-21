"""
"""
import sys
import os
import re
import math
import logging

def fileAndExt(filename):
    # Returns 'file path without extension' and the file extension
    file = filename
    idx = filename[::-1].find(".")
    if idx == -1:
        extension = ''
    else:
        extension = filename[-idx::]
        file = filename[0:-idx-1]
    return file, extension

def DirFileExt(path):
    # returns directory path, filename without extension, and extension
    # does not check if the path is for folder or file
    _dir,filename = os.path.split(path)
    if filename=='':
        logger.error('no filename in the given path')
        return None
    file,extension = fileAndExt(filename)
    return _dir,file,extension

def newFile(filename,added="_copy",ext=None):
    # creates a duplicate filename
    # the filename may have different extension name
    file,extension = fileAndExt(filename)
    if extension == '':
        extension = None
        
    if ext is None:
        if extension is None:
            file = file
        else:
            file =file + "."+extension
    else:
        file = file +added+ "." + ext
    return file



def checkExtension(file_path,ext):
    # check if the file path has particular file extension name
    if not file_path.lower().endswith(ext.lower()):
        return False
    return True

def sorted_nicely( l ): 
    """ Sort the given alpha-numeric iterable in the way that humans expect.""" 
    # By Mark Byers
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

def createFileLogger(file_name, folder_name):
    # Creates log file in %APPDATA% folder (it is window's env variable)
    # full path of log file is %APPDATA%\folder_name\file_name  
    try:
        logFolder = os.path.join(os.getenv('APPDATA'), folder_name) 
        if not os.path.exists(logFolder):
            os.makedirs(logFolder)

        logFile = os.path.join(logFolder, file_name)
        fileHandler = logging.FileHandler(logFile, mode='a')
        logging.getLogger('').addHandler(fileHandler)
        logger.info('Log file at %s', logFile)
    except:
        logger.error('',exc_info=True) 
