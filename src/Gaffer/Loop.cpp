//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#include "Gaffer/Loop.h"

#include "Gaffer/ContextAlgo.h"
#include "Gaffer/MetadataAlgo.h"

#include "boost/bind/bind.hpp"

namespace Gaffer
{

GAFFER_NODE_DEFINE_TYPE( Loop );

Loop::Loop( const std::string &name )
	:	ComputeNode( name ), m_inPlugIndex( 0 ), m_outPlugIndex( 0 ), m_firstPlugIndex( 0 )
{
	// Connect to `childAddedSignal()` so we can set ourselves up later when the
	// appropriate plugs are added manually.
	/// \todo Remove this and do all the work in `setup()`.
	m_childAddedConnection = childAddedSignal().connect( boost::bind( &Loop::childAdded, this ) );
}

Loop::~Loop()
{
}

void Loop::setup( const ValuePlug *plug )
{
	if( inPlug() )
	{
		throw IECore::Exception( "Loop already has an \"in\" plug." );
	}
	if( outPlug() )
	{
		throw IECore::Exception( "Loop already has an \"out\" plug." );
	}

	PlugPtr in = plug->createCounterpart( "in", Plug::In );
	MetadataAlgo::copyColors( plug , in.get() , /* overwrite = */ false  );
	in->setFlags( Plug::Serialisable, true );
	addChild( in );

	PlugPtr out = plug->createCounterpart( "out", Plug::Out );
	MetadataAlgo::copyColors( plug , out.get() , /* overwrite = */ false  );
	addChild( out );
}

ValuePlug *Loop::inPlug()
{
	return m_inPlugIndex ? getChild<ValuePlug>( m_inPlugIndex ) : nullptr;
}

const ValuePlug *Loop::inPlug() const
{
	return m_inPlugIndex ? getChild<ValuePlug>( m_inPlugIndex ) : nullptr;
}

ValuePlug *Loop::outPlug()
{
	return m_outPlugIndex ? getChild<ValuePlug>( m_outPlugIndex ) : nullptr;
}

const ValuePlug *Loop::outPlug() const
{
	return m_outPlugIndex ? getChild<ValuePlug>( m_outPlugIndex ) : nullptr;
}

ValuePlug *Loop::nextPlug()
{
	return m_firstPlugIndex ? getChild<ValuePlug>( m_firstPlugIndex ) : nullptr;
}

const ValuePlug *Loop::nextPlug() const
{
	return m_firstPlugIndex ? getChild<ValuePlug>( m_firstPlugIndex ) : nullptr;
}

ValuePlug *Loop::previousPlug()
{
	return m_firstPlugIndex ? getChild<ValuePlug>( m_firstPlugIndex + 1 ) : nullptr;
}

const ValuePlug *Loop::previousPlug() const
{
	return m_firstPlugIndex ? getChild<ValuePlug>( m_firstPlugIndex + 1 ) : nullptr;
}

IntPlug *Loop::iterationsPlug()
{
	return m_firstPlugIndex ? getChild<IntPlug>( m_firstPlugIndex + 2 ) : nullptr;
}

const IntPlug *Loop::iterationsPlug() const
{
	return m_firstPlugIndex ? getChild<IntPlug>( m_firstPlugIndex + 2 ) : nullptr;
}

StringPlug *Loop::indexVariablePlug()
{
	return m_firstPlugIndex ? getChild<StringPlug>( m_firstPlugIndex + 3 ) : nullptr;
}

const StringPlug *Loop::indexVariablePlug() const
{
	return m_firstPlugIndex ? getChild<StringPlug>( m_firstPlugIndex + 3 ) : nullptr;
}

Gaffer::BoolPlug *Loop::enabledPlug()
{
	return m_firstPlugIndex ? getChild<BoolPlug>( m_firstPlugIndex + 4 ) : nullptr;
}

const Gaffer::BoolPlug *Loop::enabledPlug() const
{
	return m_firstPlugIndex ? getChild<BoolPlug>( m_firstPlugIndex + 4 ) : nullptr;
}

Gaffer::Plug *Loop::correspondingInput( const Gaffer::Plug *output )
{
	return output == outPlug() ? inPlug() : nullptr;
}

const Gaffer::Plug *Loop::correspondingInput( const Gaffer::Plug *output ) const
{
	return output == outPlug() ? inPlug() : nullptr;
}

std::pair<const ValuePlug *, ContextPtr> Loop::previousIteration( const ValuePlug *output ) const
{
	int index = -1;
	IECore::InternedString indexVariable;
	if( const ValuePlug *plug = sourcePlug( output, Context::current(), index, indexVariable ) )
	{
		ContextPtr context = new Context( *Context::current() );

		if( index >= 0 )
		{
			context->set( indexVariable, index );
		}
		else
		{
			context->remove( indexVariable );
		}

		return { plug, context };
	}

	return { nullptr, nullptr };
}

void Loop::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == iterationsPlug() )
	{
		addAffectedPlug( outPlug(), outputs );
	}
	else if(
		input == indexVariablePlug() ||
		input == enabledPlug()
	)
	{
		addAffectedPlug( outPlug(), outputs );
		addAffectedPlug( previousPlug(), outputs );
	}
	else if( const ValuePlug *inputValuePlug = IECore::runTimeCast<const ValuePlug>( input ) )
	{
		std::vector<IECore::InternedString> relativeName;
		const ValuePlug *ancestor = ancestorPlug( inputValuePlug, relativeName );
		if( ancestor == inPlug() || ancestor == nextPlug() )
		{
			outputs.push_back( descendantPlug( outPlug(), relativeName ) );
			outputs.push_back( descendantPlug( previousPlug(), relativeName ) );
		}
	}
}

void Loop::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	int index = -1;
	IECore::InternedString indexVariable;
	if( const ValuePlug *plug = sourcePlug( output, context, index, indexVariable ) )
	{
		Context::EditableScope tmpContext( context );
		if( index >= 0 )
		{
			tmpContext.set( indexVariable, &index );
		}
		else
		{
			tmpContext.remove( indexVariable );
		}
		h = plug->hash();
		return;
	}

	ComputeNode::hash( output, context, h );
}

void Loop::compute( ValuePlug *output, const Context *context ) const
{
	int index = -1;
	IECore::InternedString indexVariable;
	if( const ValuePlug *plug = sourcePlug( output, context, index, indexVariable ) )
	{
		Context::EditableScope tmpContext( context );
		if( index >= 0 )
		{
			tmpContext.set( indexVariable, &index );
		}
		else
		{
			tmpContext.remove( indexVariable );
		}
		output->setFrom( plug );
		return;
	}

	ComputeNode::compute( output, context );
}

void Loop::childAdded()
{
	setupPlugs();
}

bool Loop::setupPlugs()
{
	const ValuePlug *in = getChild<ValuePlug>( "in" );
	const ValuePlug *out = getChild<ValuePlug>( "out" );
	if( !in || !out )
	{
		return false;
	}

	m_childAddedConnection.disconnect();

	m_inPlugIndex = std::find( children().begin(), children().end(), in ) - children().begin();
	m_outPlugIndex = std::find( children().begin(), children().end(), out ) - children().begin();

	const size_t firstPlugIndex = children().size();
	addChild( in->createCounterpart( "next", Plug::In ) );
	addChild( out->createCounterpart( "previous", Plug::Out ) );
	addChild( new IntPlug( "iterations", Gaffer::Plug::In, 10, 0 ) );
	addChild( new StringPlug( "indexVariable", Gaffer::Plug::In, "loop:index" ) );
	addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );

	// Only assign after adding all plugs, because our plug accessors
	// use a non-zero value to indicate that all plugs are now available.
	m_firstPlugIndex = firstPlugIndex;

	// The in/out plugs might be dynamic in the case of
	// LoopComputeNode, but because we create the next/previous
	// plugs ourselves in response, they don't need to be dynamic.
	nextPlug()->setFlags( Plug::Dynamic, false );
	previousPlug()->setFlags( Plug::Dynamic, false );

	// Copy styling over from main plugs.
	/// \todo We shouldn't really need to do this, because plug colours are
	/// expected to be registered against plug type, so our plugs will get
	/// the right colour automatically (and `copyColors()` will do nothing
	/// because of the `overwrite = false` argument). We are keeping it for
	/// now to accommodate proprietary extensions which are using custom colours
	/// instead of introducing their own plug types, but some day we should
	/// just remove this entirely. Note that the same applies for the Dot,
	/// ContextProcessor, ArrayPlug and Switch nodes. See
	/// https://github.com/GafferHQ/gaffer/pull/2953 for further discussion.
	MetadataAlgo::copyColors( inPlug(), nextPlug() , /* overwrite = */ false  );
	MetadataAlgo::copyColors( inPlug(), previousPlug() , /* overwrite = */ false  );

	// Because we're a loop, our affects() implementation specifies a cycle
	// between nextPlug() and previousPlug(), so we must ask nicely for leniency
	// during dirty propagation. The cycles aren't an issue when it comes to
	// hash()/compute() because each iteration changes the context and we bottom
	// out after the specified number of iterations.
	previousPlug()->setFlags( Plug::AcceptsDependencyCycles, true );
	for( Gaffer::Plug::RecursiveIterator it( previousPlug() ); !it.done(); ++it )
	{
		(*it)->setFlags( Plug::AcceptsDependencyCycles, true );
	}

	return true;
}

void Loop::addAffectedPlug( const ValuePlug *output, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	if( output->children().size() )
	{
		for( Plug::RecursiveOutputIterator it( output ); !it.done(); ++it )
		{
			if( !(*it)->children().size() )
			{
				outputs.push_back( it->get() );
			}
		}
	}
	else
	{
		outputs.push_back( output );
	}
}

const ValuePlug *Loop::ancestorPlug( const ValuePlug *plug, std::vector<IECore::InternedString> &relativeName ) const
{
	while( plug )
	{
		const GraphComponent *plugParent = plug->parent();
		if( plugParent == this )
		{
			return plug;
		}
		else
		{
			relativeName.push_back( plug->getName() );
			plug = static_cast<const ValuePlug *>( plugParent );
		}
	}
	return nullptr;
}

const ValuePlug *Loop::descendantPlug( const ValuePlug *plug, const std::vector<IECore::InternedString> &relativeName ) const
{
	for( std::vector<IECore::InternedString>::const_reverse_iterator it = relativeName.rbegin(), eIt = relativeName.rend(); it != eIt; ++it )
	{
		plug = plug->getChild<ValuePlug>( *it );
	}
	return plug;
}

const ValuePlug *Loop::sourcePlug( const ValuePlug *output, const Context *context, int &sourceLoopIndex, IECore::InternedString &indexVariable ) const
{
	sourceLoopIndex = -1;

	ContextAlgo::GlobalScope globalScope( context, inPlug() );

	indexVariable = indexVariablePlug()->getValue();

	std::vector<IECore::InternedString> relativeName;
	const ValuePlug *ancestor = ancestorPlug( output, relativeName );

	if( ancestor == previousPlug() )
	{
		const int index = context->get<int>( indexVariable, 0 );
		if( index >= 1 && !indexVariable.string().empty() && enabledPlug()->getValue() )
		{
			sourceLoopIndex = index - 1;
			return descendantPlug( nextPlug(), relativeName );
		}
		else
		{
			return descendantPlug( inPlug(), relativeName );
		}
	}
	else if( ancestor == outPlug() )
	{
		const int iterations = iterationsPlug()->getValue();
		if( iterations > 0 && !indexVariable.string().empty() && enabledPlug()->getValue() )
		{
			sourceLoopIndex = iterations - 1;
			return descendantPlug( nextPlug(), relativeName );
		}
		else
		{
			return descendantPlug( inPlug(), relativeName );
		}
	}

	return nullptr;
}

} // namespace Gaffer
