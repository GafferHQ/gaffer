//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/AttributeQuery.h"

#include "Gaffer/PlugAlgo.h"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/NumericPlug.h"

#include "IECore/NullObject.h"
#include "IECore/CompoundObject.h"
#include "IECore/Exception.h"

#include "boost/container/small_vector.hpp"

#include <cassert>
#include <vector>

using namespace IECore;
using namespace Gaffer;

namespace
{

Gaffer::Plug const* correspondingPlug( const Gaffer::Plug* const parent, const Gaffer::Plug* const child, const Gaffer::Plug* const other )
{
	assert( parent != 0 );
	assert( child != 0 );
	assert( other != 0 );

	boost::container::small_vector< const Gaffer::Plug*, 4 > path;

	const Gaffer::Plug* plug = child;

	while( plug != parent )
	{
		path.push_back( plug );
		plug = plug->parent< Gaffer::Plug >();
	}

	plug = other;

	while( ! path.empty() )
	{
		plug = plug->getChild< Gaffer::Plug >( path.back()->getName() );
		path.pop_back();
	}

	return plug;
}

void addChildPlugsToAffectedOutputs( const Gaffer::Plug* const plug, Gaffer::DependencyNode::AffectedPlugsContainer& outputs )
{
	assert( plug != 0 );

	if( plug->children().empty() )
	{
		outputs.push_back( plug );
	}
	else for( const Gaffer::PlugPtr& child : Gaffer::Plug::OutputRange( *plug ) )
	{
		addChildPlugsToAffectedOutputs( child.get(), outputs );
	}
}

} // namespace

namespace GafferScene
{

size_t AttributeQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( AttributeQuery );

AttributeQuery::AttributeQuery( const std::string& name )
: Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new Gaffer::StringPlug( "location" ) );
	addChild( new Gaffer::StringPlug( "attribute" ) );
	addChild( new Gaffer::BoolPlug( "inherit", Gaffer::Plug::In, false ) );
	addChild( new Gaffer::BoolPlug( "exists", Gaffer::Plug::Out, false ) );
	addChild( new Gaffer::ObjectPlug( "__internalObject", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
}

AttributeQuery::~AttributeQuery()
{}

ScenePlug* AttributeQuery::scenePlug()
{
	return const_cast< ScenePlug* >(
		static_cast< const AttributeQuery* >( this )->scenePlug() );
}

const ScenePlug* AttributeQuery::scenePlug() const
{
	return getChild< ScenePlug >( g_firstPlugIndex );
}

Gaffer::StringPlug* AttributeQuery::locationPlug()
{
	return const_cast< Gaffer::StringPlug* >(
		static_cast< const AttributeQuery* >( this )->locationPlug() );
}

const Gaffer::StringPlug* AttributeQuery::locationPlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug* AttributeQuery::attributePlug()
{
	return const_cast< Gaffer::StringPlug* >(
		static_cast< const AttributeQuery* >( this )->attributePlug() );
}

const Gaffer::StringPlug* AttributeQuery::attributePlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug* AttributeQuery::inheritPlug()
{
	return const_cast< Gaffer::BoolPlug* >(
		static_cast< const AttributeQuery* >( this )->inheritPlug() );
}

const Gaffer::BoolPlug* AttributeQuery::inheritPlug() const
{
	return getChild< Gaffer::BoolPlug >( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug* AttributeQuery::existsPlug()
{
	return const_cast< Gaffer::BoolPlug* >(
		static_cast< const AttributeQuery* >( this )->existsPlug() );
}

const Gaffer::BoolPlug* AttributeQuery::existsPlug() const
{
	return getChild< Gaffer::BoolPlug >( g_firstPlugIndex + 4 );
}

Gaffer::ObjectPlug* AttributeQuery::internalObjectPlug()
{
	return const_cast< Gaffer::ObjectPlug* >(
		static_cast< const AttributeQuery* >( this )->internalObjectPlug() );
}

const Gaffer::ObjectPlug* AttributeQuery::internalObjectPlug() const
{
	return getChild< Gaffer::ObjectPlug >( g_firstPlugIndex + 5 );
}

bool AttributeQuery::isSetup() const
{
	return ( defaultPlug() != nullptr ) && ( valuePlug() != nullptr );
}

bool AttributeQuery::canSetup( const Gaffer::ValuePlug* const plug ) const
{
	const bool success =
		( plug != nullptr ) &&
		( ! isSetup() ) &&
		( PlugAlgo::canSetValueFromData( plug ) || (Gaffer::TypeId)plug->typeId() == ObjectPlugTypeId )
	;

	return success;
}

void AttributeQuery::setup( const Gaffer::ValuePlug* const plug )
{
	if( defaultPlug() )
	{
		throw IECore::Exception( "AttributeQuery already has a \"default\" plug." );
	}
	if( valuePlug() )
	{
		throw IECore::Exception( "AttributeQuery already has a \"value\" plug." );
	}

	assert( canSetup( plug ) );

	Gaffer::PlugPtr def = plug->createCounterpart( defaultPlugName(), Gaffer::Plug::In );
	def->setFlags( Gaffer::Plug::Serialisable, true );
	def->setFlags( Gaffer::Plug::Dynamic, false );
	addChild( def );

	Gaffer::PlugPtr val = plug->createCounterpart( valuePlugName(), Gaffer::Plug::Out );
	val->setFlags( Gaffer::Plug::Serialisable, true );
	val->setFlags( Gaffer::Plug::Dynamic, false );
	addChild( val );
}

IECore::InternedString AttributeQuery::valuePlugName() const
{
	static const IECore::InternedString name( "value" );
	return name;
}

IECore::InternedString AttributeQuery::defaultPlugName() const
{
	static const IECore::InternedString name( "default" );
	return name;
}

void AttributeQuery::affects( const Gaffer::Plug* const input, AffectedPlugsContainer& outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == internalObjectPlug() )
	{
		const Gaffer::ValuePlug* const vplug = valuePlug();

		if( vplug != nullptr )
		{
			addChildPlugsToAffectedOutputs( vplug, outputs );
		}

		outputs.push_back( existsPlug() );
	}
	else if(
		( input == inheritPlug() ) ||
		( input == locationPlug() ) ||
		( input == attributePlug() ) ||
		( input == scenePlug()->existsPlug() ) ||
		( input == scenePlug()->attributesPlug() ) )
	{
		outputs.push_back( internalObjectPlug() );
	}
	else
	{
		assert( input != 0 );

		const Gaffer::ValuePlug* const dplug = defaultPlug();

		if(
			( dplug == input ) ||
			( dplug->isAncestorOf( input ) ) )
		{
			const Gaffer::ValuePlug* const vplug = valuePlug();

			if( vplug != nullptr )
			{
				outputs.push_back( correspondingPlug( dplug, input, vplug ) );
			}
		}
	}
}

void AttributeQuery::hash( const Gaffer::ValuePlug* const output, const Gaffer::Context* const context, IECore::MurmurHash& h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == internalObjectPlug() )
	{
		const std::string loc = locationPlug()->getValue();

		if( ! loc.empty() )
		{
			const ScenePlug* const splug = scenePlug();

			const ScenePlug::ScenePath path = ScenePlug::stringToPath( loc );

			if( splug->exists( path ) )
			{
				h.append( ( inheritPlug()->getValue() )
					? splug->fullAttributesHash( path )
					: splug->attributesHash( path ) );
				attributePlug()->hash( h );
			}
		}
	}
	else if( output == existsPlug() )
	{
		internalObjectPlug()->hash( h );
	}
	else
	{
		assert( output != 0 );

		const Gaffer::ValuePlug* const vplug = valuePlug();

		if(
			( vplug == output ) ||
			( vplug->isAncestorOf( output ) ) )
		{
			internalObjectPlug()->hash( h );
			IECore::assertedStaticCast< const Gaffer::ValuePlug >( correspondingPlug( vplug, output, defaultPlug() ) )->hash( h );
		}
	}
}

void AttributeQuery::compute( Gaffer::ValuePlug* const output, const Gaffer::Context* const context ) const
{
	if( output == internalObjectPlug() )
	{
		IECore::ObjectPtr obj( IECore::NullObject::defaultNullObject() );

		const std::string loc = locationPlug()->getValue();

		if( ! loc.empty() )
		{
			const ScenePlug* const splug = scenePlug();

			const ScenePlug::ScenePath path = ScenePlug::stringToPath( loc );

			if( splug->exists( path ) )
			{
				const std::string name = attributePlug()->getValue();

				if( ! name.empty() )
				{
					const IECore::ConstCompoundObjectPtr cobj = ( inheritPlug()->getValue() )
						? boost::static_pointer_cast< const IECore::CompoundObject >( splug->fullAttributes( path ) )
						: ( splug->attributes( path ) );
					assert( cobj );

					const IECore::CompoundObject::ObjectMap& objmap = cobj->members();
					const IECore::CompoundObject::ObjectMap::const_iterator it = objmap.find( name );

					if( it != objmap.end() )
					{
						obj = ( *it ).second;
					}
				}
			}
		}

		IECore::assertedStaticCast< Gaffer::ObjectPlug >( output )->setValue( obj );
	}
	else if( output == existsPlug() )
	{
		const IECore::ConstObjectPtr object = internalObjectPlug()->getValue();
		assert( object );

		IECore::assertedStaticCast< Gaffer::BoolPlug >( output )->setValue( object->isNotEqualTo( IECore::NullObject::defaultNullObject() ) );
	}
	else
	{
		assert( output != 0 );

		const Gaffer::ValuePlug* const vplug = valuePlug();

		if(
			( vplug == output ) ||
			( vplug->isAncestorOf( output ) ) )
		{
			const IECore::ConstObjectPtr object = internalObjectPlug()->getValue();
			assert( object );

			if( !object->isEqualTo( IECore::NullObject::defaultNullObject() ) )
			{
				bool success = false;

				if( auto objectPlug = runTimeCast<ObjectPlug>( output ) )
				{
					objectPlug->setValue( object );
					success = true;
				}
				else
				{
					if( const Data *value = runTimeCast<const Data>( object.get() ) )
					{
						success = PlugAlgo::setValueFromData( vplug, output, value );
					}
				}

				if( success )
				{
					return;
				}
			}

			output->setFrom( static_cast<const Gaffer::ValuePlug *>(correspondingPlug( vplug, output, defaultPlug() ) ) );
		}
	}
}

} // GafferScene
