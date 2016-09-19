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

namespace
{

/// \todo This is repeated from OSLShader.cpp. Would it make sense in PlugAlgo.h?
void transferConnectionOrValue( Plug *sourcePlug, Plug *destinationPlug )
{
	if( !sourcePlug )
	{
		return;
	}

	if( Plug *input = sourcePlug->getInput<Plug>() )
	{
		destinationPlug->setInput( input );
	}
	else
	{
		ValuePlug *sourceValuePlug = runTimeCast<ValuePlug>( sourcePlug );
		ValuePlug *destinationValuePlug = runTimeCast<ValuePlug>( destinationPlug );
		if( destinationValuePlug && sourceValuePlug )
		{
			destinationValuePlug->setFrom( sourceValuePlug );
		}
	}
}

template<typename PlugType>
Gaffer::Plug *setupNumericPlug( const AtNodeEntry *node, const AtParamEntry *parameter, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	typedef typename PlugType::ValueType ValueType;

	ValueType defaultValue = 0;
	ValueType minValue = Imath::limits<ValueType>::min();
	ValueType maxValue = Imath::limits<ValueType>::max();

	switch( AiParamGetType( parameter ) )
	{
		case AI_TYPE_BYTE :
			defaultValue = (ValueType)AiParamGetDefault( parameter )->BYTE;
			minValue = 0;
			maxValue = 255;
			break;
		case AI_TYPE_INT :
			defaultValue = (ValueType)AiParamGetDefault( parameter )->INT;
			break;
		case AI_TYPE_UINT :
			defaultValue = (ValueType)AiParamGetDefault( parameter )->UINT;
			minValue = 0;
			break;
		case AI_TYPE_FLOAT :
			defaultValue = (ValueType)AiParamGetDefault( parameter )->FLT;
			break;
	}

	const char *name = AiParamGetName( parameter );
	PlugType *existingPlug = plugParent->getChild<PlugType>( name );
	if(
		existingPlug &&
		existingPlug->direction() == direction &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue
	)
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, direction, defaultValue, minValue, maxValue, Plug::Default | Plug::Dynamic );
	transferConnectionOrValue( existingPlug, plug.get() );

	plugParent->setChild( name, plug );

	return plug.get();
}

Gaffer::Plug *setupPlug( const IECore::InternedString &parameterName, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	Plug *existingPlug = plugParent->getChild<Plug>( parameterName );
	if(
		existingPlug &&
		existingPlug->direction() == direction &&
		existingPlug->typeId() == Plug::staticTypeId()
	)
	{
		return existingPlug;
	}

	PlugPtr plug = new Plug( parameterName, direction, Plug::Default | Plug::Dynamic );

	transferConnectionOrValue( existingPlug, plug.get() );

	plugParent->setChild( parameterName, plug );

	return plug.get();
}

template<typename PlugType>
Gaffer::Plug *setupTypedPlug( const IECore::InternedString &parameterName, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, const typename PlugType::ValueType &defaultValue = typename PlugType::ValueType() )
{
	PlugType *existingPlug = plugParent->getChild<PlugType>( parameterName );
	if(
		existingPlug &&
		existingPlug->direction() == direction &&
		existingPlug->defaultValue() == defaultValue
	)
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( parameterName, direction, defaultValue );
	plug->setFlags( Plug::Dynamic, true );

	transferConnectionOrValue( existingPlug, plug.get() );

	plugParent->setChild( parameterName, plug );

	return plug.get();
}

template<typename PlugType>
Gaffer::Plug *setupTypedPlug( const AtNodeEntry *node, const AtParamEntry *parameter, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, const typename PlugType::ValueType &defaultValue )
{
	return setupTypedPlug<PlugType>( AiParamGetName( parameter ), plugParent, direction, defaultValue );
}

template<typename PlugType>
Gaffer::Plug *setupColorPlug( const AtNodeEntry *node, const AtParamEntry *parameter, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	typedef typename PlugType::ValueType ValueType;
	typedef typename ValueType::BaseType BaseType;

	ValueType defaultValue( 1 );
	switch( AiParamGetType( parameter ) )
	{
		case AI_TYPE_RGB :
			defaultValue[0] = AiParamGetDefault( parameter )->RGB.r;
			defaultValue[1] = AiParamGetDefault( parameter )->RGB.g;
			defaultValue[2] = AiParamGetDefault( parameter )->RGB.b;
			break;
		case AI_TYPE_RGBA :
			defaultValue[0] = AiParamGetDefault( parameter )->RGBA.r;
			defaultValue[1] = AiParamGetDefault( parameter )->RGBA.g;
			defaultValue[2] = AiParamGetDefault( parameter )->RGBA.b;
			defaultValue[3] = AiParamGetDefault( parameter )->RGBA.a;
			break;
		default :
			return NULL;
	}

	ValueType minValue( Imath::limits<BaseType>::min() );
	ValueType maxValue( Imath::limits<BaseType>::max() );

	const char *name = AiParamGetName( parameter );
	PlugType *existingPlug = plugParent->getChild<PlugType>( name );
	if(
		existingPlug &&
		existingPlug->direction() == direction &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->minValue() == minValue &&
		existingPlug->maxValue() == maxValue
	)
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, direction, defaultValue, minValue, maxValue, Plug::Default | Plug::Dynamic );
	if( existingPlug )
	{
		for( size_t i = 0, e = existingPlug->children().size(); i < e; ++i )
		{
			transferConnectionOrValue(
				existingPlug->getChild( i ),
				plug->getChild( i )
			);
		}
	}

	plugParent->setChild( name, plug );
	return plug.get();
}

Gaffer::Plug *setupRGBAPlug( const AtNodeEntry *node, const AtParamEntry *parameter, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	const char *name = AiParamGetName( parameter );

	const char *plugType = "Color4fPlug";
	AiMetaDataGetStr( node, name, "gaffer.plugType", &plugType );
	if( !strcmp( plugType, "Color4fPlug" ) )
	{
		return setupColorPlug<Color4fPlug>( node, parameter, plugParent, direction );
	}
	else if( !strcmp( plugType, "Color3fPlug" ) )
	{
		return setupColorPlug<Color3fPlug>( node, parameter, plugParent, direction );
	}
	else
	{
		msg(
			Msg::Warning,
			"GafferArnold::ParameterHandler::setupPlug",
			format( "Unsupported plug type \"%s\" for parameter \"%s\"" ) %
				plugType %
				AiParamGetName( parameter )
		);
		return NULL;
	}
}

} // namespace

Gaffer::Plug *ParameterHandler::setupPlug( const IECore::InternedString &parameterName, int parameterType, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	switch( parameterType )
	{
		case AI_TYPE_RGB :

			return setupTypedPlug<Color3fPlug>( parameterName, plugParent, direction );

		case AI_TYPE_RGBA :

			return setupTypedPlug<Color4fPlug>( parameterName, plugParent, direction );

		case AI_TYPE_FLOAT :

			return setupTypedPlug<FloatPlug>( parameterName, plugParent, direction );

		case AI_TYPE_INT :

			return setupTypedPlug<IntPlug>( parameterName, plugParent, direction );

		case AI_TYPE_POINT2 :

			return setupTypedPlug<V2fPlug>( parameterName, plugParent, direction );

		case AI_TYPE_POINT :
		case AI_TYPE_VECTOR :

			return setupTypedPlug<V3fPlug>( parameterName, plugParent, direction );

		case AI_TYPE_POINTER :

			return ::setupPlug( parameterName, plugParent, direction );

		default :

			msg(
				Msg::Warning,
				"GafferArnold::ParameterHandler::setupPlug",
				format( "Unsupported parameter type \"%s\"" ) % AiParamGetTypeName( parameterType )
			);
			return NULL;

	}
}

Gaffer::Plug *ParameterHandler::setupPlug( const AtNodeEntry *node, const AtParamEntry *parameter, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	Plug *plug = NULL;

	switch( AiParamGetType( parameter ) )
	{
		case AI_TYPE_BYTE :
		case AI_TYPE_INT :
		case AI_TYPE_UINT :

			plug = setupNumericPlug<IntPlug>( node, parameter, plugParent, direction );
			break;

		case AI_TYPE_FLOAT :

			plug = setupNumericPlug<FloatPlug>( node, parameter, plugParent, direction );
			break;

		case AI_TYPE_BOOLEAN :

			plug = setupTypedPlug<BoolPlug>(
				node,
				parameter,
				plugParent,
				direction,
				AiParamGetDefault( parameter )->BOOL
			);
			break;

		case AI_TYPE_RGB :

			plug = setupColorPlug<Color3fPlug>( node, parameter, plugParent, direction );
			break;

		case AI_TYPE_RGBA :

			plug = setupRGBAPlug( node, parameter, plugParent, direction );
			break;

		case AI_TYPE_POINT2 :

			plug = setupTypedPlug<V2fPlug>(
				node,
				parameter,
				plugParent,
				direction,
				V2f(
					AiParamGetDefault( parameter )->PNT2.x,
					AiParamGetDefault( parameter )->PNT2.y
				)
			);
			break;

		case AI_TYPE_POINT :

			plug = setupTypedPlug<V3fPlug>(
				node,
				parameter,
				plugParent,
				direction,
				V3f(
					AiParamGetDefault( parameter )->PNT.x,
					AiParamGetDefault( parameter )->PNT.y,
					AiParamGetDefault( parameter )->PNT.z
				)
			);
			break;

		case AI_TYPE_VECTOR :

			plug = setupTypedPlug<V3fPlug>(
				node,
				parameter,
				plugParent,
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
				plug = setupTypedPlug<StringPlug>(
					node,
					parameter,
					plugParent,
					direction,
					AiEnumGetString( e, AiParamGetDefault( parameter )->INT )
				);
			}
			break;

		case AI_TYPE_STRING :

			plug = setupTypedPlug<StringPlug>(
				node,
				parameter,
				plugParent,
				direction,
				AiParamGetDefault( parameter )->STR
			);
			break;

		case AI_TYPE_MATRIX :

			plug = setupTypedPlug<M44fPlug>(
				node,
				parameter,
				plugParent,
				direction,
				M44f( *AiParamGetDefault( parameter )->pMTX )
			);
			break;

	}

	if( !plug )
	{
		msg(
			Msg::Warning,
			"GafferArnold::ParameterHandler::setupPlug",
			format( "Unsupported parameter \"%s\" of type \"%s\"" ) %
				AiParamGetName( parameter ) %
				AiParamGetTypeName( AiParamGetType( parameter ) )
		);
	}

	return plug;
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

	// Make sure we have a plug to represent each parameter, reusing plugs wherever possible.

	std::set<const Plug *> validPlugs;

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

		validPlugs.insert( setupPlug( nodeEntry, param, plugsParent, direction ) );
	}
	AiParamIteratorDestroy( it );

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
