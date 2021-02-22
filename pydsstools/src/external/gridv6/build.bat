@echo off
set dir=%~dp0
cd "%~dp0"
set "outdir=build"
if "%1"=="clean" goto clean

:build
call "%dir%find_msbuild.bat"
%MSBuild% grid.sln /p:Configuration=Release;Platform=x64
IF not exist %outdir% (mkdir %outdir%)
xcopy x64\release\grid.lib %outdir%\ /Y
exit /b %ERRORLEVEL%

:clean
echo removing x64, build folders
rmdir /s /q x64
