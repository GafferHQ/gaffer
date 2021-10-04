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

template<typename PlugType>
bool setNumericPlugValue( PlugType *plug, const Object *value )
{
	switch( value->typeId() )
	{
		case FloatDataTypeId :
			plug->setValue( static_cast<const FloatData *>( value )->readable() );
			return true;
		case IntDataTypeId :
			plug->setValue( static_cast<const IntData *>( value )->readable() );
			return true;
		case BoolDataTypeId :
			plug->setValue( static_cast<const BoolData *>( value )->readable() );
			return true;
		default :
			return false;
	}
}

template<typename PlugType, typename ValueType>
bool setCompoundNumericPlugValue( const PlugType *parent, typename PlugType::ChildType *child, const ValueType &value )
{
	for( size_t i = 0; i < parent->children().size(); ++i )
	{
		if( child == parent->getChild( i ) )
		{
			if( i < ValueType::dimensions() )
			{
				child->setValue( value[i] );
			}
			else
			{
				// 1 for the alpha of Color4f, 0 for everthing else
				child->setValue( i == 3 ? 1 : 0 );
			}
			return true;
		}
	}
	return false;
}

template<typename PlugType>
bool setCompoundNumericPlugValue( const PlugType *parent, Gaffer::ValuePlug *child, const Object *value )
{
	auto typedChild = assertedStaticCast<typename PlugType::ChildType>( child );

	switch( value->typeId() )
	{
		case Color4fDataTypeId :
			return setCompoundNumericPlugValue( parent, typedChild, static_cast<const Color4fData *>( value )->readable() );
		case Color3fDataTypeId :
			return setCompoundNumericPlugValue( parent, typedChild, static_cast<const Color3fData *>( value )->readable() );
		case V3fDataTypeId :
			return setCompoundNumericPlugValue( parent, typedChild, static_cast<const V3fData *>( value )->readable() );
		case V2fDataTypeId :
			return setCompoundNumericPlugValue( parent, typedChild, static_cast<const V2fData *>( value )->readable() );
		case V3iDataTypeId :
			return setCompoundNumericPlugValue( parent, typedChild, static_cast<const V3iData *>( value )->readable() );
		case V2iDataTypeId :
			return setCompoundNumericPlugValue( parent, typedChild, static_cast<const V2iData *>( value )->readable() );
		case FloatDataTypeId :
		case IntDataTypeId :
		case BoolDataTypeId :
			if( parent->children().size() < 4 || child != parent->getChild( 3 ) )
			{
				return setNumericPlugValue( typedChild, value );
			}
			else
			{
				typedChild->setValue( 1 );
				return true;
			}
		default :
			return false;
	}
}

template<typename PlugType, typename ValueType>
bool setBoxPlugValue( const PlugType *boxPlug, typename PlugType::ChildType::ChildType *plug, const ValueType &value )
{
	if( plug->parent() == boxPlug->minPlug() )
	{
		return setCompoundNumericPlugValue( boxPlug->minPlug(), plug, value.min );
	}
	else
	{
		return setCompoundNumericPlugValue( boxPlug->maxPlug(), plug, value.max );
	}
}

template<typename PlugType>
bool setBoxPlugValue( const PlugType *boxPlug, Gaffer::ValuePlug *plug, const Object *value )
{
	auto typedPlug = assertedStaticCast<typename PlugType::ChildType::ChildType>( plug );
	switch( value->typeId() )
	{
		case Box3fDataTypeId :
			return setBoxPlugValue( boxPlug, typedPlug, static_cast<const Box3fData *>( value )->readable() );
		case Box2fDataTypeId :
			return setBoxPlugValue( boxPlug, typedPlug, static_cast<const Box2fData *>( value )->readable() );
		case Box3iDataTypeId :
			return setBoxPlugValue( boxPlug, typedPlug, static_cast<const Box3iData *>( value )->readable() );
		case Box2iDataTypeId :
			return setBoxPlugValue( boxPlug, typedPlug, static_cast<const Box2iData *>( value )->readable() );
		default :
			return false;
	}
}

template<typename PlugType>
bool setTypedObjectPlugValue( PlugType *plug, const Object *value )
{
	if( auto typedValue = runTimeCast<const typename PlugType::ValueType>( value ) )
	{
		plug->setValue( typedValue );
		return true;
	}
	return false;
}

bool canSetPlugType( const Gaffer::TypeId pid )
{
	bool result = false;

	switch( pid )
	{
		case Gaffer::BoolPlugTypeId:
		case Gaffer::FloatPlugTypeId:
		case Gaffer::IntPlugTypeId:
		case Gaffer::BoolVectorDataPlugTypeId:
		case Gaffer::FloatVectorDataPlugTypeId:
		case Gaffer::IntVectorDataPlugTypeId:
		case Gaffer::StringPlugTypeId:
		case Gaffer::StringVectorDataPlugTypeId:
		case Gaffer::InternedStringVectorDataPlugTypeId:
		case Gaffer::Color3fPlugTypeId:
		case Gaffer::Color4fPlugTypeId:
		case Gaffer::V3fPlugTypeId:
		case Gaffer::V3iPlugTypeId:
		case Gaffer::V2fPlugTypeId:
		case Gaffer::V2iPlugTypeId:
		case Gaffer::Box3fPlugTypeId:
		case Gaffer::Box3iPlugTypeId:
		case Gaffer::Box2fPlugTypeId:
		case Gaffer::Box2iPlugTypeId:
		case Gaffer::ObjectPlugTypeId:
			result = true;
			break;
		default:
			break;
	}

	return result;
}

bool setPlugFromObject( const Gaffer::Plug* const vplug, Gaffer::ValuePlug* const plug, const IECore::Object* const object )
{
	assert( vplug != 0 );
	assert( plug != 0 );
	assert( object != 0 );

	switch( static_cast<Gaffer::TypeId>( vplug->typeId() ) )
	{
		case Gaffer::BoolPlugTypeId:
			return setNumericPlugValue( static_cast<BoolPlug *>( plug ), object );
		case Gaffer::FloatPlugTypeId:
			return setNumericPlugValue( static_cast<FloatPlug *>( plug ), object );
		case Gaffer::IntPlugTypeId:
			return setNumericPlugValue( static_cast<IntPlug *>( plug ), object );
		case Gaffer::BoolVectorDataPlugTypeId:
			return setTypedObjectPlugValue( static_cast<BoolVectorDataPlug *>( plug ), object );
		case Gaffer::FloatVectorDataPlugTypeId:
			return setTypedObjectPlugValue( static_cast<FloatVectorDataPlug *>( plug ), object );
		case Gaffer::IntVectorDataPlugTypeId:
			return setTypedObjectPlugValue( static_cast<IntVectorDataPlug *>( plug ), object );
		case Gaffer::StringPlugTypeId:
			switch( object->typeId() )
			{
				case IECore::StringDataTypeId:
					IECore::assertedStaticCast< Gaffer::StringPlug >( plug )->setValue(
						IECore::assertedStaticCast< const IECore::StringData >( object )->readable() );
					return true;
				case IECore::InternedStringDataTypeId:
					IECore::assertedStaticCast< Gaffer::StringPlug >( plug )->setValue(
						IECore::assertedStaticCast< const IECore::InternedStringData >( object )->readable().value() );
					return true;
				default:
					return false;
			}
		case Gaffer::StringVectorDataPlugTypeId:
			return setTypedObjectPlugValue( static_cast<StringVectorDataPlug *>( plug ), object );
		case Gaffer::InternedStringVectorDataPlugTypeId:
			return setTypedObjectPlugValue( static_cast<InternedStringVectorDataPlug *>( plug ), object );
		case Gaffer::ObjectPlugTypeId:
			IECore::assertedStaticCast< Gaffer::ObjectPlug >( plug )->setValue( object );
			return true;
		case Gaffer::Color3fPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<const Color3fPlug *>( vplug ), plug, object );
		case Gaffer::Color4fPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<const Color4fPlug *>( vplug ), plug, object );
		case Gaffer::V3fPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<const V3fPlug *>( vplug ), plug, object );
		case Gaffer::V3iPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<const V3iPlug *>( vplug ), plug, object );
		case Gaffer::V2fPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<const V2fPlug *>( vplug ), plug, object );
		case Gaffer::V2iPlugTypeId:
			return setCompoundNumericPlugValue( static_cast<const V2iPlug *>( vplug ), plug, object );
		case Gaffer::Box3fPlugTypeId:
			return setBoxPlugValue( static_cast<const Box3fPlug *>( vplug ), plug, object );
		case Gaffer::Box3iPlugTypeId:
			return setBoxPlugValue( static_cast<const Box3iPlug *>( vplug ), plug, object );
		case Gaffer::Box2fPlugTypeId:
			return setBoxPlugValue( static_cast<const Box2fPlug *>( vplug ), plug, object );
		case Gaffer::Box2iPlugTypeId:
			return setBoxPlugValue( static_cast<const Box2iPlug *>( vplug ), plug, object );
		default:
			return false;
	}
}

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
		( canSetPlugType( static_cast< Gaffer::TypeId >( plug->typeId() ) ) );

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

			if(
				( object->isEqualTo( IECore::NullObject::defaultNullObject() ) ) ||
				( ! setPlugFromObject( vplug, output, object.get() ) ) )
			{
				output->setFrom( IECore::assertedStaticCast< const Gaffer::ValuePlug >(
					correspondingPlug( vplug, output, defaultPlug() ) ) );
			}
		}
	}
}

} // GafferScene
