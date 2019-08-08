@echo on
set CWD=%~dp0
set "DSS7_ROOT=%CWD%..\..\..\..\..\..\..\"
set "PYTHON_PREFIX=%DSS7_ROOT%\python\repository\cpython37\cpython"
set PY_MAJOR=37
set VS_VER=vs_2017


if "%DSS7_ENV%"=="1" (echo DSS7 Python Path already defined!!!) else (FOR /F %%i IN ("%PYTHON_PREFIX%") DO (set "PATH=%%~fi;%%~fi\Scripts;%PATH%"))
 
