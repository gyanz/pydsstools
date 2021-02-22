@echo off
set dir=%~dp0
cd "%~dp0"
if "%1"=="clean" goto clean

:build
call "%dir%find_msbuild.bat"
%MSBuild% grid.sln /p:Configuration=Release;Platform=x64
xcopy x64\release\grid.lib build\ /Y
exit /b %ERRORLEVEL%

:clean
echo removing x64, build folders
rmdir /s /q x64
