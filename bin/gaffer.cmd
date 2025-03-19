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

set OIIO_LOAD_DLLS_FROM_PATH=0

call :prependToPath "%GAFFER_ROOT%\resources\IECoreUSD" PXR_PLUGINPATH_NAME
call :prependToPath "%GAFFER_ROOT%\materialX" PXR_MTLX_STDLIB_SEARCH_PATHS
rem Prevent USD from adding entries from `PATH` to Python binary search paths.
if "%PXR_USD_WINDOWS_DLL_PATH%" EQU "" (
	set PXR_USD_WINDOWS_DLL_PATH=""
)

call :prependToPath "%USERPROFILE%\gaffer\apps;%GAFFER_ROOT%\apps" GAFFER_APP_PATHS

call :prependToPath "%USERPROFILE%\gaffer\startup" GAFFER_STARTUP_PATHS
call :appendToPath "%GAFFER_ROOT%\startup" GAFFER_STARTUP_PATHS

call :prependToPath "%GAFFER_ROOT%\graphics" GAFFERUI_IMAGE_PATHS

set OSLHOME=%GAFFER_ROOT%

call :prependToPath "%USERPROFILE%\gaffer\shaders;%GAFFER_ROOT%\shaders" OSL_SHADER_PATHS

set GAFFEROSL_CODE_DIRECTORY=%USERPROFILE%\gaffer\oslCode
call :prependToPath %GAFFEROSL_CODE_DIRECTORY% PATH

set PYTHONHOME=%GAFFER_ROOT%

call :prependToPath "%GAFFER_ROOT%\python" PYTHONPATH

if "%PYTHONNOUSERSITE%" EQU "" (
	REM Prevent Python automatically adding a user-level `site-packages`
	REM directory to the `sys.path`. These frequently contain modules which
	REM conflict with our own. Users who know what they are doing can set
	REM `PYTHONNOUSERSITE=0` before running Gaffer if they want to use
	REM the user directory.
	set PYTHONNOUSERSITE=1
)

call :prependToPath "%GAFFER_ROOT%\lib" PATH

set QT_OPENGL=desktop
set QT_QPA_PLATFORM_PLUGIN_PATH=%GAFFER_ROOT%\qt\plugins

call :prependToPath "%GAFFER_ROOT%\bin" PATH

if "%GAFFER_DEBUG%" NEQ "" (
	%GAFFER_DEBUGGER% "%GAFFER_ROOT%"\bin\python.exe "%GAFFER_ROOT%"/bin/_gaffer.py %*
) else (
	"%GAFFER_ROOT%"\bin\python.exe "%GAFFER_ROOT%"/bin/_gaffer.py %*
)

ENDLOCAL
exit /B %ERRORLEVEL%

:prependToPath
	set NewValue=%~1
	set ExistingValue=!%~2!
    if "!ExistingValue!" NEQ "" (
        set ReplacedValue=!ExistingValue:%NewValue%=!
        if /I "!ExistingValue!" == "!ReplacedValue!" (
            set "%~2=!NewValue!;!ExistingValue!"
        )
    ) else (
        set "%~2=%~1"
    )
	exit /B 0

:appendToPath
    set NewValue=%~1
	set ExistingValue=!%~2!
    if "!ExistingValue!" NEQ "" (
        set ReplacedValue=!ExistingValue:%NewValue%=!
        if /I "!ExistingValue!" == "!ReplacedValue!" (
            set "%~2=!ExistingValue!;!NewValue!"
        )
    ) else (
        set "%~2=%~1"
    )
	exit /B 0
