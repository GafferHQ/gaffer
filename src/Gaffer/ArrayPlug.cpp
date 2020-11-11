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

#include "Gaffer/BlockedConnection.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace boost;
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

ArrayPlug::ArrayPlug( const std::string &name, Direction direction, PlugPtr element, size_t minSize, size_t maxSize, unsigned flags, bool resizeWhenInputsChange )
	:	Plug( name, direction, flags ), m_minSize( std::max( minSize, size_t( 1 ) ) ), m_maxSize( std::max( maxSize, m_minSize ) ), m_resizeWhenInputsChange( resizeWhenInputsChange )
{
	if( element )
	{
		// If we're dynamic ourselves, then serialisations will include a constructor
		// for us, but it will have element==None. In this case we make sure the first
		// element is dynamic, so that it too will have a constructor written out. But
		// if we're not dynamic, we expect to be passed the element again upon reconstruction,
		// so we don't need a constructor to be serialised for the element, and therefore
		// we must set it to be non-dynamic.
		element->setFlags( Gaffer::Plug::Dynamic, getFlags( Gaffer::Plug::Dynamic ) );
		addChild( element );

		for( size_t i = 1; i < m_minSize; ++i )
		{
			PlugPtr p = element->createCounterpart( element->getName(), Plug::In );
			addChild( p );
			MetadataAlgo::copyColors( element.get() , p.get() , /* overwrite = */ false  );
		}
	}
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

	return children().size() == 0 || potentialChild->typeId() == children()[0]->typeId();
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
	BlockedConnection blockedConnection( m_inputChangedConnection );
	Plug::setInput( input );
}

PlugPtr ArrayPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	ArrayPlugPtr result = new ArrayPlug( name, direction, nullptr, m_minSize, m_maxSize, getFlags(), resizeWhenInputsChange() );
	for( Plug::Iterator it( this ); !it.done(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
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
		throw IECore::Exception( "Invalid size" );
	}

	while( size > children().size() )
	{
		PlugPtr p = getChild<Plug>( 0 )->createCounterpart( getChild<Plug>( 0 )->getName(), Plug::In );
		p->setFlags( Gaffer::Plug::Dynamic, true );
		addChild( p );
		MetadataAlgo::copyColors( getChild<Plug>( 0 ) , p.get() , /* overwrite = */ false );
	}

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
	Plug *last = static_cast<Plug *>( children().back().get() );
	if( !hasInput( last ) )
	{
		return last;
	}

	if( children().size() >= m_maxSize )
	{
		return nullptr;
	}

	PlugPtr p = getChild<Plug>( 0 )->createCounterpart( getChild<Plug>( 0 )->getName(), Plug::In );
	p->setFlags( Gaffer::Plug::Dynamic, true );
	addChild( p );
	MetadataAlgo::copyColors( getChild<Plug>( 0 ) , p.get() , /* overwrite = */ false );
	return p.get();
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
