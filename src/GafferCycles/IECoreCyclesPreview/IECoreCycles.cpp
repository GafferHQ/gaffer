//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Alex Fuller. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferCycles/IECoreCyclesPreview/IECoreCycles.h"

// Cycles
#include "util/log.h"
#include "util/path.h"
#include "util/version.h"

#include "IECore/MessageHandler.h"
#include "IECore/SearchPath.h"

namespace
{

// Version
static std::string cyclesVersion = CYCLES_VERSION_STRING;
// Store devices once
static std::vector<ccl::DeviceInfo> cyclesDevices;

}

namespace IECoreCycles
{

bool init( const char *path )
{
	// Set path to find shaders & cuda cubins
	#ifdef _WIN32
	std::string paths = ccl::string_printf( "%s;%s\\\\cycles;%s", getenv( "GAFFERCYCLES" ), getenv( "GAFFER_ROOT" ), getenv( "GAFFER_EXTENSION_PATHS" ) );
	#else
	std::string paths = ccl::string_printf( "%s:%s/cycles:%s" , getenv( "GAFFERCYCLES" ), getenv( "GAFFER_ROOT" ), getenv( "GAFFER_EXTENSION_PATHS" ) );
	#endif
	// If a path was specified, use that
	if( path )
		paths = path;
	const char *kernelFile = "source/kernel/kernel_globals.h";
	IECore::SearchPath searchPath( paths );
	boost::filesystem::path filepath = searchPath.find( kernelFile );
	if( filepath.empty() )
	{
		IECore::msg( IECore::Msg::Error, "CyclesRenderer", "Cannot find GafferCycles location. Have you set the GAFFERCYCLES environment variable?" );
	}
	else
	{
		std::string cclPath = filepath.string();
		cclPath.erase( cclPath.end() - strlen( kernelFile ), cclPath.end() );
		ccl::path_init( cclPath );
	}

	// This is a global thing for logging
	const char* argv[] = { "-", "v", "1" };
	ccl::util_logging_init( argv[0] );
	ccl::util_logging_start();
	ccl::util_logging_verbosity_set( 0 );

	// Get devies
	ccl::vector<ccl::DeviceInfo> devices = ccl::Device::available_devices( ccl::DEVICE_MASK_CPU | ccl::DEVICE_MASK_HIP | ccl::DEVICE_MASK_CUDA | ccl::DEVICE_MASK_METAL
#ifdef WITH_OPTIX
	| ccl::DEVICE_MASK_OPTIX
#endif
	);
	devices.push_back( ccl::Device::get_multi_device( devices, 0, true ) );

	for( auto device : devices )
	{
		cyclesDevices.push_back( device );
	}

	return true;
}

int majorVersion()
{
	return CYCLES_VERSION_MAJOR;
}

int minorVersion()
{
	return CYCLES_VERSION_MINOR;
}

int patchVersion()
{
	return CYCLES_VERSION_PATCH;
}

const std::string &versionString()
{
	return cyclesVersion;
}

const std::vector<ccl::DeviceInfo> &devices()
{
	return cyclesDevices;
}

}
