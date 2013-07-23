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

#include "Gaffer/GraphComponent.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/Behaviours/OrphanRemover.h"

using namespace Gaffer;
using namespace Gaffer::Behaviours;


OrphanRemover::OrphanRemover( StandardSetPtr set )
	:	m_set( set )
{
	set->memberAddedSignal().connect( boost::bind( &OrphanRemover::memberAdded, this, ::_1, ::_2 ) );
	set->memberRemovedSignal().connect( boost::bind( &OrphanRemover::memberRemoved, this, ::_1, ::_2 ) );
	for( size_t i = 0, e = set->size(); i < e; ++i )
	{
		GraphComponent *graphComponent = IECore::runTimeCast<GraphComponent>( set->member( i ) );
		if( graphComponent )
		{
			graphComponent->parentChangedSignal().connect( boost::bind( &OrphanRemover::parentChanged, this, ::_1, ::_2 ) );
		}
	}
}

void OrphanRemover::memberAdded( const Set *s, Set::Member *m )
{
	GraphComponent *graphComponent = IECore::runTimeCast<GraphComponent>( m );
	if( graphComponent )
	{
		graphComponent->parentChangedSignal().connect( boost::bind( &OrphanRemover::parentChanged, this, ::_1, ::_2 ) );
	}
}

void OrphanRemover::memberRemoved( const Set *s, Set::Member *m )
{
	GraphComponent *graphComponent = IECore::runTimeCast<GraphComponent>( m );
	if( graphComponent )
	{
		graphComponent->parentChangedSignal().disconnect( boost::bind( &OrphanRemover::parentChanged, this, ::_1, ::_2 ) );
	}
}

void OrphanRemover::parentChanged( GraphComponent *member, const GraphComponent *oldParent )
{
	if( !member->parent<GraphComponent>() )
	{
		// the node has been deleted - remove it from the selection
		m_set->remove( member );
	}
}
