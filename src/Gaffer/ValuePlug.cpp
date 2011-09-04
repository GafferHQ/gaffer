//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/ValuePlug.h"
#include "Gaffer/Node.h"

#include "boost/format.hpp"

using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( ValuePlug );

ValuePlug::ValuePlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags ), m_dirty( direction==Out )
{
}

ValuePlug::~ValuePlug()
{
}

bool ValuePlug::acceptsInput( ConstPlugPtr input ) const
{
	if( !Plug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return input->isInstanceOf( staticTypeId() );
	}
	return true;
}

void ValuePlug::setInput( PlugPtr input )
{
	Plug::setInput( input );
	if( input )
	{
		// cast safe because acceptsInput checks type.
		ValuePlugPtr vInput = IECore::staticPointerCast<ValuePlug>( input );
		if( vInput->getDirty() )
		{
			setDirty();
		}
		else
		{
			setFromInput();
		}
	}
	/// \todo What should we do with the value on disconnect?
}

void ValuePlug::setDirty()
{
	if( m_dirty )
	{
		return;
	}
	if( direction()==In && !getInput<Plug>() )
	{
		throw IECore::Exception( boost::str( boost::format( "Cannot set \"%s\" dirty as it's an input with no incoming connection." ) % fullName() ) );
	}
	m_dirty = true;
	NodePtr n = node();
	if( n )
	{
		n->plugDirtiedSignal()( this );
		if( direction()==In )
		{
			n->dirty( this );
		}
	}
	for( OutputContainer::const_iterator it=outputs().begin(); it!=outputs().end(); it++ )
	{
		ValuePlugPtr o = IECore::runTimeCast<ValuePlug>( *it );
		if( o )
		{
			o->setDirty();
		}
	}
}

bool ValuePlug::getDirty() const
{
	return m_dirty;
}

void ValuePlug::valueSet()
{
	m_dirty = false;
	Node *n = node();
	if( n )
	{
		// it is important that we emit the plug set signal before
		// we emit dirty signals for any dependent plugs. this is
		// because the node may wish to perform some internal setup when plugs
		// are set, and listeners on output plugs may pull to get new
		// output values as soon as the dirty signal is emitted. 
		n->plugSetSignal()( this );
		
		if( direction()==In )
		{
			n->dirty( this );
		}
	}
	for( OutputContainer::const_iterator it=outputs().begin(); it!=outputs().end(); it++ )
	{
		ValuePlugPtr o = IECore::runTimeCast<ValuePlug>( *it );
		if( o )
		{
			o->setFromInput();
		}
	}
}

void ValuePlug::computeIfDirty()
{
	if( getDirty() )
	{
		if( getInput<Plug>() )
		{
			setFromInput();
		}
		else
		{
			NodePtr n = node();
			if( !n )
			{
				throw IECore::Exception( boost::str( boost::format( "Unable to compute value for orphan Plug \"%s\"." ) % fullName() ) ); 
			}
			n->compute( this );
		}
		/// \todo we need a proper response to failure here - perhaps call setToDefault()?
		/// and do we need some kind of error status for plugs?
	}
}
