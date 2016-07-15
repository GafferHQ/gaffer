//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR43

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

#include "boost/assign/list_of.hpp"
#include "boost/container/flat_set.hpp"

#include "IECore/MessageHandler.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/StringPlug.h"

#include "GafferArnold/ParameterHandler.h"

using namespace Imath;
using namespace boost;
using namespace IECore;
using namespace Gaffer;
using namespace GafferArnold;

Gaffer::Plug *ParameterHandler::setupPlug( const AtParamEntry *parameter, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	std::string name = AiParamGetName( parameter );

	PlugPtr plug = 0;
	switch( AiParamGetType( parameter ) )
	{
		case AI_TYPE_BYTE :

			plug = new IntPlug(
				name,
				direction,
				AiParamGetDefault( parameter )->BYTE,
				/* minValue = */ 0,
				/* maxValue = */ 255
			);

			break;

		case AI_TYPE_INT :

			plug = new IntPlug(
				name,
				direction,
				AiParamGetDefault( parameter )->INT
			);

			break;

		case AI_TYPE_UINT :

			plug = new IntPlug(
				name,
				direction,
				AiParamGetDefault( parameter )->UINT,
				/* minValue = */ 0
			);

			break;

		case AI_TYPE_BOOLEAN :

			plug = new BoolPlug(
				name,
				direction,
				AiParamGetDefault( parameter )->BOOL
			);

			break;

		case AI_TYPE_FLOAT :

			plug = new FloatPlug(
				name,
				direction,
				AiParamGetDefault( parameter )->FLT
			);

			break;

		case AI_TYPE_RGB :

			plug = new Color3fPlug(
				name,
				direction,
				Color3f(
					AiParamGetDefault( parameter )->RGB.r,
					AiParamGetDefault( parameter )->RGB.g,
					AiParamGetDefault( parameter )->RGB.b
				)
			);

			break;

		case AI_TYPE_RGBA :

			plug = new Color4fPlug(
				name,
				direction,
				Color4f(
					AiParamGetDefault( parameter )->RGBA.r,
					AiParamGetDefault( parameter )->RGBA.g,
					AiParamGetDefault( parameter )->RGBA.b,
					AiParamGetDefault( parameter )->RGBA.a
				)
			);

			break;

		case AI_TYPE_POINT2 :

			plug = new V2fPlug(
				name,
				direction,
				V2f(
					AiParamGetDefault( parameter )->PNT2.x,
					AiParamGetDefault( parameter )->PNT2.y
				)
			);

			break;

		case AI_TYPE_POINT :

			plug = new V3fPlug(
				name,
				direction,
				V3f(
					AiParamGetDefault( parameter )->PNT.x,
					AiParamGetDefault( parameter )->PNT.y,
					AiParamGetDefault( parameter )->PNT.z
				)
			);

			break;

		case AI_TYPE_VECTOR :

			plug = new V3fPlug(
				name,
				direction,
				V3f(
					AiParamGetDefault( parameter )->VEC.x,
					AiParamGetDefault( parameter )->VEC.y,
					AiParamGetDefault( parameter )->VEC.z
				)
			);

			break;

		case AI_TYPE_ENUM :

			{
				AtEnum e = AiParamGetEnum( parameter );
				plug = new StringPlug(
					name,
					direction,
					AiEnumGetString( e, AiParamGetDefault( parameter )->INT )
				);

			}
			break;

		case AI_TYPE_STRING :

			{
				plug = new StringPlug(
					name,
					direction,
					AiParamGetDefault( parameter )->STR
				);

			}
			break;

		case AI_TYPE_MATRIX :

			{

				M44f defaultValue( *AiParamGetDefault( parameter )->pMTX );
				plug = new M44fPlug(
					name,
					direction,
					defaultValue
				);

			}

	}

	if( plug )
	{
		plug->setFlags( Plug::Dynamic, true );
		plugParent->addChild( plug );
	}
	else
	{
		msg(
			Msg::Warning,
			"GafferArnold::ParameterHandler::setupPlug",
			format( "Unsupported parameter \"%s\" of type \"%s\"" ) %
				AiParamGetName( parameter ) %
				AiParamGetTypeName( AiParamGetType( parameter ) )
		);
	}

	return plug.get();
}

namespace
{

// Names of parameters which it doesn't make sense to represent
// in Gaffer - typically because they are geometric properties
// of lights which are dealt with separately.
typedef boost::container::flat_set<std::string> ParameterSet;
ParameterSet g_parametersToIgnore = assign::list_of

	( "point_light.position" )
	( "point_light.matrix" )
	( "point_light.filters" )
	( "point_light.time_samples" )

	( "distant_light.matrix" )
	( "distant_light.filters" )
	( "distant_light.time_samples" )

	( "quad_light.vertices" )
	( "quad_light.matrix" )
	( "quad_light.filters" )
	( "quad_light.time_samples" )

	( "spot_light.position" )
	( "spot_light.look_at" )
	( "spot_light.up" )
	( "spot_light.matrix" )
	( "spot_light.filters" )
	( "spot_light.time_samples" )

	( "skydome_light.matrix" )
	( "skydome_light.filters" )
	( "skydome_light.time_samples" )

	( "cylinder_light.bottom" )
	( "cylinder_light.top" )
	( "cylinder_light.matrix" )
	( "cylinder_light.filters" )
	( "cylinder_light.time_samples" )

	( "disk_light.position" )
	( "disk_light.direction" )
	( "disk_light.matrix" )
	( "disk_light.filters" )
	( "disk_light.time_samples" )

	( "mesh_light.mesh" )
	( "mesh_light.matrix" )
	( "mesh_light.filters" )
	( "mesh_light.time_samples" )

	( "photometric_light.matrix" )
	( "photometric_light.filters" )
	( "photometric_light.time_samples" )

;

} // namespace

void ParameterHandler::setupPlugs( const AtNodeEntry *nodeEntry, Gaffer::GraphComponent *plugsParent, Gaffer::Plug::Direction direction )
{
	AtParamIterator *it = AiNodeEntryGetParamIterator( nodeEntry );
	const std::string nodeName = AiNodeEntryGetName( nodeEntry );
	while( const AtParamEntry *param = AiParamIteratorGetNext( it ) )
	{
		std::string name = AiParamGetName( param );
		if( name == "name" )
		{
			continue;
		}

		/// \todo Use a "gaffer.mtd" Arnold metadata file to define the parameters to ignore,
		/// and use that rather than this static list. To do this we need to define a mechanism
		/// by which IECoreArnold::UniverseBlock finds non-standard metadata files to load.
		if( g_parametersToIgnore.find( nodeName + "." + name ) != g_parametersToIgnore.end() )
		{
			continue;
		}

		setupPlug( param, plugsParent, direction );
	}
	AiParamIteratorDestroy( it );
}
