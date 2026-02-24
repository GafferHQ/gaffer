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
int launchGaffer( int argc, T** argv, std::function<int( int, T** )> pyMain )
{
	// Windows does not support process renaming or replacing a parent process with its child.
	// We want all of our processes to be called `gaffer` (`gaffer.exe` on Windows) so we run
	// this executable with `_gaffer.py` bootstrap script. We execute that script as-is and
	// all other cases get `__gaffer.py` inserted into the argument list.
	if( argc > 1 && std::filesystem::path( argv[1] ).filename() == std::filesystem::path( "_gaffer.py" ) )
	{
		return pyMain( argc, argv );
	}

	std::vector<T *> modifiedArgv( argv, argv + argc );

	std::filesystem::path exePath( argv[0] );
	std::filesystem::path launchScriptPath = exePath.parent_path() / "__gaffer.py";
	std::basic_string<T> genericLaunchScriptPath = launchScriptPath.generic_string<T>();
	T *script = genericLaunchScriptPath.data();
	modifiedArgv.insert( modifiedArgv.begin() + 1, script );

	return pyMain( modifiedArgv.size(), modifiedArgv.data() );

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

	return launchGaffer<wchar_t>( argc, argv, Py_Main );
	
}
#else
int main( int argc, char **argv )
{
	return launchGaffer<char>( argc, argv, Py_BytesMain );
}
#endif