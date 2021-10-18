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

#include "Gaffer/Switch.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/ContextAlgo.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/NameValuePlug.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace Gaffer;

static IECore::InternedString g_inPlugsName( "in" );
static IECore::InternedString g_outPlugName( "out" );

GAFFER_NODE_DEFINE_TYPE( Switch );

size_t Switch::g_firstPlugIndex = 0;

Switch::Switch( const std::string &name)
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "index", Gaffer::Plug::In, 0, 0 ) );
	addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );

	childAddedSignal().connect( boost::bind( &Switch::childAdded, this, ::_2 ) );
	plugSetSignal().connect( boost::bind( &Switch::plugSet, this, ::_1 ) );
	plugInputChangedSignal().connect( boost::bind( &Switch::plugInputChanged, this, ::_1 ) );
}

Switch::~Switch()
{
}

void Switch::setup( const Plug *plug )
{
	if( inPlugs() )
	{
		throw IECore::Exception( "Switch already has an \"in\" plug." );
	}
	if( outPlug() )
	{
		throw IECore::Exception( "Switch already has an \"out\" plug." );
	}

	PlugPtr inElement = plug->createCounterpart( "in0", Plug::In );
	MetadataAlgo::copyColors( plug , inElement.get() , /* overwrite = */ false  );
	inElement->setFlags( Plug::Serialisable, true );
	ArrayPlugPtr in = new ArrayPlug(
		g_inPlugsName,
		Plug::In,
		inElement,
		0,
		Imath::limits<size_t>::max()
	);
	addChild( in );

	PlugPtr out = plug->createCounterpart( g_outPlugName, Plug::Out );
	out->setFlags( Plug::Serialisable, true );
	MetadataAlgo::copyColors( plug , out.get() , /* overwrite = */ false  );
	addChild( out );
}

ArrayPlug *Switch::inPlugs()
{
	return getChild<ArrayPlug>( g_inPlugsName );
}

const ArrayPlug *Switch::inPlugs() const
{
	return getChild<ArrayPlug>( g_inPlugsName );
}

Plug *Switch::outPlug()
{
	return getChild<Plug>( g_outPlugName );
}

const Plug *Switch::outPlug() const
{
	return getChild<Plug>( g_outPlugName );
}

Plug *Switch::activeInPlug()
{
	return activeInPlug( outPlug() );
}

const Plug *Switch::activeInPlug() const
{
	return activeInPlug( outPlug() );
}

Plug *Switch::activeInPlug( const Plug *outPlug )
{
	return const_cast<Plug *>( oppositePlug( outPlug ? outPlug : this->outPlug(), Context::current() ) );
}

const Plug *Switch::activeInPlug( const Plug *outPlug ) const
{
	return oppositePlug( outPlug ? outPlug : this->outPlug(), Context::current() );
}

IntPlug *Switch::indexPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const IntPlug *Switch::indexPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

BoolPlug *Switch::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const BoolPlug *Switch::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void Switch::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == enabledPlug() ||
		input == indexPlug()
	)
	{
		if( const Plug *out = outPlug() )
		{
			if( out->children().size() )
			{
				for( Plug::RecursiveOutputIterator it( out ); !it.done(); ++it )
				{
					if( !(*it)->children().size() )
					{
						outputs.push_back( it->get() );
					}
				}
			}
			else
			{
				outputs.push_back( out );
			}
		}
	}
	else if( input->direction() == Plug::In )
	{
		if( const Plug *output = oppositePlug( input ) )
		{
			if( !output->getInput() )
			{
				outputs.push_back( output );
			}
		}
	}
}

void Switch::childAdded( GraphComponent *child )
{
	ArrayPlug *inPlugs = this->inPlugs();
	if( child->parent<Plug>() == inPlugs )
	{
		// Because inputIndex() wraps on the number of children,
		// the addition of a new one means we must update.
		updateInternalConnection();
	}
	else if( child == inPlugs )
	{
		// Our "in" plug has just been added. Update our internal connection,
		// and connect up so we can respond when extra inputs are added.
		updateInternalConnection();
		inPlugs->childAddedSignal().connect( boost::bind( &Switch::childAdded, this, ::_2 ) );
	}
	else if( child == outPlug() )
	{
		// Our "out" plug has just been added. Make sure it has
		// an appropriate internal connection.
		updateInternalConnection();
	}
}

Plug *Switch::correspondingInput( const Plug *output )
{
	return const_cast<Plug *>( oppositePlug( output ) );
}

const Plug *Switch::correspondingInput( const Plug *output ) const
{
	return oppositePlug( output );
}

bool Switch::acceptsInput( const Plug *plug, const Plug *inputPlug ) const
{
	if( !ComputeNode::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( !inputPlug )
	{
		return true;
	}

	if( plug->direction() == Plug::In )
	{
		if( const Plug *opposite = oppositePlug( plug ) )
		{
			if( !opposite->acceptsInput( inputPlug ) )
			{
				return false;
			}
		}
	}

	return true;
}

void Switch::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	if( const ValuePlug *input = IECore::runTimeCast<const ValuePlug>( oppositePlug( output, context ) ) )
	{
		h = input->hash();
		return;
	}

	ComputeNode::hash( output, context, h );
}

void Switch::compute( ValuePlug *output, const Context *context ) const
{
	if( const ValuePlug *input = IECore::runTimeCast<const ValuePlug>( oppositePlug( output, context ) ) )
	{
		output->setFrom( input );
		return;
	}

	ComputeNode::compute( output, context );
}

void Switch::plugSet( Plug *plug )
{
	if( plug == indexPlug() || plug == enabledPlug() )
	{
		updateInternalConnection();
	}
}

void Switch::plugInputChanged( Plug *plug )
{
	if( plug == indexPlug() || plug == enabledPlug() )
	{
		updateInternalConnection();
	}
}

size_t Switch::inputIndex( const Context *context ) const
{
	const ArrayPlug *inPlugs = this->inPlugs();
	const size_t numInputs = inPlugs ? inPlugs->children().size() : 0;
	if( numInputs <= 1 )
	{
		return 0;
	}

	// Find a plug we can use to create a GlobalScope, accounting for the
	// NameValuePlugs created by NameSwitch.
	const Plug *globalScopePlug = inPlugs->getChild<Plug>( 0 );
	if( auto nameValuePlug = IECore::runTimeCast<const NameValuePlug>( globalScopePlug ) )
	{
		globalScopePlug = nameValuePlug->valuePlug();
	}

	const BoolPlug *enabledPlug = this->enabledPlug();
	const IntPlug *indexPlug = this->indexPlug();

	// Create a GlobalScope if either the `index` or `enabled` plugs will launch
	// an upstream compute. This avoids leakage of context variables such as
	// `scene:path`.
	boost::optional<ContextAlgo::GlobalScope> globalScope;
	if( variesWithContext( enabledPlug ) || variesWithContext( indexPlug ) )
	{
		globalScope.emplace( context, globalScopePlug );
	}

	if( !enabledPlug->getValue() )
	{
		return 0;
	}

	const size_t index = indexPlug->getValue();
	if( inPlugs->resizeWhenInputsChange() )
	{
		// Last input is always unconnected, so should be ignored.
		return index % (numInputs - 1);
	}
	else
	{
		return index % numInputs;
	}
}

const Plug *Switch::oppositePlug( const Plug *plug, const Context *context ) const
{
	const ArrayPlug *inPlugs = this->inPlugs();
	const Plug *outPlug = this->outPlug();
	if( !inPlugs || !outPlug )
	{
		return nullptr;
	}

	// Find the ancestorPlug - this is either a child of inPlugs or it
	// is outPlug. At the same time, fill names with the names of the hierarchy
	// between plug and ancestorPlug.
	const Plug *ancestorPlug = nullptr;
	std::vector<IECore::InternedString> names;
	while( plug )
	{
		const GraphComponent *plugParent = plug->parent();
		if( plugParent == inPlugs || plug == outPlug )
		{
			ancestorPlug = plug;
			break;
		}
		else
		{
			names.push_back( plug->getName() );
			plug = static_cast<const Plug *>( plugParent );
		}
	}

	if( !ancestorPlug )
	{
		return nullptr;
	}

	// Now we can find the opposite for this ancestor plug.
	const Plug *oppositeAncestorPlug = nullptr;
	if( plug->direction() == Plug::Out )
	{
		const size_t i = context ? inputIndex( context ) : 0;
		oppositeAncestorPlug = inPlugs->getChild<Plug>( i );
	}
	else
	{
		oppositeAncestorPlug = outPlug;
	}

	// And then find the opposite of plug by traversing down from the ancestor plug.
	const Plug *result = oppositeAncestorPlug;
	for( auto it = names.rbegin(), eIt = names.rend(); it != eIt; ++it )
	{
		result = result->getChild<Plug>( *it );
	}

	return result;
}

bool Switch::variesWithContext( const Plug *plug ) const
{
	plug = plug->source<Gaffer::Plug>();
	return plug->direction() == Plug::Out && IECore::runTimeCast<const ComputeNode>( plug->node() );
}

void Switch::updateInternalConnection()
{
	Plug *out = outPlug();
	if( !out )
	{
		return;
	}

	if( variesWithContext( enabledPlug() ) || variesWithContext( indexPlug() ) )
	{
		// We can't use an internal connection to implement the switch,
		// because the index might vary from context to context. We must
		// therefore implement switching via hash()/compute().
		out->setInput( nullptr );
		return;
	}

	Plug *in = const_cast<Plug *>( oppositePlug( out, Context::current() ) );
	out->setInput( in );
}
