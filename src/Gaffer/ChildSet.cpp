//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#include "Gaffer/ChildSet.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace boost::placeholders;
using namespace Gaffer;

ChildSet::ChildSet( GraphComponentPtr parent )
	:	m_parent( parent )
{
	parent->childAddedSignal().connect( boost::bind( &ChildSet::childAdded, this, ::_1,  ::_2 ) );
	parent->childRemovedSignal().connect( boost::bind( &ChildSet::childRemoved, this, ::_1,  ::_2 ) );
}

ChildSet::~ChildSet()
{
}

bool ChildSet::contains( const Member *object ) const
{
	const GraphComponent *g = IECore::runTimeCast<const GraphComponent>( object );
	if( g )
	{
		return g->parent() == m_parent;
	}
	return false;
}

Set::Member *ChildSet::member( size_t index )
{
	return const_cast<GraphComponent *>( m_parent->getChild( index ) );
}

const Set::Member *ChildSet::member( size_t index ) const
{
	return m_parent->getChild( index );
}

size_t ChildSet::size() const
{
	return m_parent->children().size();
}

void ChildSet::childAdded( GraphComponent *parent, GraphComponent *child )
{
	memberAddedSignal()( this, child );
}

void ChildSet::childRemoved( GraphComponent *parent, GraphComponent *child )
{
	memberRemovedSignal()( this, child );
}
