//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "tbb/enumerable_thread_specific.h"

#include "boost/multi_index_container.hpp"
#include "boost/multi_index/random_access_index.hpp"
#include "boost/multi_index/ordered_index.hpp"

#include "Gaffer/DependencyNode.h"
#include "Gaffer/ValuePlug.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/StandardSet.h"

using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( DependencyNode );

DependencyNode::DependencyNode( const std::string &name )
	:	Node( name )
{
}

DependencyNode::~DependencyNode()
{
}
		
void DependencyNode::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	if( input->isInstanceOf( CompoundPlug::staticTypeId() ) )
	{
		throw IECore::Exception( "DependencyNode::affects() called with non-leaf plug " + input->fullName() );
	}
}


BoolPlug *DependencyNode::enabledPlug()
{
	return 0;
}

const BoolPlug *DependencyNode::enabledPlug() const
{
	return 0;
}

Plug *DependencyNode::correspondingInput( const Plug *output )
{
	return 0;
}

const Plug *DependencyNode::correspondingInput( const Plug *output ) const
{
	return 0;
}

//////////////////////////////////////////////////////////////////////////
// Dirty propagation
//////////////////////////////////////////////////////////////////////////

typedef boost::multi_index::multi_index_container<
	Plug *,
	boost::multi_index::indexed_by<
		boost::multi_index::ordered_unique<boost::multi_index::identity<Plug *> >,
		boost::multi_index::random_access<>
	>
> DirtyPlugsContainer;

static tbb::enumerable_thread_specific<DirtyPlugsContainer> g_dirtyPlugsContainers;
		
void DependencyNode::propagateDirtiness( Plug *plugToDirty )
{
	// we're not able to signal anything if there's no node, so just early out
	Node *node = plugToDirty->ancestor<Node>();
	if( !node )
	{
		return;
	}
	
	// we don't emit dirtiness immediately for each plug as we traverse the
	// dependency graph for two reasons :
	//
	// - we don't want to emit dirtiness for the same plug more than once
	// - we don't want to emit dirtiness while the graph may still be being
	//   rewired by slots connected to plugSetSignal() or plugInputChangedSignal()
	//
	// instead we collect all the dirty plugs in a container as we traverse
	// the graph and only when the traversal is complete do we emit the plugDirtiedSignal().
	//
	// the container used is stored per-thread as although it's illegal to be
	// monkeying with a script from multiple threads, it's perfectly legal to
	// be monkeying with a different script in each thread.
	
	DirtyPlugsContainer &dirtyPlugs = g_dirtyPlugsContainers.local();
	
	// if the container is currently empty then we are at the start of a traversal,
	// and will emit plugDirtiedSignal() and empty the container before returning
	// from this function. if the container isn't empty then we are mid-traversal
	// and will just add to it.
	const bool emit = dirtyPlugs.empty();

	Plug *p = plugToDirty;
	while( p )
	{
		dirtyPlugs.insert( p );
		p = p->parent<Plug>();
	}	
	
	// we only propagate dirtiness along leaf level plugs, because
	// they are the only plugs which can be the target of the affects(),
	// and compute() methods.
	if( !plugToDirty->isInstanceOf( (IECore::TypeId)CompoundPlugTypeId ) )
	{
		DependencyNode *dependencyNode = IECore::runTimeCast<DependencyNode>( node );
		if( dependencyNode )
		{
			AffectedPlugsContainer affected;
			dependencyNode->affects( plugToDirty, affected );
			for( AffectedPlugsContainer::const_iterator it=affected.begin(); it!=affected.end(); it++ )
			{
				if( ( *it )->isInstanceOf( (IECore::TypeId)Gaffer::CompoundPlugTypeId ) )
				{
					// DependencyNode::affects() implementations are only allowed to place leaf plugs in the outputs,
					// so we helpfully report any mistakes.
					dirtyPlugs.clear();
					throw IECore::Exception( "Non-leaf plug " + (*it)->fullName() + " cannot be returned by affects()" );
				}
				// cast is ok - AffectedPlugsContainer only holds const pointers so that
				// affects() can be const to discourage implementations from having side effects.
				propagateDirtiness( const_cast<Plug *>( *it ) );
			}
		}
	
		for( Plug::OutputContainer::const_iterator it=plugToDirty->outputs().begin(), eIt=plugToDirty->outputs().end(); it!=eIt; ++it )
		{
			propagateDirtiness( *it );
		}		
	}
	
	if( emit )
	{
		for( size_t i = 0, e = dirtyPlugs.size(); i < e; ++i )
		{
			Plug *plug = dirtyPlugs.get<1>()[i];
			Node *node = plug->node();
			if( node )
			{
				node->plugDirtiedSignal()( plug );
			}
		}
		dirtyPlugs.clear();
	}
}
