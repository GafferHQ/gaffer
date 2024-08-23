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

#include "Gaffer/ArrayPlug.h"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace boost;
using namespace boost::placeholders;
using namespace Gaffer;

namespace
{

bool hasInput( const Plug *p )
{
	if( p->getInput() )
	{
		return true;
	}
	for( Plug::Iterator it( p ); !it.done(); ++it )
	{
		if( hasInput( it->get() ) )
		{
			return true;
		}
	}
	return false;
}

} // namespace

GAFFER_PLUG_DEFINE_TYPE( ArrayPlug )

ArrayPlug::ArrayPlug( const std::string &name, Direction direction, ConstPlugPtr elementPrototype, size_t minSize, size_t maxSize, unsigned flags, bool resizeWhenInputsChange )
	:	Plug( name, direction, flags ), m_elementPrototype( elementPrototype ), m_minSize( minSize ), m_maxSize( std::max( maxSize, m_minSize ) ), m_resizeWhenInputsChange( resizeWhenInputsChange )
{
	if( !m_elementPrototype )
	{
		// We're being constructed during execution of a legacy serialisation
		// (nobody else is allowed to pass a null `elementPrototype`). Arrange
		// to recover our protoype when the first element is added.
		childAddedSignal().connect( boost::bind( &ArrayPlug::childAdded, this ) );
		return;
	}

	resize( m_minSize );
}

ArrayPlug::~ArrayPlug()
{
}

bool ArrayPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !Plug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	if( !m_elementPrototype )
	{
		// Special case to support loading of legacy serialisations. We accept
		// the first child we are given and then in `childAdded()` we initialise
		// `m_elementPrototype` from it.
		assert( children().size() == 0 );
		return true;
	}

	return potentialChild->typeId() == m_elementPrototype->typeId();
}

bool ArrayPlug::acceptsInput( const Plug *input ) const
{
	if( !Plug::acceptsInput( input ) )
	{
		return false;
	}
	return !input || IECore::runTimeCast<const ArrayPlug>( input );
}

void ArrayPlug::setInput( PlugPtr input )
{
	// Plug::setInput() will be managing the inputs of our children,
	// and we don't want to be fighting with it in inputChanged(), so
	// we disable our connection while it does its work.
	Signals::BlockedConnection blockedConnection( m_inputChangedConnection );
	Plug::setInput( input );
}

PlugPtr ArrayPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	ArrayPlugPtr result = new ArrayPlug( name, direction, m_elementPrototype, m_minSize, m_maxSize, getFlags(), resizeWhenInputsChange() );
	if( m_elementPrototype )
	{
		result->resize( children().size() );
	}
	return result;
}

const Plug *ArrayPlug::elementPrototype() const
{
	return m_elementPrototype.get();
}

size_t ArrayPlug::minSize() const
{
	return m_minSize;
}

size_t ArrayPlug::maxSize() const
{
	return m_maxSize;
}

void ArrayPlug::resize( size_t size )
{
	if( size > m_maxSize || size < m_minSize )
	{
		throw IECore::Exception(
			fmt::format(
				"Invalid size {} requested for `{}` (minSize={}, maxSize={})",
				size, fullName(), m_minSize, m_maxSize
			)
		);
	}

	if( !m_elementPrototype )
	{
		throw IECore::Exception(
			fmt::format(
				"ArrayPlug `{}` was constructed without the required `elementPrototype`",
				fullName()
			)
		);
	}

	while( size > children().size() )
	{
		PlugPtr p = m_elementPrototype->createCounterpart( m_elementPrototype->getName(), direction() );
		addChild( p );
		MetadataAlgo::copyColors( m_elementPrototype.get(), p.get() , /* overwrite = */ false );
	}

	Gaffer::Signals::BlockedConnection blockedInputChange( m_inputChangedConnection );
	while( children().size() > size )
	{
		removeChild( children().back() );
	}
}

bool ArrayPlug::resizeWhenInputsChange() const
{
	return m_resizeWhenInputsChange;
}

Gaffer::Plug *ArrayPlug::next()
{
	if( children().size() )
	{
		Plug *last = static_cast<Plug *>( children().back().get() );
		if( !hasInput( last ) )
		{
			return last;
		}
	}

	if( children().size() >= m_maxSize )
	{
		return nullptr;
	}

	resize( children().size() + 1 );
	return static_cast<Plug *>( children().back().get() );
}

void ArrayPlug::parentChanged( GraphComponent *oldParent )
{
	Plug::parentChanged( oldParent );

	if( !m_resizeWhenInputsChange || !node() )
	{
		return;
	}

	m_inputChangedConnection = node()->plugInputChangedSignal().connect( boost::bind( &ArrayPlug::inputChanged, this, ::_1 ) );
}

void ArrayPlug::inputChanged( Gaffer::Plug *plug )
{
	if( !this->isAncestorOf( plug ) )
	{
		return;
	}

	if( getInput() )
	{
		// When we ourselves have an input, we don't do any automatic addition or
		// removal of children, because the Plug base class itself manages
		// children to maintain the connection.
		return;
	}

	if( const ScriptNode *script = ancestor<ScriptNode>() )
	{
		if(
			script->currentActionStage() == Action::Undo ||
			script->currentActionStage() == Action::Redo
		)
		{
			// If we're currently in an undo or redo, we don't
			// need to do anything, because our previous actions
			// will be in the undo queue and will be being replayed
			// for us automatically.
			return;
		}
	}

	if( plug->getInput() )
	{
		// Connection made. If it's the last plug
		// then we need to add one more.
		if( plug == children().back() || children().back()->isAncestorOf( plug ) )
		{
			next();
		}
	}
	else
	{
		// Connection broken. We need to remove any
		// unneeded unconnected plugs so that we have
		// only one unconnected plug at the end.
		for( size_t i = children().size() - 1; i > m_minSize - 1; --i )
		{
			if( !hasInput( getChild<Plug>( i ) ) && !hasInput( getChild<Plug>( i - 1 ) ) )
			{
				removeChild( getChild<Plug>( i ) );
			}
			else
			{
				break;
			}
		}
	}
}

void ArrayPlug::childAdded()
{
	if( !m_elementPrototype )
	{
		// First child being added from a legacy serialisation. Initialise prototype.
		const Plug *firstElement = getChild<Plug>( 0 );
		m_elementPrototype = firstElement->createCounterpart( firstElement->getName(), firstElement->direction() );
	}
}
