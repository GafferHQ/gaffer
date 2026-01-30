@echo off

rem Public-facing launch script for gaffer. This sets up the Python interpreter
rem and then defers to `_gaffer.py` to set up the appropriate environment
rem and finally launch `__gaffer.py`.

setlocal EnableDelayedExpansion

set "HOME=%USERPROFILE:\=/%"

set PYTHONHOME=%~dp0%..
rem Needed for `gaffer.exe` to find the Python DLLs it needs because they are not in the same directory.
set PATH=%PYTHONHOME%\bin;%PATH%

if "%GAFFER_DEBUG%" NEQ "" (
	%GAFFER_DEBUGGER% "%PYTHONHOME%"\bin\__private\gaffer.exe "%PYTHONHOME%"/bin/__private/_gaffer.py %*
) else (
	"%PYTHONHOME%"\bin\__private\gaffer.exe "%PYTHONHOME%"/bin/__private/_gaffer.py %*
)

endlocal
exit /B %ERRORLEVEL%
