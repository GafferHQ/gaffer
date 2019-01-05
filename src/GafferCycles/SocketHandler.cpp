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
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/MessageHandler.h"

#include "boost/container/flat_set.hpp"

// Cycles
#include "util/util_transform.h"
#include "util/util_types_float2.h"
#include "util/util_types_float3.h"

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
Gaffer::Plug *setupNumericPlug( const ccl::NodeType *nodeType, const ccl::SocketType socketType, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	typedef typename PlugType::ValueType ValueType;

	ValueType defaultValue = (ValueType&)socketType.default_value;
	ValueType minValue = Imath::limits<ValueType>::min();
	ValueType maxValue = Imath::limits<ValueType>::max();

	if( socketType.type == ccl::SocketType::UINT )
	{
		minValue = 0;
	}

	const char *name = ccl::SocketType::type_name( socketType.type ).c_str();
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
	PlugType *existingPlug = plugParent->getChild<PlugType>( socketName );
	if(
		existingPlug &&
		existingPlug->direction() == direction &&
		existingPlug->defaultValue() == defaultValue
	)
	{
		existingPlug->setFlags( Gaffer::Plug::Dynamic, false );
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( socketName, direction, defaultValue );

	PlugAlgo::replacePlug( plugParent, plug );

	return plug.get();
}

template<typename PlugType>
Gaffer::Plug *setupTypedPlug( const ccl::NodeType *nodeType, const ccl::SocketType socketType, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction, const typename PlugType::ValueType &defaultValue )
{
	return setupTypedPlug<PlugType>( ccl::SocketType::type_name( socketType.type ).c_str(), plugParent, direction, defaultValue );
}

template<typename PlugType>
Gaffer::Plug *setupColorPlug( const ccl::NodeType *nodeType, const ccl::SocketType socketType, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	typedef typename PlugType::ValueType ValueType;
	typedef typename ValueType::BaseType BaseType;

	ValueType defaultValue( 1 );
	ccl::float3 defaultCValue = (ccl::float3&)socketType.default_value;
	defaultValue[0] = defaultCValue.x;
	defaultValue[0] = defaultCValue.y;
	defaultValue[0] = defaultCValue.z;

	ValueType minValue( Imath::limits<BaseType>::min() );
	ValueType maxValue( Imath::limits<BaseType>::max() );

	const char *name = ccl::SocketType::type_name( socketType.type ).c_str();
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

Gaffer::Plug *setupClosurePlug( const IECore::InternedString &socketName, Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction )
{
	GafferOSL::ClosurePlug *existingPlug = plugParent->getChild<GafferOSL::ClosurePlug>( socketName );
	if(
		existingPlug &&
		existingPlug->direction() == direction
	)
	{
		existingPlug->setFlags( Gaffer::Plug::Dynamic, false );
		return existingPlug;
	}

	GafferOSL::ClosurePlugPtr plug = new GafferOSL::ClosurePlug( socketName, direction );

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

			return setupTypedPlug<V3fPlug>( socketName, plugParent, direction, V3f( 0.0f ) );

		case ccl::SocketType::NODE :

			return setupNodePlug( socketName, plugParent, direction );

		case ccl::SocketType::CLOSURE :

			return setupClosurePlug( socketName, plugParent, direction );

		case ccl::SocketType::STRING :

			return setupTypedPlug<StringPlug>( socketName, plugParent, direction, "" );

		case ccl::SocketType::BOOLEAN :

			return setupTypedPlug<BoolPlug>( socketName, plugParent, direction, false );

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

			plug = setupNumericPlug<IntPlug>( nodeType, socketType, plugParent, direction );
			break;

		case ccl::SocketType::FLOAT :

			plug = setupNumericPlug<FloatPlug>( nodeType, socketType, plugParent, direction );
			break;

		case ccl::SocketType::BOOLEAN :

			plug = setupTypedPlug<BoolPlug>(
				nodeType,
				socketType,
				plugParent,
				direction,
				(bool&)socketType.default_value
			);
			break;

		case ccl::SocketType::COLOR :

			plug = setupColorPlug<Color3fPlug>( nodeType, socketType, plugParent, direction );
			break;

		case ccl::SocketType::POINT2 :

			{
				ccl::float2 defaultValue = (ccl::float2&)socketType.default_value;
				plug = setupTypedPlug<V2fPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					V2f(
						defaultValue.x,
						defaultValue.y
					)
				);
			}
			break;

		case ccl::SocketType::VECTOR :

			{
				ccl::float3 defaultValue = (ccl::float3&)socketType.default_value;
				plug = setupTypedPlug<V3fPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					V3f(
						defaultValue.x,
						defaultValue.y,
						defaultValue.z
					)
				);
			}
			break;

		case ccl::SocketType::ENUM :

			{
				ccl::NodeEnum defaultEnum = (ccl::NodeEnum&)socketType.enum_values;
				plug = setupTypedPlug<StringPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					defaultEnum[(int&)socketType.default_value].c_str()
				);
			}
			break;

		case ccl::SocketType::STRING :

			{
				ccl::ustring defaultValue = (ccl::ustring&)socketType.default_value;
				plug = setupTypedPlug<StringPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					defaultValue.c_str()
				);
			}
			break;

		case ccl::SocketType::TRANSFORM :

			{
				ccl::Transform t = (ccl::Transform&)socketType.default_value;
				plug = setupTypedPlug<M44fPlug>(
					nodeType,
					socketType,
					plugParent,
					direction,
					SocketAlgo::getTransform( t )
				);
			}
			break;

		case ccl::SocketType::CLOSURE :

			plug = setupClosurePlug(
				socketType.name.c_str(),
				plugParent,
				direction
			);
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
		for( const ccl::SocketType socketType : nodeType->inputs )
		{
			validPlugs.insert( setupPlug( nodeType, socketType, plugsParent, direction ) );
		}
	}
	else
	{
		for( const ccl::SocketType socketType : nodeType->outputs )
		{
			validPlugs.insert( setupPlug( nodeType, socketType, plugsParent, direction ) );
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

Gaffer::Plug *setupOutputNodePlug( Gaffer::GraphComponent *plugParent )
{
	Plug *existingPlug = plugParent->getChild<Plug>( "out" );
	if(
		existingPlug &&
		existingPlug->direction() == Gaffer::Plug::Out &&
		existingPlug->typeId() == Plug::staticTypeId()
	)
	{
		existingPlug->setFlags( Gaffer::Plug::Dynamic, false );
		return existingPlug;
	}

	PlugPtr plug = new Plug( "out", Gaffer::Plug::Out, Plug::Default );
	PlugAlgo::replacePlug( plugParent, plug );

	return plug.get();
}

} // namespace SocketHandler

} // namespace GafferCycles
