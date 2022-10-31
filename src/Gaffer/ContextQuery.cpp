//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/ContextQuery.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/TypedObjectPlug.h"

#include "IECore/NullObject.h"

#include "boost/bind.hpp"

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

/// Returns the child of `parentPlug` that has `descendantPlug` as a descendant or is descendantPlug.
/// Throws an Exception if the `descendantPlug` is not a descendant of `parentPlug`.
const Gaffer::ValuePlug *getChildWithDescendant( const Gaffer::Plug *parentPlug, const Gaffer::ValuePlug *descendantPlug )
{
	const ValuePlug *p = descendantPlug;
	while( p )
	{
		if( p->parent() == parentPlug )
		{
			return p;
		}
		p = p->parent<ValuePlug>();
	}

	throw IECore::Exception( "ContextQuery : Plug not in hierarchy." );
}

}  // namespace

namespace Gaffer
{

GAFFER_NODE_DEFINE_TYPE( ContextQuery );

size_t ContextQuery::g_firstPlugIndex = 0;

ContextQuery::ContextQuery( const std::string &name ) : Gaffer::ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ArrayPlug( "queries", Plug::Direction::In, nullptr, 1, std::numeric_limits<size_t>::max(), Plug::Flags::Default, false ) );
	addChild( new ArrayPlug( "out", Plug::Direction::Out, nullptr, 1, std::numeric_limits<size_t>::max(), Plug::Flags::Default, false ) );
}

ContextQuery::~ContextQuery()
{
}

Gaffer::ArrayPlug *ContextQuery::queriesPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::ArrayPlug *ContextQuery::queriesPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 0 );
}

Gaffer::ArrayPlug *ContextQuery::outPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::ArrayPlug *ContextQuery::outPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 1 );
}

Gaffer::NameValuePlug *ContextQuery::addQuery(
	const Gaffer::ValuePlug *plug,
	const std::string &variable
)
{
	NameValuePlugPtr childQueryPlug = new NameValuePlug(
		"",
		plug->createCounterpart( "query", Gaffer::Plug::Direction::In ),
		"query0",
		Gaffer::Plug::Flags::Default
	);
	childQueryPlug->namePlug()->setValue( variable );

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

void ContextQuery::removeQuery( Gaffer::NameValuePlug *plug )
{
	const ValuePlug *outputPlug = outPlugFromQueryPlug( plug );

	queriesPlug()->removeChild( plug );
	outPlug()->removeChild( const_cast<ValuePlug *>( outputPlug ) );
}

void ContextQuery::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs) const
{
	ComputeNode::affects( input, outputs );

	if( queriesPlug()->isAncestorOf( input ) )
	{
		const NameValuePlug *childQueryPlug = input->ancestor<NameValuePlug>();
		if( childQueryPlug == nullptr )
		{
			throw IECore::Exception( "ContextQuery::affects : Query plugs must be \"NameValuePlug\"" );
		}

		const ValuePlug *outputPlug = outPlugFromQueryPlug( childQueryPlug );
		const ValuePlug *valuePlug = outputPlug->getChild<ValuePlug>( g_valuePlugIndex );

		if( input == childQueryPlug->namePlug() )
		{
			addChildPlugsToAffectedOutputs( valuePlug, outputs );

			outputs.push_back( outputPlug->getChild<BoolPlug>( g_existsPlugIndex ) );
		}
		else if( childQueryPlug->valuePlug() == input || childQueryPlug->valuePlug()->isAncestorOf( input ) )
		{
			outputs.push_back(
				correspondingPlug(
					static_cast<const ValuePlug *>( childQueryPlug->valuePlug<ValuePlug>() ),
					runTimeCast<const ValuePlug>( input ),
					valuePlug
				)
			);
		}
	}
}

void ContextQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( outPlug()->isAncestorOf( output ) )
	{
		const ValuePlug *outputPlug = getChildWithDescendant( outPlug(), output );
		const NameValuePlug *childQueryPlug = queryPlugFromOutPlug( output );

		if( output == outputPlug->getChild( g_existsPlugIndex ) )
		{
			h.append( context->variableHash( childQueryPlug->namePlug()->getValue() ) );
			return;
		}

		const ValuePlug *valuePlug = outputPlug->getChild<const ValuePlug>( g_valuePlugIndex );
		if( valuePlug && ( valuePlug->isAncestorOf( output ) || output == valuePlug ) )
		{
			correspondingPlug(
				valuePlug,
				output,
				static_cast<const ValuePlug *>( childQueryPlug->valuePlug() )
			)->hash( h );
			h.append( context->variableHash( childQueryPlug->namePlug()->getValue() ) );
		}
	}
}

void ContextQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( outPlug()->isAncestorOf( output ) )
	{
		const ValuePlug *outputPlug = getChildWithDescendant( outPlug(), output );
		const NameValuePlug *childQueryPlug = queryPlugFromOutPlug( output );

		IECore::DataPtr resultValue = context->getAsData( childQueryPlug->namePlug()->getValue(), nullptr );

		const ValuePlug *valuePlug = outputPlug->getChild<ValuePlug>( g_valuePlugIndex );

		if( output == outputPlug->getChild( g_existsPlugIndex ) )
		{
			bool exists = resultValue && PlugAlgo::canSetValueFromData( valuePlug, resultValue.get() );
			static_cast<BoolPlug *>( output )->setValue( exists );

			return;
		}
		else if( valuePlug && ( valuePlug->isAncestorOf( output ) || output == valuePlug ) )
		{
			if( resultValue && PlugAlgo::setValueFromData( valuePlug, output, resultValue.get() ) )
			{
				return;
			}

			output->setFrom(
				static_cast<const Gaffer::ValuePlug *>(
					correspondingPlug(
						valuePlug,
						output,
						static_cast<const ValuePlug *>( childQueryPlug->valuePlug() )
					)
				)
			);

			return;
		}
	}

	ComputeNode::compute( output, context );

}

const Gaffer::ValuePlug *ContextQuery::outPlugFromQueryPlug( const Gaffer::NameValuePlug *queryPlug ) const
{
	const ValuePlug *topLevelOutput = getChildWithDescendant( queriesPlug(), queryPlug );
	const ValuePlug::ChildContainer &c = queriesPlug()->children();
	const size_t childIndex = std::find( c.begin(), c.end(), topLevelOutput ) - c.begin();

	if( childIndex < outPlug()->children().size() )
	{
		const ValuePlug *outputPlug = outPlug()->getChild<const ValuePlug>( childIndex );
		if( outputPlug )
		{
			return outputPlug;
		}
	}

	throw IECore::Exception( "ContextQuery : \"outPlug\" is missing." );
}

const Gaffer::NameValuePlug *ContextQuery::queryPlugFromOutPlug( const Gaffer::ValuePlug *outputPlug ) const
{
	const ValuePlug *topLevelOutput = getChildWithDescendant( outPlug(), outputPlug );
	const ValuePlug::ChildContainer &c = outPlug()->children();
	const size_t childIndex = std::find( c.begin(), c.end(), topLevelOutput ) - c.begin();

	if( childIndex >= queriesPlug()->children().size() )
	{
		throw IECore::Exception( "ContextQuery : \"query\" plug is missing." );
	}

	if( const NameValuePlug *childQueryPlug = queriesPlug()->getChild<NameValuePlug>( childIndex ) )
	{
		return childQueryPlug;
	}

	throw IECore::Exception( "ContextQuery::queryPlug : Queries must be a \"NameValuePlug\".");

}

Gaffer::BoolPlug *ContextQuery::existsPlugFromQueryPlug( const Gaffer::NameValuePlug *queryPlug )
{
	if( const ValuePlug *oPlug = outPlugFromQueryPlug( queryPlug ) )
	{
		if( const BoolPlug *ePlug = oPlug->getChild<BoolPlug>( g_existsPlugIndex ) )
		{
			return const_cast<Gaffer::BoolPlug*>( ePlug );
		}
	}

	throw IECore::Exception( "ContextQuery : \"exists\" plug is missing or of the wrong type." );
}

Gaffer::ValuePlug *ContextQuery::valuePlugFromQueryPlug( const Gaffer::NameValuePlug *queryPlug )
{
	if( const ValuePlug *oPlug = outPlugFromQueryPlug( queryPlug ) )
	{
		if( const ValuePlug *vPlug = oPlug->getChild<ValuePlug>( g_valuePlugIndex ) )
		{
			return const_cast<Gaffer::ValuePlug*>( vPlug );
		}
	}

	throw IECore::Exception( "ContextQuery : \"value\" plug is missing or of the wrong type." );
}

} // namespace Gaffer
