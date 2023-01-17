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

#include "GafferCycles/SocketHandler.h"

#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "GafferOSL/ClosurePlug.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/Node.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/SplinePlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/AngleConversion.h"
#include "IECore/MessageHandler.h"

#include "boost/algorithm/string.hpp"
#include "boost/container/flat_set.hpp"

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "kernel/types.h"
#include "util/transform.h"
#include "util/types_float2.h"
#include "util/types_float3.h"
IECORE_POP_DEFAULT_VISIBILITY

using namespace std;
using namespace Imath;
using namespace boost;
using namespace IECore;
using namespace Gaffer;
using namespace GafferCycles;
using namespace IECoreCycles;

namespace
{

template<typename PlugType>
Gaffer::Plug *setupNumericPlug( const ccl::NodeType *nodeType, const ccl::SocketType &socketType, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, typename PlugType::ValueType defaultValue )
{
	using ValueType = typename PlugType::ValueType;

	ValueType minValue = std::numeric_limits<ValueType>::lowest();
	if( socketType.type == ccl::SocketType::UINT )
	{
		minValue = 0;
	}

	string name = boost::replace_first_copy( string( socketType.name.c_str() ), ".", "__" );
	PlugType *existingPlug = plugParent->getChild<PlugType>( name );
	if(
		existingPlug &&
		existingPlug->direction() == direction &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue
	)
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, direction, defaultValue, minValue, std::numeric_limits<ValueType>::max(), Plug::Default );
	PlugAlgo::replacePlug( plugParent, plug );

	return plug.get();
}

Gaffer::Plug *setupNodePlug( const IECore::InternedString &socketName, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	Plug *existingPlug = plugParent->getChild<Plug>( socketName );
	if(
		existingPlug &&
		existingPlug->direction() == direction &&
		existingPlug->typeId() == Plug::staticTypeId()
	)
	{
		existingPlug->setFlags( Gaffer::Plug::Dynamic, false );
		return existingPlug;
	}

	PlugPtr plug = new Plug( socketName, direction, Plug::Default );
	PlugAlgo::replacePlug( plugParent, plug );

	return plug.get();
}

template<typename PlugType>
Gaffer::Plug *setupTypedPlug( const IECore::InternedString &socketName, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, const typename PlugType::ValueType &defaultValue )
{
	string name = boost::replace_first_copy( string( socketName ), ".", "__" );
	PlugType *existingPlug = plugParent->getChild<PlugType>( name );
	if(
		existingPlug &&
		existingPlug->direction() == direction &&
		existingPlug->defaultValue() == defaultValue
	)
	{
		existingPlug->setFlags( Gaffer::Plug::Dynamic, false );
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, direction, defaultValue );

	PlugAlgo::replacePlug( plugParent, plug );

	return plug.get();
}

template<typename PlugType>
Gaffer::Plug *setupTypedPlug( const ccl::NodeType *nodeType, const ccl::SocketType socketType, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, const typename PlugType::ValueType &defaultValue )
{
	return setupTypedPlug<PlugType>( socketType.name.c_str(), plugParent, direction, defaultValue );
}

template<typename PlugType>
Gaffer::Plug *setupColorPlug( const ccl::NodeType *nodeType, const ccl::SocketType socketType, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	using ValueType = typename PlugType::ValueType;
	using BaseType = typename ValueType::BaseType;

	ValueType defaultValue( 1 );
	ccl::float3 *defaultCValue = (ccl::float3*)socketType.default_value;
	defaultValue[0] = defaultCValue->x;
	defaultValue[1] = defaultCValue->y;
	defaultValue[2] = defaultCValue->z;

	ValueType minValue( std::numeric_limits<BaseType>::lowest() );
	ValueType maxValue( std::numeric_limits<BaseType>::max() );

	string name = boost::replace_first_copy( string( socketType.name.c_str() ), ".", "__" );
	PlugType *existingPlug = plugParent->getChild<PlugType>( name );
	if(
		existingPlug &&
		existingPlug->direction() == direction &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue
	)
	{
		existingPlug->setFlags( Gaffer::Plug::Dynamic, false );
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, direction, defaultValue, minValue, maxValue, Plug::Default );
	PlugAlgo::replacePlug( plugParent, plug );

	return plug.get();
}

const string nodeName ( Gaffer::GraphComponent *plugParent )
{
	const Gaffer::Node *node = IECore::runTimeCast<const Gaffer::Node>( plugParent );
	if( !node )
	{
		node = plugParent->ancestor<Gaffer::Node>();
	}

	return node->relativeName( node->scriptNode() );
}

using NodeSocket = std::pair<ccl::ustring, ccl::ustring>;
boost::container::flat_set<NodeSocket> g_socketBlacklist = {
	// This socket is used to provide a list of available UDIMs
	// to Cycles, which unlike other renderers, won't look for them
	// itself. We handle this automatically in ShaderNetworkAlgo, so
	// there is no need to expose the socket to the user.
	{ ccl::ustring( "image_texture" ), ccl::ustring( "tiles" ) }
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace GafferCycles

{

namespace SocketHandler

{

Gaffer::Plug *setupPlug( const IECore::InternedString &socketName, int socketType, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	switch( socketType )
	{
		case ccl::SocketType::COLOR :

			return setupTypedPlug<Color3fPlug>( socketName, plugParent, direction, Color3f( 0.0f ) );

		case ccl::SocketType::FLOAT :

			return setupTypedPlug<FloatPlug>( socketName, plugParent, direction, 0.0f );

		case ccl::SocketType::INT :
		case ccl::SocketType::UINT :

			return setupTypedPlug<IntPlug>( socketName, plugParent, direction, 0 );

		case ccl::SocketType::POINT2 :

			return setupTypedPlug<V2fPlug>( socketName, plugParent, direction, V2f( 0.0f ) );

		case ccl::SocketType::VECTOR :
		case ccl::SocketType::POINT :
		case ccl::SocketType::NORMAL :

			return setupTypedPlug<V3fPlug>( socketName, plugParent, direction, V3f( 0.0f ) );

		case ccl::SocketType::NODE :

			return setupNodePlug( socketName, plugParent, direction );

		case ccl::SocketType::CLOSURE :

			return setupNodePlug( socketName, plugParent, direction );

		case ccl::SocketType::STRING :

			return setupTypedPlug<StringPlug>( socketName, plugParent, direction, "" );

		case ccl::SocketType::BOOLEAN :

			return setupTypedPlug<BoolPlug>( socketName, plugParent, direction, false );

		case ccl::SocketType::FLOAT_ARRAY :

			{
				IECore::Splineff::PointContainer points;
				points.insert( std::pair<float, float>( 0.0f, 0.0f ) );
				points.insert( std::pair<float, float>( 1.0f, 1.0f ) );

				return setupTypedPlug<SplineffPlug>( socketName, plugParent, direction, SplineDefinitionff( points, SplineDefinitionInterpolationCatmullRom ) );
			}

		case ccl::SocketType::COLOR_ARRAY :
		case ccl::SocketType::VECTOR_ARRAY :

			{

				IECore::SplinefColor3f::PointContainer points;
				points.insert( std::pair<float, Color3f>( 0.0f, Color3f( 0.0f ) ) );
				points.insert( std::pair<float, Color3f>( 1.0f, Color3f( 1.0f ) ) );

				return setupTypedPlug<SplinefColor3fPlug>( socketName, plugParent, direction, SplineDefinitionfColor3f( points, SplineDefinitionInterpolationCatmullRom ) );

			}

		default :

			msg(
				Msg::Warning,
				"GafferCycles::SocketHandler::setupPlug",
				format( "Unsupported socket type \"%s\" for \"%s\" on node \"%s\"" ) %
					ccl::SocketType::type_name( (ccl::SocketType::Type)socketType ) %
					socketName.string() %
					nodeName( plugParent )
			);
			return nullptr;

	}
}

Gaffer::Plug *setupPlug( const ccl::NodeType *nodeType, const ccl::SocketType socketType, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	Plug *plug = nullptr;

	switch( socketType.type )
	{
		case ccl::SocketType::INT :
		case ccl::SocketType::UINT :

			plug = setupNumericPlug<IntPlug>(
				nodeType, socketType, plugParent, direction,
				*static_cast<const int *>( socketType.default_value )
			);
			break;

		case ccl::SocketType::FLOAT :

			plug = setupNumericPlug<FloatPlug>(
				nodeType, socketType, plugParent, direction,
				*static_cast<const float *>( socketType.default_value )
			);
			break;

		case ccl::SocketType::BOOLEAN :

			{
				const bool *defaultValue = (bool*)socketType.default_value;
				plug = setupTypedPlug<BoolPlug>( nodeType, socketType, plugParent, direction, *defaultValue );
			}
			break;

		case ccl::SocketType::COLOR :

			plug = setupColorPlug<Color3fPlug>( nodeType, socketType, plugParent, direction );
			break;

		case ccl::SocketType::POINT2 :

			{
				const ccl::float2 *defaultValue = (ccl::float2*)socketType.default_value;
				plug = setupTypedPlug<V2fPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					V2f(
						defaultValue->x,
						defaultValue->y
					)
				);
			}
			break;

		case ccl::SocketType::VECTOR :
		case ccl::SocketType::POINT :
		case ccl::SocketType::NORMAL :

			{
				const ccl::float3 *defaultValue = (ccl::float3*)socketType.default_value;
				plug = setupTypedPlug<V3fPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					V3f(
						defaultValue->x,
						defaultValue->y,
						defaultValue->z
					)
				);
			}
			break;

		case ccl::SocketType::ENUM :

			{
				const int *defaultValue = (int*)socketType.default_value;
				const ccl::NodeEnum &enums = *socketType.enum_values;

				plug = setupTypedPlug<StringPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					enums[*defaultValue].c_str()
				);
			}
			break;

		case ccl::SocketType::STRING :

			{
				plug = setupTypedPlug<StringPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					""
				);
			}
			break;

		case ccl::SocketType::TRANSFORM :

			{
				ccl::Transform *t = (ccl::Transform*)socketType.default_value;
				plug = setupTypedPlug<M44fPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					SocketAlgo::getTransform( *t )
				);
			}
			break;

		case ccl::SocketType::CLOSURE :

			plug = setupNodePlug(
				socketType.name.c_str(),
				plugParent,
				direction
			);
			break;

		case ccl::SocketType::FLOAT_ARRAY :

			{
				IECore::Splineff::PointContainer points;
				points.insert( std::pair<float, float>( 0.0f, 0.0f ) );
				points.insert( std::pair<float, float>( 1.0f, 1.0f ) );
				plug = setupTypedPlug<SplineffPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					SplineDefinitionff( points, SplineDefinitionInterpolationCatmullRom )
				);
			}
			break;

		case ccl::SocketType::COLOR_ARRAY :
		case ccl::SocketType::VECTOR_ARRAY :

			{
				IECore::SplinefColor3f::PointContainer points;
				points.insert( std::pair<float, Color3f>( 0.0f, Color3f( 0.0f ) ) );
				points.insert( std::pair<float, Color3f>( 1.0f, Color3f( 1.0f ) ) );
				plug = setupTypedPlug<SplinefColor3fPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					SplineDefinitionfColor3f( points, SplineDefinitionInterpolationCatmullRom )
				);
			}
			break;

		default :
			break;
	}

	if( !plug )
	{
		msg(
			Msg::Warning,
			"GafferCycles::SocketHandler::setupPlug",
			format( "Unsupported socket \"%s\" of type \"%s\" on node \"%s\" of type \"%s\"" ) %
				socketType.name.c_str() %
				ccl::SocketType::type_name(socketType.type).c_str() %
				nodeName( plugParent ) %
				nodeType->name.c_str()
		);
	}

	return plug;
}

void setupPlugs( const ccl::NodeType *nodeType, Gaffer::GraphComponent *plugsParent, Gaffer::Plug::Direction direction )
{

	// Make sure we have a plug to represent each socket, reusing plugs wherever possible.

	std::set<const Plug *> validPlugs;

	if( direction == Plug::In )
	{
		for( const ccl::SocketType &socketType : nodeType->inputs )
		{
			if( g_socketBlacklist.contains( { nodeType->name, socketType.name } ) ||
				( socketType.flags & ccl::SocketType::INTERNAL ) )
			{
				continue;
			}
			validPlugs.insert( setupPlug( nodeType, socketType, plugsParent, direction ) );
		}
	}
	else
	{
		for( const ccl::SocketType &socketType : nodeType->outputs )
		{
			std::string name = socketType.name.c_str();
			validPlugs.insert( setupPlug( name, (int)socketType.type, plugsParent, direction ) );
		}
	}

	// Remove any old plugs which it turned out we didn't need.

	for( int i = plugsParent->children().size() - 1; i >= 0; --i )
	{
		Plug *child = plugsParent->getChild<Plug>( i );
		if( validPlugs.find( child ) == validPlugs.end() )
		{
			plugsParent->removeChild( child );
		}
	}
}

void setupLightPlugs( const std::string &shaderName, const ccl::NodeType *nodeType, Gaffer::GraphComponent *plugsParent, bool keepExistingChildren )
{

	// Make sure we have a plug to represent each socket, reusing plugs wherever possible.

	std::set<const Plug *> validPlugs;

	if( shaderName != "portal" )
	{
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "cast_shadow" ) )), plugsParent, Gaffer::Plug::In ) );
		validPlugs.insert( setupTypedPlug<BoolPlug>( "use_mis", plugsParent, Gaffer::Plug::In, true ) );
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "use_camera" ) )), plugsParent, Gaffer::Plug::In ) );
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "use_diffuse" ) )), plugsParent, Gaffer::Plug::In ) );
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "use_glossy" ) )), plugsParent, Gaffer::Plug::In ) );
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "use_transmission" ) )), plugsParent, Gaffer::Plug::In ) );
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "use_scatter" ) )), plugsParent, Gaffer::Plug::In ) );
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "use_caustics" ) )), plugsParent, Gaffer::Plug::In ) );
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "max_bounces" ) )), plugsParent, Gaffer::Plug::In ) );
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "lightgroup" ) )), plugsParent, Gaffer::Plug::In ) );
		validPlugs.insert( setupTypedPlug<FloatPlug>( "intensity", plugsParent, Gaffer::Plug::In, 1.0f ) );
		validPlugs.insert( setupTypedPlug<FloatPlug>( "exposure", plugsParent, Gaffer::Plug::In, 0.0f ) );
		validPlugs.insert( setupTypedPlug<Color3fPlug>( "color", plugsParent, Gaffer::Plug::In, Color3f( 1.0f ) ) );
	}

	if( shaderName == "portal" || shaderName == "quad_light" )
	{
		validPlugs.insert( setupTypedPlug<FloatPlug>( "width", plugsParent, Gaffer::Plug::In, 2.0f ) );
		validPlugs.insert( setupTypedPlug<FloatPlug>( "height", plugsParent, Gaffer::Plug::In, 2.0f ) );
	}
	else if( shaderName == "spot_light" )
	{
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "size" ) )), plugsParent, Gaffer::Plug::In ) );
		const ccl::SocketType *angleSocket = nodeType->find_input( ccl::ustring( "spot_angle" ) );
		validPlugs.insert(
			setupNumericPlug<FloatPlug>(
				nodeType, *angleSocket, plugsParent, Gaffer::Plug::In,
				// Cycles API uses radians, but that isn't user-friendly so we convert to degrees.
				// We convert back to radians in the renderer backend.
				IECore::radiansToDegrees( *static_cast<const float *>( angleSocket->default_value ) )
			)
		);
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "spot_smooth" ) )), plugsParent, Gaffer::Plug::In ) );
	}
	else if( shaderName == "point_light" )
	{
		validPlugs.insert( setupPlug( nodeType, *(nodeType->find_input( ccl::ustring( "size" ) )), plugsParent, Gaffer::Plug::In ) );
	}
	else if( shaderName == "disk_light" )
	{
		validPlugs.insert( setupTypedPlug<FloatPlug>( "width", plugsParent, Gaffer::Plug::In, 2.0f ) );
	}
	else if( shaderName == "background_light" )
	{
		validPlugs.insert( setupTypedPlug<IntPlug>( "map_resolution", plugsParent, Gaffer::Plug::In, 1024 ) );
	}
	else if( shaderName == "distant_light" )
	{
		const ccl::SocketType *angleSocket = nodeType->find_input( ccl::ustring( "angle" ) );
		validPlugs.insert(
			setupNumericPlug<FloatPlug>(
				nodeType, *angleSocket, plugsParent, Gaffer::Plug::In,
				// Cycles API uses radians, but that isn't user-friendly so we convert to degrees.
				// We convert back to radians in the renderer backend.
				IECore::radiansToDegrees( *static_cast<const float *>( angleSocket->default_value ) )
			)
		);
	}

	if( shaderName == "quad_light" || shaderName == "disk_light" )
	{
		const ccl::SocketType *spreadSocket = nodeType->find_input( ccl::ustring( "spread" ) );
		validPlugs.insert(
			setupNumericPlug<FloatPlug>(
				nodeType, *spreadSocket, plugsParent, Gaffer::Plug::In,
				// Cycles API uses radians, but that isn't user-friendly so we convert to degrees.
				// We convert back to radians in the renderer backend.
				IECore::radiansToDegrees( *static_cast<const float *>( spreadSocket->default_value ) )
			)
		);
	}

	if( shaderName != "portal" && shaderName != "background_light" )
	{
		validPlugs.insert( setupTypedPlug<BoolPlug>( "normalize", plugsParent, Gaffer::Plug::In, true ) );
	}

	// Remove any old plugs which it turned out we didn't need.

	if( !keepExistingChildren )
	{
		for( int i = plugsParent->children().size() - 1; i >= 0; --i )
		{
			Plug *child = plugsParent->getChild<Plug>( i );
			if( validPlugs.find( child ) == validPlugs.end() )
			{
				plugsParent->removeChild( child );
			}
		}
	}
}

} // namespace SocketHandler

} // namespace GafferCycles
