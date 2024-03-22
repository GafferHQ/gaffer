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

#include "fmt/format.h"

#include <filesystem>

namespace
{

// Version
std::string cyclesVersion = CYCLES_VERSION_STRING;
// Store devices once
std::vector<ccl::DeviceInfo> cyclesDevices;

}

namespace IECoreCycles
{

bool init()
{
	const char *cyclesRoot = getenv( "CYCLES_ROOT" );
	if( !cyclesRoot )
	{
		IECore::msg( IECore::Msg::Error, "IECoreCycles::init", "CYCLES_ROOT environment variable not set" );
		return false;
	}

	auto kernelFile = std::filesystem::path( cyclesRoot ) / "source" / "kernel" / "types.h";
	if( !std::filesystem::is_regular_file( kernelFile ) )
	{
		IECore::msg( IECore::Msg::Error, "IECoreCycles::init", fmt::format( "File \"{}\" not found", kernelFile ) );
		return false;
	}

	ccl::path_init( cyclesRoot );

	// This is a global thing for logging
	const char* argv[] = { "-", "v", "1" };
	ccl::util_logging_init( argv[0] );
	ccl::util_logging_start();
	ccl::util_logging_verbosity_set( 0 );

	// Get devices
	ccl::vector<ccl::DeviceInfo> devices = ccl::Device::available_devices();
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

std::vector<ccl::DeviceInfo> &devices()
{
	return cyclesDevices;
}

}
