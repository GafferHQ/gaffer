//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

// Reproduce Python's main executable found in `Programs/python.c` of CPython.
// Conceptually, Gaffer is just a Python process, and in an ideal world would
// run using a vanilla Python executable. But in practice we use our own
// derivative which provides the following benefits :
//   - A readily identifiable process name (gaffer rather than python).
//   - Control over what libraries the main executable links to, for example
//     libstdc++ and custom allocators.

#include "Python.h"

#include <filesystem>
#include <functional>
#include <vector>

#ifdef MS_WINDOWS

// Replace the standard Windows allocators with TBB allocators
// which are much faster for heavily threaded applications.
// The header includes MSVC linker `pragma` preprocessor directives
// to link to the appropriate libraries.
#include "tbb/tbbmalloc_proxy.h"

#include <iostream>

#endif

namespace
{

template<typename T>
int launchGaffer( int argc, T** argv )
{
	// This executable should be run after the environment is configured. The default launch
	// script does that in `_gaffer.py`. We want all of our processes to be called `gaffer`
	// (`gaffer.exe` on Windows). Windows does not support process renaming or replacing a
	// parent process with its child, so this executable, rather than `python` is used to
	// launch the Gaffer application (`__gaffer.py`).

	std::vector<T *> modifiedArgv( argv, argv + argc );

	std::filesystem::path exePath( argv[0] );
	std::filesystem::path launchScriptPath = exePath.parent_path() / "__gaffer.py";
	std::basic_string<T> genericLaunchScriptPath = launchScriptPath.generic_string<T>();
	T *script = genericLaunchScriptPath.data();
	modifiedArgv.insert( modifiedArgv.begin() + 1, script );

	PyStatus status;

	PyConfig config;
	PyConfig_InitPythonConfig( &config );

	// `config.executable` is the source of Python's `sys.executable` value. We set
	// that to `python` (in the exception handling block below) to allow subprocesses
	// to be launched using `sys.executable` and not have to work around the automatic
	// insertion of `__gaffer.py` done above.
	std::filesystem::path pythonPath = exePath.parent_path().parent_path() / "python";
#ifdef MS_WINDOWS
	pythonPath.replace_extension( "exe" );
#endif
	std::wstring pythonPathString = pythonPath.wstring();

	try
	{
		// `PyConfig_Set*Argv` takes care of Python's preconfiguration.
		if constexpr( std::is_same_v<T, char> )
		{
			status = PyConfig_SetBytesArgv( &config, modifiedArgv.size(), modifiedArgv.data() );
		}
		else if constexpr( std::is_same_v<T, wchar_t> )
		{
			status = PyConfig_SetArgv( &config, modifiedArgv.size(), modifiedArgv.data() );
		}
		if( PyStatus_Exception( status ) )
		{
			throw std::runtime_error( "Error initializing command line arguments." );
		}

		status = PyConfig_SetString( &config, &config.executable, pythonPathString.data() );
		if( PyStatus_Exception( status ) )
		{
			throw std::runtime_error( "Error initializing \"sys.executable\"." );
		}

		status = Py_InitializeFromConfig( &config );
		if( PyStatus_Exception( status ) )
		{
			throw std::runtime_error( "Error initializing Python configuration." );
		}
	}
	catch( const std::runtime_error &e )
	{
		std::string msg = std::string( e.what() ) + " : " + std::string( status.err_msg );
		status.err_msg = msg.data();
		PyConfig_Clear( &config );
		if( PyStatus_IsExit( status ) )
		{
			return status.exitcode;
		}
		Py_ExitStatusException( status );
	}

	PyConfig_Clear( &config );

	return Py_RunMain();

}

}  // namespace

#ifdef MS_WINDOWS

int wmain( int argc, wchar_t **argv )
{
	// Verify that the TBB allocator has been registered.
	char **replacementLog;
	int replacementStatus = TBB_malloc_replacement_log( &replacementLog );

	if( replacementStatus != 0 )
	{
		std::cerr << "gaffer.exe : Failed to install TBB memory allocator. Performance may be degraded.\n";
		for( char **logEntry = replacementLog; *logEntry != 0; logEntry++ )
		{
			std::cerr << "gaffer.exe : " << *logEntry << "\n";
		}
	}

	return launchGaffer<wchar_t>( argc, argv );

}
#else
int main( int argc, char **argv )
{
	return launchGaffer<char>( argc, argv );
}
#endif
