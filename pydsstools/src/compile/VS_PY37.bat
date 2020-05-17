%comspec% /k "C:\Program Files (x86)\IntelSWTools\compilers_and_libraries\windows\bin\ipsxe-comp-vars.bat" intel64
:: CALL "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\VC\Auxiliary\Build\vcvarsx86_amd64.bat"
:: Win 10 SDK, version 1809 = 10.0.17763.0 
CALL "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsx86_amd64.bat" 10.0.17763.0 -vcvars_ver=14.16 
