//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/PrimitiveVariableQuery.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"
#include "IECoreScene/Primitive.h"

#include "boost/container/small_vector.hpp"

#include <limits>

namespace
{

const size_t g_existsPlugIndex = 0;
const size_t g_valuePlugIndex = 1;
const size_t g_typePlugIndex = 2;
const size_t g_interpolationPlugIndex = 3;

const Gaffer::ValuePlug* correspondingPlug(
	const Gaffer::ValuePlug* const parent,
	const Gaffer::ValuePlug* const child,
	const Gaffer::ValuePlug* const other
)
{
	boost::container::small_vector< const Gaffer::ValuePlug*, 4 > path;

	const Gaffer::ValuePlug* plug = child;

	while( plug != parent )
	{
		path.push_back( plug );
		plug = plug->parent< Gaffer::ValuePlug >();
	}

	plug = other;

	while( ! path.empty() )
	{
		plug = plug->getChild< Gaffer::ValuePlug >( path.back()->getName() );
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

/// Returns the index into the child vector of `parentPlug` that is
/// either the `childPlug` itself or an ancestor of childPlug.
/// Throws an Exception if the `childPlug` is not a descendant of `parentPlug`.
size_t getChildIndex( const Gaffer::Plug* const parentPlug, const Gaffer::ValuePlug* const descendantPlug )
{
	const Gaffer::GraphComponent* p = descendantPlug;
	while( p )
	{
		if( p->parent() == parentPlug )
		{
			for( size_t i = 0, eI = parentPlug->children().size(); i < eI; ++i )
			{
				if( parentPlug->getChild( i ) == p )
				{
					return i;
				}
			}
		}
		p = p->parent();
	}

	throw IECore::Exception( "PrimitiveVariableQuery : Plug not in hierarchy." );
}

} // namespace

namespace GafferScene
{

size_t PrimitiveVariableQuery::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( PrimitiveVariableQuery );

PrimitiveVariableQuery::PrimitiveVariableQuery( const std::string& name )
: Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new Gaffer::StringPlug( "location" ) );
	addChild( new Gaffer::ArrayPlug( "queries", Gaffer::Plug::Direction::In,
		nullptr, 1, std::numeric_limits< size_t >::max(), Gaffer::Plug::Flags::Default, false ) );
	addChild( new Gaffer::ArrayPlug( "out", Gaffer::Plug::Direction::Out,
		nullptr, 1, std::numeric_limits< size_t >::max(), Gaffer::Plug::Flags::Default, false ) );
	addChild( new Gaffer::ObjectPlug( "__internalObject", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
}

PrimitiveVariableQuery::~PrimitiveVariableQuery()
{}

ScenePlug* PrimitiveVariableQuery::scenePlug()
{
	return const_cast< ScenePlug* >(
		static_cast< const PrimitiveVariableQuery* >( this )->scenePlug() );
}

const ScenePlug* PrimitiveVariableQuery::scenePlug() const
{
	return getChild< ScenePlug >( g_firstPlugIndex );
}

Gaffer::StringPlug* PrimitiveVariableQuery::locationPlug()
{
	return const_cast< Gaffer::StringPlug* >(
		static_cast< const PrimitiveVariableQuery* >( this )->locationPlug() );
}

const Gaffer::StringPlug* PrimitiveVariableQuery::locationPlug() const
{
	return getChild< Gaffer::StringPlug >( g_firstPlugIndex + 1 );
}

Gaffer::ArrayPlug* PrimitiveVariableQuery::queriesPlug()
{
	return const_cast< Gaffer::ArrayPlug* >(
		static_cast< const PrimitiveVariableQuery* >( this )->queriesPlug() );
}

const Gaffer::ArrayPlug* PrimitiveVariableQuery::queriesPlug() const
{
	return getChild< Gaffer::ArrayPlug >( g_firstPlugIndex + 2 );
}

Gaffer::ArrayPlug* PrimitiveVariableQuery::outPlug()
{
	return const_cast< Gaffer::ArrayPlug* >(
		static_cast< const PrimitiveVariableQuery* >( this )->outPlug() );
}

const Gaffer::ArrayPlug* PrimitiveVariableQuery::outPlug() const
{
	return getChild< Gaffer::ArrayPlug >( g_firstPlugIndex + 3 );
}

const Gaffer::ObjectPlug* PrimitiveVariableQuery::internalObjectPlug() const
{
	return getChild< Gaffer::ObjectPlug >( g_firstPlugIndex + 4 );
}

Gaffer::NameValuePlug* PrimitiveVariableQuery::addQuery(
	const Gaffer::ValuePlug* const plug, const std::string& variable )
{
	// NOTE : create the query plug with name and value child plugs

	Gaffer::NameValuePlugPtr childQueryPlug = new Gaffer::NameValuePlug(
		"",
		plug->createCounterpart( "query0", Gaffer::Plug::Direction::In ),
		"query0",
		Gaffer::Plug::Flags::Default
	);
	childQueryPlug->namePlug()->setValue( variable );

	// NOTE : create the output plug with exists, value, type and interpolation plugs

	Gaffer::ValuePlugPtr newOutPlug = new Gaffer::ValuePlug( "out0", Gaffer::Plug::Direction::Out );
	newOutPlug->addChild(
		new Gaffer::BoolPlug(
			"exists",
			Gaffer::Plug::Direction::Out,
			false ) );
	newOutPlug->addChild( plug->createCounterpart( "value", Gaffer::Plug::Direction::Out ) );
	newOutPlug->addChild(
		new Gaffer::StringPlug(
			"type",
			Gaffer::Plug::Direction::Out ) );
	newOutPlug->addChild(
		new Gaffer::IntPlug(
			"interpolation",
			Gaffer::Plug::Direction::Out,
			static_cast< int >( IECoreScene::PrimitiveVariable::Invalid ),
			static_cast< int >( IECoreScene::PrimitiveVariable::Invalid ),
			static_cast< int >( IECoreScene::PrimitiveVariable::FaceVarying ) ) );

	// NOTE : store new query and output plugs

	outPlug()->addChild( newOutPlug );
	queriesPlug()->addChild( childQueryPlug );

	return childQueryPlug.get();
}

void PrimitiveVariableQuery::removeQuery( Gaffer::NameValuePlug* const plug )
{
	const Gaffer::ValuePlug* const outputPlug = outPlugFromQuery( plug );

	queriesPlug()->removeChild( plug );
	outPlug()->removeChild( const_cast< Gaffer::ValuePlug* >( outputPlug ) );
}

const Gaffer::BoolPlug* PrimitiveVariableQuery::existsPlugFromQuery( const Gaffer::NameValuePlug* const queryPlug ) const
{
	const Gaffer::ValuePlug* const outputPlug = outPlugFromQuery( queryPlug );
	if( g_existsPlugIndex < outputPlug->children().size() )
	{
		if( const Gaffer::BoolPlug* const existsPlug =
			outputPlug->getChild< const Gaffer::BoolPlug >( g_existsPlugIndex ) )
		{
			return existsPlug;
		}
	}

	throw IECore::Exception( "PrimitiveVariableQuery : \"exists\" plug is missing." );
}

const Gaffer::ValuePlug* PrimitiveVariableQuery::valuePlugFromQuery( const Gaffer::NameValuePlug* const queryPlug ) const
{
	const Gaffer::ValuePlug* const outputPlug = outPlugFromQuery( queryPlug );
	if( g_valuePlugIndex < outputPlug->children().size() )
	{
		if( const Gaffer::ValuePlug* const valuePlug =
			outputPlug->getChild< const Gaffer::ValuePlug >( g_valuePlugIndex ) )
		{
			return valuePlug;
		}
	}

	throw IECore::Exception( "PrimitiveVariableQuery : \"value\" plug is missing." );
}

const Gaffer::StringPlug* PrimitiveVariableQuery::typePlugFromQuery( const Gaffer::NameValuePlug* const queryPlug ) const
{
	const Gaffer::ValuePlug* const outputPlug = outPlugFromQuery( queryPlug );
	if( g_typePlugIndex < outputPlug->children().size() )
	{
		if( const Gaffer::StringPlug* const typePlug =
			outputPlug->getChild< const Gaffer::StringPlug >( g_typePlugIndex ) )
		{
			return typePlug;
		}
	}

	throw IECore::Exception( "PrimitiveVariableQuery : \"type\" plug is missing." );
}

const Gaffer::IntPlug* PrimitiveVariableQuery::interpolationPlugFromQuery( const Gaffer::NameValuePlug* const queryPlug ) const
{
	const Gaffer::ValuePlug* const outputPlug = outPlugFromQuery( queryPlug );
	if( g_interpolationPlugIndex < outputPlug->children().size() )
	{
		if( const Gaffer::IntPlug* const interpolationPlug =
			outputPlug->getChild< const Gaffer::IntPlug >( g_interpolationPlugIndex ) )
		{
			return interpolationPlug;
		}
	}

	throw IECore::Exception( "PrimitiveVariableQuery : \"interpolation\" plug is missing." );
}

const Gaffer::ValuePlug* PrimitiveVariableQuery::outPlugFromQuery( const Gaffer::NameValuePlug* const queryPlug ) const
{
	const size_t childIndex = getChildIndex( queriesPlug(), queryPlug );

	if( childIndex >= outPlug()->children().size() )
	{
		throw IECore::Exception( "PrimitiveVariableQuery : \"out\" plug is missing." );
	}

	if( const Gaffer::ValuePlug* const childOutPlug = outPlug()->getChild< const Gaffer::ValuePlug >( childIndex ) )
	{
		if( childOutPlug->typeId() == Gaffer::ValuePlug::staticTypeId() )
		{
			return childOutPlug;
		}
	}

	throw IECore::Exception( "PrimitiveVariableQuery : \"out\" plug must be a `ValuePlug`." );
}

const Gaffer::NameValuePlug* PrimitiveVariableQuery::queryPlug( const Gaffer::ValuePlug* const outputPlug ) const
{
	const size_t childIndex = getChildIndex( outPlug(), outputPlug );

	if( childIndex >= queriesPlug()->children().size() )
	{
		throw IECore::Exception( "PrimitiveVariableQuery : \"query\" plug is missing." );
	}

	if( const Gaffer::NameValuePlug* const childQueryPlug = queriesPlug()->getChild< Gaffer::NameValuePlug >( childIndex ) )
	{
		return childQueryPlug;
	}

	throw IECore::Exception( "PrimitiveVariableQuery::queryPlug : Queries must be a \"NameValuePlug\".");
}

const Gaffer::ValuePlug* PrimitiveVariableQuery::outPlug( const Gaffer::ValuePlug* const outputPlug ) const
{
	const size_t childIndex = getChildIndex( outPlug(), outputPlug );

	if( const Gaffer::ValuePlug* const outputPlug = outPlug()->getChild< const Gaffer::ValuePlug >( childIndex ) )
	{
		if( outputPlug->typeId() != Gaffer::ValuePlug::staticTypeId() )
		{
			throw IECore::Exception( "PrimitiveVariableQuery : \"out\" plug must be a `ValuePlug`." );
		}
		return outputPlug;
	}

	throw IECore::Exception( "PrimitiveVariableQuery : \"out\" plug is missing or of the wrong type.");
}

void PrimitiveVariableQuery::affects( const Gaffer::Plug* const input, AffectedPlugsContainer& outputs ) const
{
	Gaffer::ComputeNode::affects( input, outputs );

	if( input == internalObjectPlug() )
	{
		addChildPlugsToAffectedOutputs( outPlug(), outputs );
	}
	else if(
		( input == locationPlug() ) ||
		( input == scenePlug()->existsPlug() ) ||
		( input == scenePlug()->objectPlug() ) )
	{
		outputs.push_back( internalObjectPlug() );
	}
	else if( queriesPlug()->isAncestorOf( input ) )
	{
		const Gaffer::NameValuePlug* const childQueryPlug = input->ancestor< Gaffer::NameValuePlug >();
		if( childQueryPlug == nullptr )
		{
			throw IECore::Exception( "PrimitiveVariableQuery::affects : Query plugs must be \"NameValuePlug\"" );
		}

		const Gaffer::ValuePlug* const outputPlug = outPlugFromQuery( childQueryPlug );
		const Gaffer::ValuePlug* const valuePlug = outputPlug->getChild< const Gaffer::ValuePlug >( g_valuePlugIndex );

		if( input == childQueryPlug->namePlug() )
		{
			addChildPlugsToAffectedOutputs( valuePlug, outputs );
			outputs.push_back( outputPlug->getChild< const Gaffer::BoolPlug >( g_existsPlugIndex ) );
			outputs.push_back( outputPlug->getChild< const Gaffer::StringPlug >( g_typePlugIndex ) );
			outputs.push_back( outputPlug->getChild< const Gaffer::IntPlug >( g_interpolationPlugIndex ) );
		}
		else if( childQueryPlug->valuePlug() == input || childQueryPlug->valuePlug()->isAncestorOf( input ) )
		{
			outputs.push_back(
				correspondingPlug(
					static_cast< const Gaffer::ValuePlug* >( childQueryPlug->valuePlug< const Gaffer::ValuePlug >() ),
					IECore::runTimeCast< const Gaffer::ValuePlug >( input ),
					valuePlug
				)
			);
		}
	}
}

void PrimitiveVariableQuery::hash( const Gaffer::ValuePlug* const output, const Gaffer::Context* const context, IECore::MurmurHash& h ) const
{
	Gaffer::ComputeNode::hash( output, context, h );

	if( output == internalObjectPlug() )
	{
		const std::string loc = locationPlug()->getValue();

		if( ! loc.empty() )
		{
			const ScenePlug* const splug = scenePlug();
			const ScenePlug::ScenePath path = ScenePlug::stringToPath( loc );

			if( splug->exists( path ) )
			{
				h.append( splug->objectHash( path ) );
			}
		}
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		const Gaffer::ValuePlug* const outputPlug = outPlug( output );
		const Gaffer::NameValuePlug* const childQueryPlug = queryPlug( outputPlug );

		if(
			( output == outputPlug->getChild( g_existsPlugIndex        ) ) ||
			( output == outputPlug->getChild( g_typePlugIndex          ) ) ||
			( output == outputPlug->getChild( g_interpolationPlugIndex ) ) )
		{
			internalObjectPlug()->hash( h );
			childQueryPlug->namePlug()->hash( h );
			return;
		}

		const Gaffer::ValuePlug* const valuePlug = outputPlug->getChild< const Gaffer::ValuePlug >( g_valuePlugIndex );
		if( valuePlug && ( valuePlug->isAncestorOf( output ) || output == valuePlug ) )
		{
			internalObjectPlug()->hash( h );
			childQueryPlug->namePlug()->hash( h );
			correspondingPlug(
				valuePlug,
				output,
				static_cast< const Gaffer::ValuePlug* >( childQueryPlug->valuePlug() )
			)->hash( h );
		}
	}
}

void PrimitiveVariableQuery::compute( Gaffer::ValuePlug* const output, const Gaffer::Context* const context) const
{
	if( output == internalObjectPlug() )
	{
		// NOTE : cache the primitive at the specified location in the input scene
		//        as all queries operate on this same primitive.

		IECore::ConstObjectPtr object( IECore::NullObject::defaultNullObject() );
		const std::string loc = locationPlug()->getValue();

		if( ! loc.empty() )
		{
			const ScenePlug* const splug = scenePlug();
			const ScenePlug::ScenePath path = ScenePlug::stringToPath( loc );

			if( splug->exists( path ) )
			{
				object = splug->object( path );
			}
		}

		IECore::assertedStaticCast< Gaffer::ObjectPlug >( output )->setValue( object );
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		// NOTE : retrieve the cached primitive and query

		const IECore::ConstObjectPtr object = internalObjectPlug()->getValue();
		assert( object );

		const Gaffer::ValuePlug* const outputPlug = outPlug( output );
		const Gaffer::NameValuePlug* const childQueryPlug = queryPlug( outputPlug );

		// NOTE : find named primitive variable

		IECoreScene::PrimitiveVariable resultVariable;
		if( const IECoreScene::Primitive* const primitive =
			IECore::runTimeCast< const IECoreScene::Primitive >( object.get() ) )
		{
			const IECoreScene::PrimitiveVariableMap::const_iterator it =
				primitive->variables.find( childQueryPlug->namePlug()->getValue() );

			if( it != primitive->variables.end() )
			{
				resultVariable = it->second;
			}
		}

		const Gaffer::ValuePlug* const valuePlug =
			outputPlug->getChild< const Gaffer::ValuePlug >( g_valuePlugIndex );

		if( output == outputPlug->getChild( g_existsPlugIndex ) )
		{
			// NOTE : set the query's output exists plug. no need to expand indexed data

			static_cast< Gaffer::BoolPlug* >( output )->setValue(
				static_cast< bool >( resultVariable.data ) );

			return;
		}
		else if( output == outputPlug->getChild( g_typePlugIndex ) )
		{
			// NOTE : set the query's output type plug. no need to expand indexed data

			static_cast< Gaffer::StringPlug* >( output )->setValue(
				( resultVariable.data )
					? resultVariable.data->typeName()
					: static_cast< const char* >( "" ) );
		}
		else if( output == outputPlug->getChild( g_interpolationPlugIndex ) )
		{
			// NOTE : set the query's output interpolation plug. no need to expand indexed data

			static_cast< Gaffer::IntPlug* >( output )->setValue( static_cast< int >(
				( resultVariable.data )
					? resultVariable.interpolation
					: IECoreScene::PrimitiveVariable::Invalid ) );

			return;
		}
		else if( valuePlug && ( valuePlug->isAncestorOf( output ) || output == valuePlug ) )
		{
			// NOTE : set the query's output value plug. variable data may be indexed. only expand when neccessary

			if( resultVariable.data )
			{
				if( resultVariable.indices )
				{
					if( Gaffer::PlugAlgo::canSetValueFromData( valuePlug, resultVariable.data.get() ) )
					{
						const IECore::DataPtr resultData = resultVariable.expandedData();
						Gaffer::PlugAlgo::setValueFromData( valuePlug, output, resultData.get() );

						return;
					}
				}
				else if( Gaffer::PlugAlgo::setValueFromData( valuePlug, output, resultVariable.data.get() ) )
				{
					return;
				}
			}

			output->setFrom(
				static_cast< const Gaffer::ValuePlug* >(
					correspondingPlug(
						valuePlug,
						output,
						static_cast< const Gaffer::ValuePlug* >( childQueryPlug->valuePlug() )
					)
				)
			);

			return;
		}
	}

	Gaffer::ComputeNode::compute( output, context );
}

} // GafferScene
