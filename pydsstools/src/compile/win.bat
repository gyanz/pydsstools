@echo on
set CWD=%~dp0
set "DSS7_ROOT=..\..\..\..\..\..\..\"
FOR /F %%i IN ("%DSS7_ROOT%") DO (set "DSS7_ROOT=%%~fi")
::set PYTHONHOME=%DSS7_ROOT%\python\repository\cpython\
set "PYTHON_PREFIX=%DSS7_ROOT%\python\repository\%~4\cpython"
set PY_MAJOR=37
set VS_VER=vs_2017

set "py=%~4"
set "py=py%py:~-2%"

set ARCH=
set RELEASE=_RELEASE
:: Parse the incoming arguments
if /i "%1"=="win32"       (set ARCH=WIN32)
if /i "%1"=="x32"         (set ARCH=WIN32)
if /i "%1"=="amd64"       (set ARCH=WIN64)
if /i "%1"=="intel64"     (set ARCH=WIN64)
if /i "%1"=="win64"     (set ARCH=WIN64)
if /i "%1"=="x64"         (set ARCH=WIN64)
if /i "%2"=="debug"       (set RELEASE=_DEBUG) else (set RELEASE=_RELEASE)
if /i "%3"==2010      (set VS_VER=vs_2010)
if /i "%3"==VS2010    (set VS_VER=vs_2010)
if /i "%3"==2017      (set VS_VER=vs_2017)
if /i "%3"==VS2017    (set VS_VER=vs_2017)

if %ARCH%==WIN32 (set MACHINE=x86) else (set MACHINE=X64)
if %ARCH%==WIN64 (set ARCH2=AMD64) else (set ARCH2=WIN32)
if %ARCH%==WIN64 (set ARCH3=x64) else (set ARCH3=x86)
if %RELEASE%==_RELEASE (set CHECKSUM=RELEASE) else (set CHECKSUM=DEBUG)


rem del Release\*.*

:: Set compile/link environment
:: --
set "CPROJ=%DSS7_ROOT%\%VS_VER%\c_proj"
set "DSS7_INCL=%CPROJ%\headers"
if /i %ARCH%==WIN64 (set "DSS7_LIB=../../../../../../c_proj/%ARCH%")
if /i %ARCH%==WIN64 (set "DSS7_INTEL_LIB=../../../../../../c_proj/intel/%ARCH%")
if /i %ARCH%==WIN32 (set "DSS7_LIB=../../../../../../c_proj/%ARCH%")
if /i %ARCH%==WIN32 (set "DSS7_INTEL_LIB=../../../../../../c_proj/intel/%ARCH%")
:: --
set "ZLIB_INCL=../../../../../../extra/zlib-1.2.11"
set "ZLIB_LIB=../../../../../../extra/zlib-1.2.11"
:: --
set "PY_LIB=../../../../../../../python/repository/%~4/cpython/PCbuild/%ARCH2%"
set "PY_INCL=%PYTHON_PREFIX%\include"
set "PY_PC_INCL=%PYTHON_PREFIX%\PC"
set "PY_NPY_INCL=%PYTHON_PREFIX%\Lib\site-packages\numpy\core\include" 
:: --


:: Input/Output files
set "test_pydss=test_pydss"
set ext_name=core_heclib

:: if /i %RELEASE%==_RELEASE (set "DEST_FOLDER=%ARCH%\release") else (set "DEST_FOLDER=%ARCH%\debug")
:: if /i "%~4"==""      (echo "Default Destination for PYD") else (if /i %RELEASE%==_RELEASE (set "DEST_FOLDER=%ARCH%\%~4\release") else (set "DEST_FOLDER=%ARCH%\%~4\debug"))  
set "DEST_FOLDER=..\..\_lib\%ARCH3%\%py%"
if not exist %DEST_FOLDER% (mkdir %DEST_FOLDER%)
set "PY_SRC_FOLDER=..\"
set "py_src_file=%PY_SRC_FOLDER%\%ext_name%.pyx" 
set "C_SRC_FOLDER=%DEST_FOLDER%\doc"
if not exist %C_SRC_FOLDER% (mkdir %C_SRC_FOLDER%)
set c_ext_file=%C_SRC_FOLDER%\%ext_name%.c
set "obj_file=%DEST_FOLDER%\%ext_name%.obj"
set "ext_module=%DEST_FOLDER%\%ext_name%.pyd"

:: clean up
del /Q "%DEST_FOLDER%\*.pyd"
del /Q "%DEST_FOLDER%\*.obj"
del /Q "%DEST_FOLDER%\*.manifest"
del /Q "%DEST_FOLDER%\*.exp"
del /Q "%DEST_FOLDER%\*.lib"
del /Q "%C_SRC_FOLDER%\*.c"
del /Q "%C_SRC_FOLDER%\*.html"


:: cythonize extension file
if "%DSS7_ENV%"=="1" (echo DSS7 Python Path already defined!!!) else (set "PATH=%PYTHON_PREFIX%;%PYTHON_PREFIX%\Scripts;%PATH%")
set DSS7_ENV=1
cython -a -3 "%py_src_file%" -o "%c_ext_file%"  

:: Compilation
if /i %RELEASE%==_RELEASE ( 
 cl /c /I"%PY_INCL%" /I"%DSS7_INCL%" /I"%PY_NPY_INCL%" /I"%PY_PC_INCL%" /I"%ZLIB_INCL%" /nologo /W3 /O2 /WX- /D %ARCH% /D %RELEASE% /D _CONSOLE /D _WINDLL /D _UNICODE /D UNICODE /GL /EHsc /MD /GS /fp:precise /Zc:wchar_t /Zc:forScope /Fo%obj_file% /Fd"%DEST_FOLDER%\\" /Gd /TC /analyze- /errorReport:prompt %c_ext_file%) else (
 cl /c /I"%PY_INCL%" /I"%DSS7_INCL%" /I"%PY_NPY_INCL%" /I"%PY_PC_INCL%" /I"%ZLIB_INCL%" /nologo /W3 /WX- /Od /D %ARCH% /D %RELEASE% /D _CONSOLE /D _WINDLL /D _UNICODE /D UNICODE /Gm /Zi /EHsc /MDd /GS /fp:precise /Zc:wchar_t /Zc:forScope /Fo%obj_file% /Fd"%DEST_FOLDER%\\" /Gd /TC /analyze- /errorReport:prompt %c_ext_file%)



:: Linking
::link /OUT:%ext_module% /NOLOGO /LIBPATH:"%DSS7_LIB%" /LIBPATH:"%DSS7_INTEL_LIB%" /LIBPATH:"%PY_LIB%" heclib_c_v6v7.lib heclib_f_v6v7.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /NODEFAULTLIB:LIBCMTD.lib /MANIFEST /%CHECKSUM% /PDB:"%DEST_FOLDER%\" /SUBSYSTEM:CONSOLE /TLBID:1 /DYNAMICBASE /NXCOMPAT /MACHINE:%MACHINE% /DLL "%obj_file%"

link /OUT:"%ext_module%" /NOLOGO /VERBOSE /LIBPATH:"%DSS7_LIB%" /LIBPATH:"%PY_LIB%" /LIBPATH:"%ZLIB_LIB%" heclib_c_v6v7.lib heclib_f_v6v7.lib zlibstatic.lib /NODEFAULTLIB:MSVCRT.lib /MANIFEST /%CHECKSUM% /PDB:"%DEST_FOLDER%\\" /SUBSYSTEM:CONSOLE /TLBID:1 /DYNAMICBASE /NXCOMPAT /MACHINE:%MACHINE% /DLL "%obj_file%"


