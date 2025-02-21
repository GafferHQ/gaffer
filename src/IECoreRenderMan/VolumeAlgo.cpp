
//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GeometryAlgo.h"

#include "IECoreVDB/VDBObject.h"

#include "RixPredefinedStrings.hpp"

#include "fmt/format.h"

using namespace std;
using namespace IECore;
using namespace IECoreVDB;
using namespace IECoreRenderMan;

namespace
{

const RtUString g_implOpenVDB( "blobbydso:impl_openvdb" );

RtUString convertVDBObject( const IECoreVDB::VDBObject *vdbObject, RtPrimVarList &primVars, const std::string &messageContext )
{
	string fileName = vdbObject->fileName();
	if( fileName.empty() || !vdbObject->unmodifiedFromFile() )
	{
		/// \todo Pass in-memory grids via RixStorage. Since we have to
		/// load the grids below anyway, we could possibly always pass via
		/// RixStorage. We'll need to worry about ABI compatibility between
		/// the OpenVDB lib that we use and RenderMan uses though.
		return RtUString();
	}

	primVars.SetString( Rix::k_Ri_type, g_implOpenVDB );
	// Dimensions is a required parameter so we have to set it.
	// I think it is only useful if you want to provide the volume
	// data as a dense grid via primvars. We're providing the data via
	// VDB so can set it all to zeroes.
	const int dimensions[] = { 0, 0, 0 };
	primVars.SetIntegerArray( Rix::k_Ri_dimensions, dimensions, 3 );
	// Because dimensions is 0, all primvar details are size 0 too,
	// except for constant.
	primVars.SetDetail( 1, 0, 0, 0 );

	// Declare primitive variables for each grid, while also trying
	// to find the names of the best grids to use for density and velocity.
	string densityName;
	string velocityName;
	for( const auto &gridName : vdbObject->gridNames() )
	{
		openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( gridName );

		if( grid->isType<openvdb::FloatGrid>() )
		{
			if( gridName == "density" || densityName.empty() )
			{
				// RenderMan docs state that if the grid is a level set, it will
				// get converted to fog automatically. But if the grid doesn't have
				// class metadata, we must apply a suffix to reassure RenderMan that
				// it can treat it as a fog volume directly.
				const string classSuffix = grid->getGridClass() == openvdb::GridClass::GRID_LEVEL_SET ? ":levelset" : ":fogvolume";
				densityName = gridName + classSuffix;
			}
			primVars.SetFloatDetail( RtUString( gridName.c_str() ), nullptr, RtDetailType::k_varying );
		}
		else if( grid->isType<openvdb::Vec3fGrid>() )
		{
			if( gridName == "velocity" || gridName == "vel" || gridName == "v" )
			{
				// Velocity must be a fog volume, and if untagged as such in the file,
				// we have to add a suffix to reassure RenderMan.
				velocityName = gridName + ":fogvolume";
			}
			primVars.SetVectorDetail( RtUString( gridName.c_str() ), nullptr, RtDetailType::k_varying );
		}
		else
		{
			IECore::msg(
				IECore::Msg::Warning, messageContext,
				fmt::format(
					"Ignoring grid \"{}\" with unsupported type \"{}\"",
					gridName, grid->valueType()
				)
			);
		}
	}

	if( densityName.empty() )
	{
		IECore::msg( IECore::Msg::Warning, messageContext, "No density field found" );
		return RtUString();
	}

	std::array<RtUString, 4> stringArgs = {
		RtUString( fileName.c_str() ),
		RtUString( densityName.c_str() ),
		RtUString( velocityName.c_str() ),
		/// \todo It is possible to send additional parameters via a little JSON
		/// dictionary - `filterWidth`, `velocityScale`, `densityMult` and `densityRolloff`.
		/// Where would we get those from? Attributes perhaps?
		RtUString( "{}" )
	};
	primVars.SetStringArray( Rix::k_blobbydso_stringargs, stringArgs.data(), stringArgs.size() );

	return Rix::k_Ri_Volume;
}

GeometryAlgo::ConverterDescription<VDBObject> g_meshConverterDescription( convertVDBObject );

} // namespace
