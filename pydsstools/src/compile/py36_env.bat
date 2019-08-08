@echo on
set CWD=%~dp0
set "DSS7_ROOT=%CWD%..\..\..\..\..\..\..\"
set "PYTHON_PREFIX=%DSS7_ROOT%\python\repository\cpython36\cpython"


if "%DSS7_ENV%"=="1" (echo DSS7 Python Path already defined!!!) else (FOR /F %%i IN ("%PYTHON_PREFIX%") DO (set "PATH=%%~fi;%%~fi\Scripts;%PATH%"))
 
