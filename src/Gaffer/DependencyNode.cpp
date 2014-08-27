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

#include "boost/graph/adjacency_list.hpp"
#include "boost/graph/topological_sort.hpp"

#include "boost/multi_index_container.hpp"
#include "boost/multi_index/sequenced_index.hpp"
#include "boost/multi_index/ordered_index.hpp"

#include "Gaffer/DependencyNode.h"
#include "Gaffer/ValuePlug.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/StandardSet.h"

using namespace boost;
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

namespace
{

// We don't emit dirtiness immediately for each plug as we traverse the
// dependency graph for two reasons :
//
// - we don't want to emit dirtiness for the same plug more than once
// - we don't want to emit dirtiness while the graph may still be being
//   rewired by slots connected to plugSetSignal() or plugInputChangedSignal()
//
// Instead we collect all the dirty plugs in this container as we traverse
// the graph and only when the traversal is complete do we emit the plugDirtiedSignal().
//
// The container used is stored per-thread as although it's illegal to be
// monkeying with a script from multiple threads, it's perfectly legal to
// be monkeying with a different script in each thread.
class DirtyPlugs
{

	public :

		void insert( Plug *plugToDirty )
		{
			insertInternal( plugToDirty );
		}

		void emit()
		{
			std::vector<VertexDescriptor> sorted;
			topological_sort( m_graph, std::back_inserter( sorted ) );
			for( std::vector<VertexDescriptor>::const_reverse_iterator it = sorted.rbegin(), eIt = sorted.rend(); it != eIt; ++it )
			{
				Plug *plug = m_graph[*it];
				Node *node = plug->node();
				if( node )
				{
					node->plugDirtiedSignal()( plug );
				}
			}
		}

		void clear()
		{
			m_graph.clear();
			m_plugs.clear();
		}

		bool empty() const
		{
			return m_plugs.empty();
		}

	private :

		// We use this graph structure to keep track of the dirty propagation.
		// Vertices in the graph represent plugs which have been dirtied, and
		// edges represent the relationships that caused the dirtying - an
		// edge from U to V indicates that V was dirtied by U. We do a topological
		// sort on the graph to give us an appropriate order to emit the dirty
		// signals in, so that dirtiness is only signalled for an affected plug
		// after it has been signalled for all upstream dirty plugs.
		typedef boost::adjacency_list<vecS, vecS, directedS, Plug *> Graph;
		typedef Graph::vertex_descriptor VertexDescriptor;

		typedef std::map<const Plug *, VertexDescriptor> PlugMap;

		// Inserts a vertex representing plugToDirty into the graph, and
		// then inserts all affected plugs. Note that we visit affected
		// plugs for plugToDirty in the reverse order to which we wish to
		// emit signals - this is because boost::topological_sort() outputs
		// vertices in reverse order.
		VertexDescriptor insertInternal( Plug *plugToDirty )
		{
			// If we've inserted this one before, then early out. There's
			// no point repeating the propagation all over again, and our
			// Graph isn't designed to have duplicate edges anyway.
			PlugMap::const_iterator it = m_plugs.find( plugToDirty );
			if( it != m_plugs.end() )
			{
				return it->second;
			}

			// Insert a vertex for this plug.
			VertexDescriptor result = add_vertex( m_graph );
			m_graph[result] = plugToDirty;
			m_plugs[plugToDirty] = result;

			// Propagate dirtiness to output plugs and affected plugs.
			// We only propagate dirtiness along leaf level plugs, because
			// they are the only plugs which can be the target of the affects(),
			// and compute() methods.
			if( !plugToDirty->isInstanceOf( (IECore::TypeId)CompoundPlugTypeId ) )
			{
				for( Plug::OutputContainer::const_reverse_iterator it=plugToDirty->outputs().rbegin(), eIt=plugToDirty->outputs().rend(); it!=eIt; ++it )
				{
					VertexDescriptor outputVertex = insertInternal( const_cast<Plug *>( *it ) );
					add_edge( result, outputVertex, m_graph );
				}

				const DependencyNode *dependencyNode = plugToDirty->ancestor<DependencyNode>();
				if( dependencyNode )
				{
					DependencyNode::AffectedPlugsContainer affected;
					dependencyNode->affects( plugToDirty, affected );
					for( DependencyNode::AffectedPlugsContainer::const_reverse_iterator it=affected.rbegin(); it!=affected.rend(); it++ )
					{
						if( ( *it )->isInstanceOf( (IECore::TypeId)Gaffer::CompoundPlugTypeId ) )
						{
							// DependencyNode::affects() implementations are only allowed to place leaf plugs in the outputs,
							// so we helpfully report any mistakes.
							clear();
							throw IECore::Exception( "Non-leaf plug " + (*it)->fullName() + " cannot be returned by affects()" );
						}
						// cast is ok - AffectedPlugsContainer only holds const pointers so that
						// affects() can be const to discourage implementations from having side effects.
						VertexDescriptor affectedVertex = insertInternal( const_cast<Plug *>( *it ) );
						add_edge( result, affectedVertex, m_graph );
					}
				}
			}

			// Insert all ancestor plugs.
			Plug *child = plugToDirty;
			VertexDescriptor childVertex = result;
			while( Plug *parent = child->parent<Plug>() )
			{
				VertexDescriptor parentVertex = insertInternal( parent );
				add_edge( childVertex, parentVertex, m_graph );

				child = parent;
				childVertex = parentVertex;
			}

			return result;
		}

		Graph m_graph;
		PlugMap m_plugs;

};

} // namespace

static tbb::enumerable_thread_specific<DirtyPlugs> g_dirtyPlugs;

void DependencyNode::propagateDirtiness( Plug *plugToDirty )
{
	DirtyPlugs &dirtyPlugs = g_dirtyPlugs.local();

	// If the container is currently empty then we are at the start of a traversal,
	// and will emit plugDirtiedSignal() and empty the container before returning
	// from this function. If the container isn't empty then we are mid-traversal
	// and will just add to it.
	const bool emit = dirtyPlugs.empty();
	dirtyPlugs.insert( plugToDirty );
	if( emit )
	{
		dirtyPlugs.emit();
		dirtyPlugs.clear();
	}
}
