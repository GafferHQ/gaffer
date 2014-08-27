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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "Gaffer/ArrayPlug.h"

using namespace Gaffer;
using namespace boost;

IE_CORE_DEFINERUNTIMETYPED( ArrayPlug )

ArrayPlug::ArrayPlug( const std::string &name, Direction direction, PlugPtr element, size_t minSize, size_t maxSize, unsigned flags )
	:	CompoundPlug( name, direction, flags ), m_minSize( minSize ), m_maxSize( maxSize )
{
	if( direction == Plug::Out )
	{
		throw IECore::Exception( "Output ArrayPlugs are currently unsupported." );
	}

	if( element )
	{
		// If we're dynamic ourselves, then serialisations will include a constructor
		// for us, but it will have element==None. In this case we make sure the first
		// element is dynamic, so that it too will have a constructor written out (and then
		// we'll capture it in childAdded()). But if we're not dynamic, we expect to be
		// passed the element again upon reconstruction, so we don't need a constructor
		// to be serialised for the element, and therefore we must set it to be non-dynamic.
		element->setFlags( Gaffer::Plug::Dynamic, getFlags( Gaffer::Plug::Dynamic ) );
		addChild( element );
	}
	else
	{
		childAddedSignal().connect( boost::bind( &ArrayPlug::childAdded, this ) );
	}
	parentChangedSignal().connect( boost::bind( &ArrayPlug::parentChanged, this ) );
}

ArrayPlug::~ArrayPlug()
{
}

bool ArrayPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !CompoundPlug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	return children().size() == 0 || potentialChild->typeId() == children()[0]->typeId();
}

PlugPtr ArrayPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	ArrayPlugPtr result = new ArrayPlug( name, direction, NULL, m_minSize, m_maxSize, getFlags() );
	for( PlugIterator it( this ); it != it.end(); it++ )
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

void ArrayPlug::childAdded()
{
	assert( children().size() == 1 );
	childAddedSignal().disconnect( boost::bind( &ArrayPlug::childAdded, this ) );
	if( node() )
	{
		// this code path is triggered when loading a dynamic ArrayPlug from a script,
		// and the first child is just being added. unfortunately the InputGenerator
		// constructor will generate m_minSize extra inputs when we construct it, even
		// though the rest of the necessary inputs are about to be loaded from the script.
		// here we avoid that in the simple minSize==maxSize case (where we don't need
		// an InputGenerator anyway). to avoid it in the general case would be a little
		// trickier and isn't yet necessary for our use cases. fixing the problem would
		// probably be cleaner without using an InputGenerator, so perhaps it could be
		// addressed if and when we replace all InputGenerator use with ArrayPlugs.
		if( m_minSize != m_maxSize )
		{
			m_inputGenerator = InputGeneratorPtr( new InputGenerator( this, boost::static_pointer_cast<Plug>( children()[0] ), m_minSize, m_maxSize ) );
		}
	}
}

void ArrayPlug::parentChanged()
{
	if( node() && !m_inputGenerator && children().size() )
	{
		m_inputGenerator = InputGeneratorPtr( new InputGenerator( this, boost::static_pointer_cast<Plug>( children()[0] ), m_minSize, m_maxSize ) );
	}
	parentChangedSignal().disconnect( boost::bind( &ArrayPlug::parentChanged, this ) );
}
