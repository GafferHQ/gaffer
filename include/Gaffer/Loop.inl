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

#include "boost/bind.hpp"

#include "Gaffer/Loop.h"

namespace Gaffer
{

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<Loop<BaseType> > Loop<BaseType>::g_typeDescription;

template<typename BaseType>
Loop<BaseType>::Loop( const std::string &name )
	:	BaseType( name ), m_inPlugIndex( 0 ), m_outPlugIndex( 0 ), m_firstPlugIndex( 0 )
{
	if( !setupPlugs() )
	{
		// Our base class didn't provide the plugs we expect. Connect to
		// childAddedSignal() so we can set ourselves up later when the
		// appropriate plugs are added manually - this lets the LoopComputeNode
		// be used with any sort of plug.
		BaseType::childAddedSignal().connect( boost::bind( &Loop::childAdded, this ) );
	}
}

template<typename BaseType>
Loop<BaseType>::~Loop()
{
}

template<typename BaseType>
ValuePlug *Loop<BaseType>::nextPlug()
{
	return m_firstPlugIndex ? BaseType::template getChild<ValuePlug>( m_firstPlugIndex ) : NULL;
}

template<typename BaseType>
const ValuePlug *Loop<BaseType>::nextPlug() const
{
	return m_firstPlugIndex ? BaseType::template getChild<ValuePlug>( m_firstPlugIndex ) : NULL;
}

template<typename BaseType>
ValuePlug *Loop<BaseType>::previousPlug()
{
	return m_firstPlugIndex ? BaseType::template getChild<ValuePlug>( m_firstPlugIndex + 1 ) : NULL;
}

template<typename BaseType>
const ValuePlug *Loop<BaseType>::previousPlug() const
{
	return m_firstPlugIndex ? BaseType::template getChild<ValuePlug>( m_firstPlugIndex + 1 ) : NULL;
}

template<typename BaseType>
IntPlug *Loop<BaseType>::iterationsPlug()
{
	return m_firstPlugIndex ? BaseType::template getChild<IntPlug>( m_firstPlugIndex + 2 ) : NULL;
}

template<typename BaseType>
const IntPlug *Loop<BaseType>::iterationsPlug() const
{
	return m_firstPlugIndex ? BaseType::template getChild<IntPlug>( m_firstPlugIndex + 2 ) : NULL;
}

template<typename BaseType>
StringPlug *Loop<BaseType>::indexVariablePlug()
{
	return m_firstPlugIndex ? BaseType::template getChild<StringPlug>( m_firstPlugIndex + 3 ) : NULL;
}

template<typename BaseType>
const StringPlug *Loop<BaseType>::indexVariablePlug() const
{
	return m_firstPlugIndex ? BaseType::template getChild<StringPlug>( m_firstPlugIndex + 3 ) : NULL;
}

template<typename BaseType>
Gaffer::BoolPlug *Loop<BaseType>::enabledPlug()
{
	if( BoolPlug *p = BaseType::enabledPlug() )
	{
		return p;
	}
	return m_firstPlugIndex ? BaseType::template getChild<BoolPlug>( m_firstPlugIndex + 4 ) : NULL;
}

template<typename BaseType>
const Gaffer::BoolPlug *Loop<BaseType>::enabledPlug() const
{
	if( const BoolPlug *p = BaseType::enabledPlug() )
	{
		return p;
	}
	return m_firstPlugIndex ? BaseType::template getChild<BoolPlug>( m_firstPlugIndex + 4 ) : NULL;
}

template<typename BaseType>
Gaffer::Plug *Loop<BaseType>::correspondingInput( const Gaffer::Plug *output )
{
	if( Plug *p = BaseType::correspondingInput( output ) )
	{
		return p;
	}
	return output == outPlugInternal() ? inPlugInternal() : NULL;
}

template<typename BaseType>
const Gaffer::Plug *Loop<BaseType>::correspondingInput( const Gaffer::Plug *output ) const
{
	if( const Plug *p = BaseType::correspondingInput( output ) )
	{
		return p;
	}
	return output == outPlugInternal() ? inPlugInternal() : NULL;
}

template<typename BaseType>
void Loop<BaseType>::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	BaseType::affects( input, outputs );

	if( input == iterationsPlug() )
	{
		addAffectedPlug( outPlugInternal(), outputs );
	}
	else if(
		input == indexVariablePlug() ||
		input == enabledPlug()
	)
	{
		addAffectedPlug( outPlugInternal(), outputs );
		addAffectedPlug( previousPlug(), outputs );
	}
	else if( const ValuePlug *inputValuePlug = IECore::runTimeCast<const ValuePlug>( input ) )
	{
		std::vector<IECore::InternedString> relativeName;
		const ValuePlug *ancestor = ancestorPlug( inputValuePlug, relativeName );
		if( ancestor == inPlugInternal() || ancestor == nextPlug() )
		{
			outputs.push_back( descendantPlug( outPlugInternal(), relativeName ) );
			outputs.push_back( descendantPlug( previousPlug(), relativeName ) );
		}
	}
}

template<typename BaseType>
void Loop<BaseType>::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	int index = -1;
	IECore::InternedString indexVariable;
	if( const ValuePlug *plug = sourcePlug( output, context, index, indexVariable ) )
	{
		if( index >= 0 )
		{
			ContextPtr tmpContext = new Context( *context, Context::Borrowed );
			tmpContext->set<int>( indexVariable, index );
			Context::Scope scopedContext( tmpContext.get() );
			h = plug->hash();
		}
		else
		{
			h = plug->hash();
		}
		return;
	}

	BaseType::hash( output, context, h );
}

template<typename BaseType>
void Loop<BaseType>::compute( ValuePlug *output, const Context *context ) const
{
	int index = -1;
	IECore::InternedString indexVariable;
	if( const ValuePlug *plug = sourcePlug( output, context, index, indexVariable ) )
	{
		if( index >= 0 )
		{
			ContextPtr tmpContext = new Context( *context, Context::Borrowed );
			tmpContext->set<int>( indexVariable, index );
			Context::Scope scopedContext( tmpContext.get() );
			output->setFrom( plug );
		}
		else
		{
			output->setFrom( plug );
		}
		return;
	}

	BaseType::compute( output, context );
}

template<typename BaseType>
void Loop<BaseType>::childAdded()
{
	setupPlugs();
}

template<typename BaseType>
bool Loop<BaseType>::setupPlugs()
{
	const ValuePlug *in = BaseType::template getChild<ValuePlug>( "in" );
	const ValuePlug *out = BaseType::template getChild<ValuePlug>( "out" );
	if( !in || !out )
	{
		return false;
	}

	BaseType::childAddedSignal().disconnect( boost::bind( &Loop::childAdded, this ) );

	m_inPlugIndex = std::find( BaseType::children().begin(), BaseType::children().end(), in ) - BaseType::children().begin();
	m_outPlugIndex = std::find( BaseType::children().begin(), BaseType::children().end(), out ) - BaseType::children().begin();

	const size_t firstPlugIndex = BaseType::children().size();
	BaseType::addChild( in->createCounterpart( "next", Plug::In ) );
	BaseType::addChild( out->createCounterpart( "previous", Plug::Out ) );
	BaseType::addChild( new IntPlug( "iterations", Gaffer::Plug::In, 10, 0 ) );
	BaseType::addChild( new StringPlug( "indexVariable", Gaffer::Plug::In, "loop:index" ) );

	if( !BaseType::enabledPlug() )
	{
		BaseType::addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );
	}

	// Only assign after adding all plugs, because our plug accessors
	// use a non-zero value to indicate that all plugs are now available.
	m_firstPlugIndex = firstPlugIndex;

	// The in/out plugs might be dynamic in the case of
	// LoopComputeNode, but because we create the next/previous
	// plugs ourselves in response, they don't need to be dynamic.
	nextPlug()->setFlags( Plug::Dynamic, false );
	previousPlug()->setFlags( Plug::Dynamic, false );

	// Because we're a loop, our affects() implementation specifies a cycle
	// between nextPlug() and previousPlug(), so we must ask nicely for leniency
	// during dirty propagation. The cycles aren't an issue when it comes to
	// hash()/compute() because each iteration changes the context and we bottom
	// out after the specified number of iterations.
	previousPlug()->setFlags( Plug::AcceptsDependencyCycles, true );
	for( Gaffer::RecursivePlugIterator it( previousPlug() ); !it.done(); ++it )
	{
		(*it)->setFlags( Plug::AcceptsDependencyCycles, true );
	}

	return true;
}

template<typename BaseType>
ValuePlug *Loop<BaseType>::inPlugInternal()
{
	return m_inPlugIndex ? BaseType::template getChild<ValuePlug>( m_inPlugIndex ) : NULL;
}

template<typename BaseType>
const ValuePlug *Loop<BaseType>::inPlugInternal() const
{
	return m_inPlugIndex ? BaseType::template getChild<ValuePlug>( m_inPlugIndex ) : NULL;
}

template<typename BaseType>
ValuePlug *Loop<BaseType>::outPlugInternal()
{
	return m_outPlugIndex ? BaseType::template getChild<ValuePlug>( m_outPlugIndex ) : NULL;
}

template<typename BaseType>
const ValuePlug *Loop<BaseType>::outPlugInternal() const
{
	return m_outPlugIndex ? BaseType::template getChild<ValuePlug>( m_outPlugIndex ) : NULL;
}

template<typename BaseType>
void Loop<BaseType>::addAffectedPlug( const ValuePlug *output, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	if( output->children().size() )
	{
		for( RecursiveOutputPlugIterator it( output ); !it.done(); ++it )
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

template<typename BaseType>
const ValuePlug *Loop<BaseType>::ancestorPlug( const ValuePlug *plug, std::vector<IECore::InternedString> &relativeName ) const
{
	while( plug )
	{
		const GraphComponent *plugParent = plug->parent<GraphComponent>();
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
	return NULL;
}

template<typename BaseType>
const ValuePlug *Loop<BaseType>::descendantPlug( const ValuePlug *plug, const std::vector<IECore::InternedString> &relativeName ) const
{
	for( std::vector<IECore::InternedString>::const_reverse_iterator it = relativeName.rbegin(), eIt = relativeName.rend(); it != eIt; ++it )
	{
		plug = plug->getChild<ValuePlug>( *it );
	}
	return plug;
}

template<typename BaseType>
const ValuePlug *Loop<BaseType>::sourcePlug( const ValuePlug *output, const Context *context, int &sourceLoopIndex, IECore::InternedString &indexVariable ) const
{
	sourceLoopIndex = -1;

	indexVariable = indexVariablePlug()->getValue();

	std::vector<IECore::InternedString> relativeName;
	const ValuePlug *ancestor = ancestorPlug( output, relativeName );

	if( ancestor == previousPlug() )
	{
		const int index = context->get<int>( indexVariable, 0 );
		if( index >= 1 && enabledPlug()->getValue() )
		{
			sourceLoopIndex = index - 1;
			return descendantPlug( nextPlug(), relativeName );
		}
		else
		{
			return descendantPlug( inPlugInternal(), relativeName );
		}
	}
	else if( ancestor == outPlugInternal() )
	{
		const int iterations = iterationsPlug()->getValue();
		if( iterations > 0 && enabledPlug()->getValue() )
		{
			sourceLoopIndex = iterations - 1;
			return descendantPlug( nextPlug(), relativeName );
		}
		else
		{
			return descendantPlug( inPlugInternal(), relativeName );
		}
	}

	return NULL;
}

} // namespace Gaffer
