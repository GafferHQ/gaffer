@echo off

rem Public-facing launch script for gaffer. This sets up the Python interpreter
rem and then defers to `_gaffer.py` to set up the appropriate environment
rem and finally launch `__gaffer.py`.
rem
rem \todo Move all remaining environment setup to `_gaffer.py`.

setlocal EnableDelayedExpansion

set GAFFER_ROOT=%~dp0%..
set "GAFFER_ROOT=%GAFFER_ROOT:\=/%"

set "HOME=%USERPROFILE:\=/%"

set PYTHONHOME=%GAFFER_ROOT%

if "%PYTHONNOUSERSITE%" EQU "" (
	REM Prevent Python automatically adding a user-level `site-packages`
	REM directory to the `sys.path`. These frequently contain modules which
	REM conflict with our own. Users who know what they are doing can set
	REM `PYTHONNOUSERSITE=0` before running Gaffer if they want to use
	REM the user directory.
	set PYTHONNOUSERSITE=1
)

if "%GAFFER_DEBUG%" NEQ "" (
	%GAFFER_DEBUGGER% "%GAFFER_ROOT%"\bin\python.exe "%GAFFER_ROOT%"/bin/_gaffer.py %*
) else (
	"%GAFFER_ROOT%"\bin\python.exe "%GAFFER_ROOT%"/bin/_gaffer.py %*
)

ENDLOCAL
exit /B %ERRORLEVEL%
