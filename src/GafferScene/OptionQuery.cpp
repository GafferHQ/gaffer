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

#include "GafferScene/OptionQuery.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/TypedObjectPlug.h"

#include "IECore/NullObject.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;

namespace
{

const size_t g_existsPlugIndex = 0;
const size_t g_valuePlugIndex = 1;

/// \todo: Can the next function be move to somewhere to be shared with `AttributeQuery`?

const Gaffer::ValuePlug *correspondingPlug(
	const Gaffer::ValuePlug *parent,
	const Gaffer::ValuePlug *child,
	const Gaffer::ValuePlug *other
)
{
	boost::container::small_vector< const Gaffer::ValuePlug*, 4 > path;

	const Gaffer::ValuePlug *plug = child;

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

void addChildPlugsToAffectedOutputs( const Gaffer::Plug* plug, Gaffer::DependencyNode::AffectedPlugsContainer& outputs )
{
	if( plug->children().empty() )
	{
		outputs.push_back( plug );
	}
	else
	{
		for( const Gaffer::PlugPtr& child : Gaffer::Plug::OutputRange( *plug ) )
		{
			addChildPlugsToAffectedOutputs( child.get(), outputs );
		}
	}
}

/// Returns the index into the child vector of `parentPlug` that is
/// either the `childPlug` itself or an ancestor of childPlug.
/// Throws an Exception if the `childPlug` is not a descendant of `parentPlug`.
size_t getChildIndex( const Gaffer::Plug *parentPlug, const Gaffer::ValuePlug *descendantPlug )
{
	const GraphComponent *p = descendantPlug;
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

	throw IECore::Exception( "OptionQuery : Plug not in hierarchy." );
}

}  // namespace

namespace GafferScene
{

GAFFER_NODE_DEFINE_TYPE( OptionQuery );

const std::string g_namePrefix = "option:";

size_t OptionQuery::g_firstPlugIndex = 0;

OptionQuery::OptionQuery( const std::string &name ) : Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "scene" ) );
	/// \todo See notes in `ShaderQuery::ShaderQuery`.
	addChild( new ArrayPlug( "queries", Plug::Direction::In, nullptr, 1, std::numeric_limits<size_t>::max(), Plug::Flags::Default, false ) );

	addChild( new ArrayPlug( "out", Plug::Direction::Out, nullptr, 1, std::numeric_limits<size_t>::max(), Plug::Flags::Default, false ) );
}

OptionQuery::~OptionQuery()
{
}

ScenePlug *OptionQuery::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *OptionQuery::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::ArrayPlug *OptionQuery::queriesPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ArrayPlug *OptionQuery::queriesPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ArrayPlug *OptionQuery::outPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ArrayPlug *OptionQuery::outPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 2 );
}

Gaffer::NameValuePlug *OptionQuery::addQuery(
	const Gaffer::ValuePlug *plug,
	const std::string &option
)
{
	NameValuePlugPtr childQueryPlug = new NameValuePlug(
		"",
		plug->createCounterpart( "query0", Gaffer::Plug::Direction::In ),
		"query0",
		Gaffer::Plug::Flags::Default
	);
	childQueryPlug->namePlug()->setValue( option );

	ValuePlugPtr newOutPlug = new ValuePlug( "out0", Gaffer::Plug::Direction::Out );
	newOutPlug->addChild(
		new BoolPlug(
			"exists",
			Gaffer::Plug::Direction::Out,
			false
		)
	);
	newOutPlug->addChild( plug->createCounterpart( "value", Gaffer::Plug::Direction::Out ) );

	outPlug()->addChild( newOutPlug );

	queriesPlug()->addChild( childQueryPlug );

	return childQueryPlug.get();
}

void OptionQuery::removeQuery( Gaffer::NameValuePlug *plug )
{
	const ValuePlug *oPlug = outPlugFromQuery( plug );

	queriesPlug()->removeChild( plug );
	outPlug()->removeChild( const_cast<ValuePlug *>( oPlug ) );
}

void OptionQuery::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs) const
{
	ComputeNode::affects( input, outputs );

	if( input == scenePlug()->globalsPlug() )
	{
		addChildPlugsToAffectedOutputs( outPlug(), outputs );
	}

	else if( queriesPlug()->isAncestorOf( input ) )
	{
		const NameValuePlug *childQueryPlug = input->ancestor<NameValuePlug>();
		if( childQueryPlug == nullptr )
		{
			throw IECore::Exception( "OptionQuery::affects : Query plugs must be \"NameValuePlug\"" );
		}

		const ValuePlug *vPlug = valuePlugFromQuery( childQueryPlug );

		if( input == childQueryPlug->namePlug() )
		{
			addChildPlugsToAffectedOutputs( vPlug, outputs );

			outputs.push_back( existsPlugFromQuery( childQueryPlug ) );
		}
		else if( childQueryPlug->valuePlug() == input || childQueryPlug->valuePlug()->isAncestorOf( input ) )
		{
			outputs.push_back(
				correspondingPlug(
					static_cast<const ValuePlug *>( childQueryPlug->valuePlug<ValuePlug>() ),
					runTimeCast<const ValuePlug>( input ),
					vPlug
				)
			);
		}
	}
}

void OptionQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( outPlug()->isAncestorOf( output ) )
	{
		ScenePlug::GlobalScope globalScope( context );
		const ValuePlug *oPlug = outPlug( output );

		if( output == oPlug->getChild( g_existsPlugIndex ) )
		{
			const NameValuePlug *childQueryPlug = queryPlug( output );
			childQueryPlug->namePlug()->hash( h );
			scenePlug()->globalsPlug()->hash( h );
		}

		else if(
			oPlug->getChild( g_valuePlugIndex )->isAncestorOf( output ) ||
			output == oPlug->getChild( g_valuePlugIndex )
		)
		{
			const NameValuePlug *childQueryPlug = queryPlug( output );
			childQueryPlug->namePlug()->hash( h );
			scenePlug()->globalsPlug()->hash( h );

			correspondingPlug(
				valuePlugFromQuery( childQueryPlug ),
				output,
				static_cast<const ValuePlug *>( childQueryPlug->valuePlug() )
			)->hash( h );
		}
	}
}

void OptionQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( outPlug()->isAncestorOf( output ) )
	{
		ScenePlug::GlobalScope globalScope( context );
		const ValuePlug *oPlug = outPlug( output );

		if( output == oPlug->getChild( g_existsPlugIndex ) )
		{
			const std::string optionName = queryPlug( output )->namePlug()->getValue();
			bool exists = false;
			if( optionName.size() )
			{
				ConstCompoundObjectPtr globals = scenePlug()->globalsPlug()->getValue();
				exists = globals->members().count( g_namePrefix + optionName );
			}
			static_cast<BoolPlug *>( output )->setValue( exists );
			return;
		}

		const ValuePlug *valuePlug = oPlug->getChild<ValuePlug>( g_valuePlugIndex );
		if( output == valuePlug || valuePlug->isAncestorOf( output ) )
		{
			const NameValuePlug *childQueryPlug = queryPlug( output );

			const std::string optionName = childQueryPlug->namePlug()->getValue();
			ConstObjectPtr object;
			if( optionName.size() )
			{
				ConstCompoundObjectPtr globals = scenePlug()->globalsPlug()->getValue();
				object = globals->member<Object>( g_namePrefix + optionName );
			}

			if( object )
			{
				if( auto objectPlug = runTimeCast<ObjectPlug>( output ) )
				{
					objectPlug->setValue( object );
					return;
				}
				else if( auto data = runTimeCast<const Data>( object.get() ) )
				{
					if( PlugAlgo::setValueFromData( valuePlug, output, data ) )
					{
						return;
					}
				}
			}

			output->setFrom(
				correspondingPlug( valuePlug, output, childQueryPlug->valuePlug<ValuePlug>() )
			);
			return;
		}
	}

	ComputeNode::compute( output, context );

}

const Gaffer::BoolPlug *OptionQuery::existsPlugFromQuery( const Gaffer::NameValuePlug *queryPlug ) const
{
	if( const ValuePlug *oPlug = outPlugFromQuery( queryPlug ) )
	{
		return oPlug->getChild<BoolPlug>( g_existsPlugIndex );
	}

	throw IECore::Exception( "OptionQuery : \"exists\" plug is missing or of the wrong type." );
}

const Gaffer::ValuePlug *OptionQuery::valuePlugFromQuery( const Gaffer::NameValuePlug *queryPlug ) const
{
	if( const ValuePlug *oPlug = outPlugFromQuery( queryPlug ) )
	{
		return oPlug->getChild<const ValuePlug>( g_valuePlugIndex );
	}

	throw IECore::Exception( "OptionQuery : \"value\" plug is missing." );
}

const Gaffer::ValuePlug *OptionQuery::outPlugFromQuery( const Gaffer::NameValuePlug *queryPlug ) const
{
	size_t childIndex = getChildIndex( queriesPlug(), queryPlug );

	if( childIndex < outPlug()->children().size() )
	{
		const ValuePlug *oPlug = outPlug()->getChild<const ValuePlug>( childIndex );
		if( oPlug != nullptr && oPlug->typeId() != Gaffer::ValuePlug::staticTypeId() )
		{
			throw IECore::Exception( "OptionQuery : \"outPlug\" must be a `ValuePlug`."  );
		}
		return outPlug()->getChild<ValuePlug>( childIndex );
	}

	throw IECore::Exception( "OptionQuery : \"outPlug\" is missing." );
}

const Gaffer::NameValuePlug *OptionQuery::queryPlug( const Gaffer::ValuePlug *outputPlug ) const
{
	const size_t childIndex = getChildIndex( outPlug(), outputPlug );

	if( childIndex >= queriesPlug()->children().size() )
	{
		throw IECore::Exception( "OptionQuery : \"query\" plug is missing." );
	}

	if( const NameValuePlug *childQueryPlug = queriesPlug()->getChild<NameValuePlug>( childIndex ) )
	{
		return childQueryPlug;
	}

	throw IECore::Exception( "OptionQuery::queryPlug : Queries must be a \"NameValuePlug\".");

}

const Gaffer::ValuePlug *OptionQuery::outPlug( const Gaffer::ValuePlug *outputPlug ) const
{
	size_t childIndex = getChildIndex( outPlug(), outputPlug );

	if( const ValuePlug *result = outPlug()->getChild<const ValuePlug>( childIndex ) )
	{
		return result;
	}

	throw IECore::Exception( "OptionQuery : \"out\" plug is missing or of the wrong type.");
}

}  // namespace GafferScene
