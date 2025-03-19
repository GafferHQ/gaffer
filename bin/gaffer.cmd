@echo off

rem Public-facing launch script for gaffer. This sets up the Python interpreter
rem and then defers to `_gaffer.py` to set up the appropriate environment
rem and finally launch `__gaffer.py`.

setlocal EnableDelayedExpansion

set GAFFER_ROOT=%~dp0%..
set "GAFFER_ROOT=%GAFFER_ROOT:\=/%"

set "HOME=%USERPROFILE:\=/%"

set PYTHONHOME=%GAFFER_ROOT%

if "%GAFFER_DEBUG%" NEQ "" (
	%GAFFER_DEBUGGER% "%GAFFER_ROOT%"\bin\python.exe "%GAFFER_ROOT%"/bin/_gaffer.py %*
) else (
	"%GAFFER_ROOT%"\bin\python.exe "%GAFFER_ROOT%"/bin/_gaffer.py %*
)

ENDLOCAL
exit /B %ERRORLEVEL%
