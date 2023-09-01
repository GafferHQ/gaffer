//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "IECoreVDB/VDBObject.h"

#include "IECoreDelight/NodeAlgo.h"
#include "IECoreDelight/ParameterList.h"

#include "fmt/format.h"

#include <unordered_set>

using namespace IECoreDelight;

static std::vector<std::pair<std::string, std::vector<std::string>>> g_gridCandidates = {
	{ "densitygrid", { "density", "dens" } },
	{ "colorgrid", { "color", "c", "col", "Cd", "Cs" } },
	{ "temperaturegrid", { "temperature", "temp" } },
	{ "emissionintensitygrid", { "emissionintensity", "emissionIntensity", "emission_intensity" } },
	{ "emissiongrid", { "emission" } },
	{ "velocitygrid", { "velocity", "vel", "v" } }
};

namespace
{

bool convert( const IECoreVDB::VDBObject *object, NSIContext_t context, const char *handle )
{
	ParameterList parameters;

	if( !object->unmodifiedFromFile() )
	{
		IECore::msg( IECore::Msg::Warning, "IECoreDelight", "Modified VDB data is not supported" );
		return false;
	}

	std::vector<std::string> gridNames = object->gridNames();
	std::unordered_set<std::string> gridNameSet( gridNames.begin(), gridNames.end() );

	for( const auto &[grid, candidates] : g_gridCandidates )
	{
		for( const auto &candidate : candidates )
		{
			if( gridNameSet.find( candidate ) != gridNameSet.end() )
			{
				parameters.add( grid.c_str(), candidate );
				break;
			}
		}
	}

	const std::string fileName = object->fileName();

	if( !parameters.size() )
	{
		IECore::msg( IECore::Msg::Warning, "IECoreDelight", fmt::format( "No grids recognized in \"{}\"", fileName ) );
		return false;
	}

	parameters.add( "vdbfilename", fileName );

	NSICreate( context, handle, "volume", 0, nullptr );
	NSISetAttribute( context, handle, parameters.size(), parameters.data() );

	return true;
}

NodeAlgo::ConverterDescription<IECoreVDB::VDBObject> g_description( convert );

}  // namespace