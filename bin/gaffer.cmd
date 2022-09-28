@echo off

setlocal EnableDelayedExpansion

set GAFFER_ROOT=%~dp0%..
set "GAFFER_ROOT=%GAFFER_ROOT:\=/%"

set HOME=%USERPROFILE%

set GAFFER_JEMALLOC=0

call :prependToPath "%GAFFER_ROOT%\glsl" IECOREGL_SHADER_PATHS
call :prependToPath "%GAFFER_ROOT%\glsl" IECOREGL_SHADER_INCLUDE_PATHS

call :prependToPath "%GAFFER_ROOT%\fonts" IECORE_FONT_PATHS
call :prependToPath "%GAFFER_ROOT%\ops" IECORE_OP_PATHS

call :prependToPath "%USERPROFILE%\gaffer\opPresets;%GAFFER_ROOT%\opPresets" IECORE_OP_PRESET_PATHS
call :prependToPath "%USERPROFILE%\gaffer\procedurals;%GAFFER_ROOT%\procedurals" IECORE_PROCEDURAL_PATHS
call :prependToPath "%USERPROFILE%\gaffer\proceduralPresets;%GAFFER_ROOT%\proceduralPresets" IECORE_PROCEDURAL_PRESET_PATHS

set CORTEX_POINTDISTRIBUTION_TILESET=%GAFFER_ROOT%\resources\cortex\tileset_2048.dat

call :prependToPath "%USERPROFILE%\gaffer\apps;%GAFFER_ROOT%\apps" GAFFER_APP_PATHS

call :prependToPath "%USERPROFILE%\gaffer\startup" GAFFER_STARTUP_PATHS
call :appendToPath "%GAFFER_ROOT%\startup" GAFFER_STARTUP_PATHS

call :prependToPath "%GAFFER_ROOT%\graphics" GAFFERUI_IMAGE_PATHS

set OSLHOME=%GAFFER_ROOT%

call :prependToPath "%USERPROFILE%\gaffer\shaders;%GAFFER_ROOT%\shaders" OSL_SHADER_PATHS

set GAFFEROSL_CODE_DIRECTORY="%USERPROFILE%\gaffer\oslCode"
call :prependToPath %GAFFEROSL_CODE_DIRECTORY% PATH

set PYTHONHOME=%GAFFER_ROOT%

call :prependToPath "%GAFFER_ROOT%\python" PYTHONPATH

call :prependToPath "%GAFFER_ROOT%\lib" PATH

set QT_OPENGL=desktop
set QT_QPA_PLATFORM_PLUGIN_PATH=%GAFFER_ROOT%\qt\plugins

call :prependToPath "%GAFFER_ROOT%\bin" PATH

if "%OCIO%" EQU "" (
	set OCIO=%GAFFER_ROOT%\openColorIO\config.ocio
)

rem Appleseed
rem if "%APPLESEED%" == "" (
rem 	if EXIST "%GAFFER_ROOT%"\appleseed (
rem 		set APPLESEED=%GAFFER_ROOT%\appleseed
rem 	)
rem )

rem if "%APPLESEED%" NEQ "" (
rem 	call :prependToPath "%APPLESEED%\shaders\gaffer" OSL_SHADER_PATHS
rem 	call :prependToPath "%APPLESEED%\shaders\appleseed" OSL_SHADER_PATHS
rem )

rem if "%APPLESEED%" NEQ "" (
rem 	call :prependToPath "%APPLESEED%\bin;%APPLESEED%\lib" PATH
rem 	call :prependToPath "%APPLESEED%\lib\python2.7" PYTHONPATH
rem 	call :prependToPath "%OSL_SHADER_PATHS%;%GAFFER_ROOT%\appleseedDisplays" APPLESEED_SEARCHPATH
rem )

rem Arnold
if "%ARNOLD_ROOT%" NEQ "" (
	call :appendToPath "%ARNOLD_ROOT%\bin" PATH
	call :appendToPath "%ARNOLD_ROOT%\python" PYTHONPATH

	if exist "%ARNOLD_ROOT%\include\ai_version.h" (
		for /f "tokens=3" %%A in ('findstr /R /C:"#define *AI_VERSION_ARCH_NUM" "%ARNOLD_ROOT%\include\ai_version.h"') do (
			set ARNOLD_ARCH_NUM=%%A
		)
		for /f "tokens=3" %%A in ('findstr /R /C:"#define *AI_VERSION_MAJOR_NUM" "%ARNOLD_ROOT%\include\ai_version.h"') do (
			set ARNOLD_VERSION_NUM=%%A
		)

		set ARNOLD_VERSION=!ARNOLD_ARCH_NUM!.!ARNOLD_VERSION_NUM!
		if exist "%GAFFER_ROOT%\arnold\%ARNOLD_VERSION%" (
			call :prependToPath "%GAFFER_ROOT%\arnold\!ARNOLD_VERSION!" GAFFER_EXTENSION_PATHS
			call :prependToPath "%GAFFER_ROOT%\arnold\!ARNOLD_VERSION!\arnoldPlugins" ARNOLD_PLUGIN_PATH
			call :prependToPath "%ARNOLD_ROOT%\plugins" ARNOLD_PLUGIN_PATH
		) else (
			echo WARNING : GafferArnold extension not available for Arnold %ARNOLD_VERSION%
		)
	) else (
		echo WARNING : Unable to determine Arnold version
	)
)

rem 3Delight
if "%DELIGHT%" NEQ "" (
	call :appendToPath "%DELIGHT%\bin" PATH
	call :appendToPath "%DELIGHT%\python" PYTHONPATH
	call :appendToPath "%DELIGHT%\shaders" DL_SHADERS_PATH
	call :appendToPath "%DELIGHT%\displays" DL_DISPLAYS_PATH
	
	call :appendToPath "%DELIGHT%" OSL_SHADER_PATHS

	call :appendToPath "%GAFFER_ROOT%\renderMan\displayDrivers" DL_RESOURCES_PATH
)

rem Set up 3rd party extensions
rem Batch files are awkward at `for` loops. The default `for`, without `/f`
rem uses semi-colons AND spaces as delimiters, meaning we would not be able
rem to support spaces in extension paths. Bad. Using the `/f` switch lets
rem us specify the delimiter, but it then separates the tokens into a
rem set number that must be known ahead of time (i.e. %%A, %%B, etc.).
rem The accepted pattern seems to be to use recursion to pop the first token
rem then recurse through the remaining tokens until there are none left.

set EXTENSION_PATH=%GAFFER_EXTENSION_PATHS%
:NextPath
for /f "tokens=1* delims=;" %%A in ("%EXTENSION_PATH%") do (
	if "%%A" NEQ "" (
		call :appendToPath "%%A\bin" PATH
		call :appendToPath "%%A\lib" PATH
		call :appendToPath "%%A\python" PYTHONPATH
		call :appendToPath "%%A\apps" GAFFER_APP_PATHS
		call :appendToPath "%%A\graphics" GAFFERUI_IMAGE_PATHS
		call :appendToPath "%%A\glsl" IECOREGL_SHADER_PATHS
		call :appendToPath "%%A\glsl" IECOREGL_SHADER_INCLUDE_PATHS
		call :appendToPath "%%A\shaders" OSL_SHADER_PATHS
		call :prependToPath "%%A\startup" GAFFER_STARTUP_PATHS
	)
	if "%%B" NEQ "" (
		set EXTENSION_PATH=%%B
		goto :NextPath
	)
)

if "%GAFFER_DEBUG%" NEQ "" (
	%GAFFER_DEBUGGER% /debugexe "%GAFFER_ROOT%\bin\python.exe" "%GAFFER_ROOT%"/bin/__gaffer.py %*
) else (
	"%GAFFER_ROOT%"\bin\python.exe "%GAFFER_ROOT%"/bin/__gaffer.py %*
)

if %ERRORLEVEL% NEQ 0 (
	echo "Error(s) running Gaffer"
	exit /B %ERRORLEVEL%
)

ENDLOCAL
exit /B 0

:prependToPath
	set NewValue=%~1
	set ExistingValue=!%~2!
    if "%ExistingValue%" NEQ "" (
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
    if "%ExistingValue%" NEQ "" (
        set ReplacedValue=!ExistingValue:%NewValue%=!
        if /I "!ExistingValue!" == "!ReplacedValue!" (
            set "%~2=!ExistingValue!;!NewValue!"
        )
    ) else (
        set "%~2=%~1"
    )
	exit /B 0
