//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Plug.h"

#include "Gaffer/Action.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/DownstreamIterator.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"

#include "IECore/Exception.h"

#include "boost/bind.hpp"
#include "boost/format.hpp"
#include "boost/graph/adjacency_list.hpp"
#include "boost/graph/depth_first_search.hpp"
#include "boost/unordered_map.hpp"

#include "tbb/enumerable_thread_specific.h"

using namespace boost;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// Assigns a value to something, reassigning the original
/// value when it goes out of scope.
template<typename T>
class ScopedAssignment : boost::noncopyable
{
	public :

		ScopedAssignment( T &target, const T &value )
			:	m_target( target ), m_originalValue( target )
		{
			m_target = value;
		}

		~ScopedAssignment()
		{
			m_target = m_originalValue;
		}

	private :

		T &m_target;
		T m_originalValue;

};

bool allDescendantInputsAreNull( const Plug *plug )
{
	for( RecursivePlugIterator it( plug ); !it.done(); ++it )
	{
		if( (*it)->getInput() )
		{
			return false;
		}
	}
	return true;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Plug implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Plug );

Plug::Plug( const std::string &name, Direction direction, unsigned flags )
	:	GraphComponent( name ), m_direction( direction ), m_input( nullptr ), m_flags( None ), m_skipNextUpdateInputFromChildInputs( false )
{
	setFlags( flags );
}

Plug::~Plug()
{
	setInputInternal( nullptr, false );
	for( OutputContainer::iterator it=m_outputs.begin(); it!=m_outputs.end(); )
	{
	 	// get the next iterator now, as the call to setInputInternal invalidates
		// the current iterator.
		OutputContainer::iterator next = it; next++;
		(*it)->setInputInternal( nullptr, true );
		it = next;
	}
	Metadata::clearInstanceMetadata( this );
}

bool Plug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !GraphComponent::acceptsChild( potentialChild ) )
	{
		return false;
	}
	const Plug *p = IECore::runTimeCast<const Plug>( potentialChild );
	if( !p )
	{
		return false;
	}
	/// \todo Having children of a different direction is useful,
	/// but we're currently only allowing it if the parent doesn't
	/// accept inputs. Figure out the correct logic for propagating
	/// connections from parents to children (and vice versa), and
	/// free things up to always allow differing directions. Should
	/// a child with a different direction be connected in the
	/// opposite direction?
	return p->direction() == direction() || !getFlags( AcceptsInputs );
}

bool Plug::acceptsParent( const GraphComponent *potentialParent ) const
{
	if( !GraphComponent::acceptsParent( potentialParent ) )
	{
		return false;
	}
	return potentialParent->isInstanceOf( (IECore::TypeId)NodeTypeId ) || potentialParent->isInstanceOf( Plug::staticTypeId() );
}

Node *Plug::node()
{
	return ancestor<Node>();
}

const Node *Plug::node() const
{
	return ancestor<Node>();
}

Plug::Direction Plug::direction() const
{
	return m_direction;
}

unsigned Plug::getFlags() const
{
	return m_flags;
}

bool Plug::getFlags( unsigned flags ) const
{
	return (m_flags & flags) == flags;
}

void Plug::setFlags( unsigned flags )
{
	if( flags == m_flags )
	{
		return;
	}

	if( !refCount() )
	{
		// No references to us - chances are we're being called
		// from the constructor. We can't implement undo (if we
		// have no references, we have no ScriptNode ancestor),
		// and Action::enact will add and remove a reference and
		// cause our premature destruction. Just set the flags
		// directly.
		setFlagsInternal( flags );
	}
	else
	{
		// We have references to us, so should implement things
		// in an undoable manner.
		Action::enact(
			this,
			boost::bind( &Plug::setFlagsInternal, this, flags ),
			boost::bind( &Plug::setFlagsInternal, this, m_flags )
		);
	}
}

void Plug::setFlags( unsigned flags, bool enable )
{
	setFlags( (m_flags & ~flags) | ( enable ? flags : 0 ) );
}

void Plug::setFlagsInternal( unsigned flags )
{
	m_flags = flags;

	if( Node *n = node() )
	{
		n->plugFlagsChangedSignal()( this );
	}
}

// The implementation of acceptsInputInternal() checks
// that the output plugs of a plug also accept the potential
// input. This can yield performance linear in the number
// of downstream connections, which is acceptable. However,
// it also calls `Node::acceptsInput()`, which can lead to
// greater complexity and unacceptable performance where an
// upstream `acceptsInput()` call triggers multiple identical
// downstream calls - see `GafferTest.SwitchTest.testAcceptsInputPerformance()`
// for a particularly bad example. To avoid this problem, we
// use a simple cache of results from `acceptsInputInternal()`,
// which persists only for the duration of the outermost
// `acceptsInput()` call.
class Plug::AcceptsInputCache
{

	private :

		struct ThreadData;
		typedef std::pair<const Plug *, const Plug *> PlugPair;
		typedef boost::unordered_map<PlugPair, bool> ResultMap;

	public :

		class Accessor
		{

			public :

				Accessor( const Plug *plug, const Plug *input )
					:	m_threadData( g_threadData.local() )
				{
					++m_threadData.depth;
					std::pair<ResultMap::iterator, bool> i = m_threadData.cache.insert(
						ResultMap::value_type( PlugPair( plug, input ), false )
					);
					if( i.second )
					{
						i.first->second = plug->acceptsInputInternal( input );
					}
					m_result = i.first->second;
				}

				~Accessor()
				{
					if( --m_threadData.depth == 0 )
					{
						// Outermost acceptsInput() call is
						// completing, so we clear the cache.
						m_threadData.cache.clear();
					}
				}

				bool get() const
				{
					return m_result;
				}

			private :

				bool m_result;
				ThreadData &m_threadData;

		};

	private :

		struct ThreadData
		{
			ThreadData() : depth( 0 ) {}
			int depth;
			ResultMap cache;
		};

		static tbb::enumerable_thread_specific<ThreadData> g_threadData;

};

tbb::enumerable_thread_specific<Plug::AcceptsInputCache::ThreadData> Plug::AcceptsInputCache::g_threadData;

bool Plug::acceptsInput( const Plug *input ) const
{
	AcceptsInputCache::Accessor accessor( this, input );
	return accessor.get();
}

bool Plug::acceptsInputInternal( const Plug *input ) const
{
	if( !getFlags( AcceptsInputs ) )
	{
		return false;
	}

	if( input == this )
	{
		return false;
	}

	// We should always accept a disconnection - how else could undo work?
	if( !input )
	{
		return true;
	}

	// If we accepted it previously, we can't change our minds now.
	if( input == getInput() )
	{
		return true;
	}

	// Give the node a say.
	if( const Node *n = node() )
	{
		if( !n->acceptsInput( this, input ) )
		{
			return false;
		}
	}

	// Give our outputs a chance to deny inputs they wouldn't accept themselves,
	// because an input to us is indirectly an input to them.
	for( OutputContainer::const_iterator it=m_outputs.begin(), eIt=m_outputs.end(); it!=eIt; ++it )
	{
		if( !(*it)->acceptsInput( input ) )
		{
			return false;
		}
	}

	// Make sure our children are happy to accept the equivalent child inputs.
	if( children().size() > input->children().size() )
	{
		return false;
	}
	for( PlugIterator it1( this ), it2( input ); !it1.done(); ++it1, ++it2 )
	{
		if( !( *it1 )->acceptsInput( it2->get() ) )
		{
			return false;
		}
	}

	return true;
}

/// \todo Make this non-virtual - it is too error prone to allow derived classes to
/// modify the mechanics of making connections. We could add a protected
/// `virtual inputChanging()` method that ValuePlug uses to do what it currently does
/// in `setInput()`, and we could rewrite ArrayPlug so that it only adds new plugs on
/// explicit request, not automatically in `plugInputChanged()`.
void Plug::setInput( PlugPtr input )
{
	setInput( input, /* setChildInputs = */ true, /* updateParentInput = */ true );
}

void Plug::setInput( PlugPtr input, bool setChildInputs, bool updateParentInput )
{
	if( input.get()==m_input )
	{
		if(
			// If the current input is non-null, we know that our
			// children have the appropriate corresponding
			// inputs too, so can exit early.
			m_input ||
			// But if the input is null, our children might
			// still have inputs of their own that we're meant
			// to be clearing, so we need to be careful about
			// when we take the shortcut.
			!setChildInputs ||
			allDescendantInputsAreNull( this )
		)
		{
			return;
		}
	}

	if( input && !acceptsInput( input.get() ) )
	{
		std::string what = boost::str(
			boost::format( "Plug \"%s\" rejects input \"%s\"." )
			% fullName()
			% input->fullName()
		);
		throw IECore::Exception( what );
	}

	// Connect our children first.
	// We use a dirty propagation scope to defer dirty signalling
	// until all connections have been made, when we're in our final
	// state.
	DirtyPropagationScope dirtyPropagationScope;

	if( setChildInputs )
	{
		if( !input )
		{
			for( PlugIterator it( this ); !it.done(); ++it )
			{
				(*it)->setInput( nullptr, /* setChildInputs = */ true, /* updateParentInput = */ false );
			}
		}
		else
		{
			for( PlugIterator it1( this ), it2( input.get() ); !it1.done(); ++it1, ++it2 )
			{
				(*it1)->setInput( *it2, /* setChildInputs = */ true, /* updateParentInput = */ false );
			}
		}
	}

	// then connect ourselves

	if( refCount() )
	{
		// someone is referring to us, so we're definitely fully constructed and we may have a ScriptNode
		// above us, so we should do things in a way compatible with the undo system.
		Action::enact(
			this,
			boost::bind( &Plug::setInputInternal, PlugPtr( this ), input, true ),
			boost::bind( &Plug::setInputInternal, PlugPtr( this ), PlugPtr( m_input ), true )
		);
	}
	else
	{
		// noone is referring to us. we're probably still constructing, and undo is impossible anyway (we
		// have no ScriptNode ancestor), so we can't make a smart pointer
		// to ourselves (it will result in double destruction). so we just set the input directly.
		setInputInternal( input, false );
	}

	// finally, adjust our parent's connection to take account of
	// the changes to its child.

	if( updateParentInput )
	{
		if( Plug *parentPlug = parent<Plug>() )
		{
			parentPlug->updateInputFromChildInputs( this );
		}
	}

}

void Plug::setInputInternal( PlugPtr input, bool emit )
{
	if( m_input )
	{
		m_input->m_outputs.remove( this );
	}
	m_input = input.get();
	if( m_input )
	{
		m_input->m_outputs.push_back( this );
	}
	if( emit )
	{
		// We must emit inputChanged prior to propagating
		// dirtiness, because inputChanged slots may be
		// used to rewire the graph, and we want to emit
		// plugDirtied only after all the rewiring is done.
		emitInputChanged();
		propagateDirtiness( this );
	}
}

void Plug::emitInputChanged()
{
	Node *n = node();
	if( n )
	{
		n->plugInputChangedSignal()( this );
	}

	// Take a copy of the outputs, owning a reference - because who
	// knows what will be added and removed by the connected slots.
	std::vector<PlugPtr> o( outputs().begin(), outputs().end() );
	for( std::vector<PlugPtr>::const_iterator it=o.begin(), eIt=o.end(); it!=eIt; ++it )
	{
		(*it)->emitInputChanged();
	}
}

void Plug::updateInputFromChildInputs( Plug *checkFirst )
{

#ifndef NDEBUG
	if( ScriptNode *scriptNode = ancestor<ScriptNode>() )
	{
		// This function should not be called during Undo/Redo. The actions
		// it takes should be recorded during Do and then undone/redone
		// automatically thereafter.
		assert( scriptNode->currentActionStage() != Action::Undo && scriptNode->currentActionStage() != Action::Redo );
	}
#endif // NDEBUG

	if( m_skipNextUpdateInputFromChildInputs )
	{
		m_skipNextUpdateInputFromChildInputs = false;
		return;
	}

	if( !children().size() )
	{
		return;
	}

	if( !checkFirst )
	{
		checkFirst = static_cast<Plug *>( children().front().get() );
	}

	Plug *input = checkFirst->getInput();
	if( !input || !input->parent<Plug>() )
	{
		setInput( nullptr, /* setChildInputs = */ false, /* updateParentInput = */ true );
		return;
	}

	Plug *candidateInput = input->parent<Plug>();
	if( !acceptsInput( candidateInput ) )
	{
		// if we're never going to accept the candidate input anyway, then
		// don't even bother checking to see if all the candidate's children
		// are connected to our children.
		setInput( nullptr, /* setChildInputs = */ false, /* updateParentInput = */ true );
		return;
	}

	for( PlugIterator it1( this ), it2( candidateInput ); !it1.done(); ++it1, ++it2 )
	{
		if( (*it1)->getInput() != it2->get() )
		{
			setInput( nullptr, /* setChildInputs = */ false, /* updateParentInput = */ true );
			return;
		}
	}

	setInput( candidateInput, /* setChildInputs = */ false, /* updateParentInput = */ true );
}

void Plug::removeOutputs()
{
	for( OutputContainer::iterator it = m_outputs.begin(); it!=m_outputs.end();  )
	{
		Plug *p = *it++;
		p->setInput( nullptr );
	}
}

const Plug::OutputContainer &Plug::outputs() const
{
	return m_outputs;
}

PlugPtr Plug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new Plug( name, direction, getFlags() );
	for( PlugIterator it( this ); !it.done(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

void Plug::parentChanging( Gaffer::GraphComponent *newParent )
{
	// When a plug is removed from a node, we need to propagate
	// dirtiness based on that. We must call `DependencyNode::affects()`
	// now, while the plug is still a child of the node, but we push
	// scope so that the emission of `plugDirtiedSignal()` is deferred
	// until `parentChanged()` when the operation is complete. It is
	// essential that exceptions don't prevent us getting to `parentChanged()`
	// where we pop scope, so propateDirtiness() takes care of handling
	// exceptions thrown by `DependencyNode::affects()`.
	pushDirtyPropagationScope();
	if( node() )
	{
		propagateDirtinessForParentChange( this );
	}

	// This method manages the connections between plugs when
	// additional child plugs are added or removed. We only
	// want to react to these changes when they are first made -
	// after this our own actions will have been recorded in the
	// undo buffer anyway and will be undone/redone automatically.
	// So here we early out if we're in such an Undo/Redo situation.

	ScriptNode *scriptNode = ancestor<ScriptNode>();
	scriptNode = scriptNode ? scriptNode : ( newParent ? newParent->ancestor<ScriptNode>() : nullptr );
	if( scriptNode && ( scriptNode->currentActionStage() == Action::Undo || scriptNode->currentActionStage() == Action::Redo ) )
	{
		return;
	}

	// Now we can take the actions we need to based on the new parent
	// we're getting.

	if( !newParent )
	{
		// We're losing our parent - remove all our connections first.
		// this must be done here (rather than in a parentChangedSignal() slot)
		// because we need a current parent for the operation to be undoable.
		setInput( nullptr );
		// Deal with outputs whose parent is an output of our parent.
		// For these we actually remove the destination plug itself,
		// so that the parent plugs may remain connected.
		if( Plug *oldParent = parent<Plug>() )
		{
			for( OutputContainer::iterator it = m_outputs.begin(); it!=m_outputs.end();  )
			{
				Plug *output = *it++;
				Plug *outputParent = output->parent<Plug>();
				if( outputParent && outputParent->getInput() == oldParent )
				{
					// We're removing the child precisely so that the parent connection
					// remains valid, so we can block its updateInputFromChildInputs() call.
					assert( outputParent->m_skipNextUpdateInputFromChildInputs == false );
					ScopedAssignment<bool> blocker( outputParent->m_skipNextUpdateInputFromChildInputs, true );
					outputParent->removeChild( output );
				}
			}
		}
		// Remove any remaining output connections.
		removeOutputs();
	}
	else if( Plug *newParentPlug = IECore::runTimeCast<Plug>( newParent ) )
	{
		// we're getting a new parent - update its input connection from
		// all the children including the pending one.
		newParentPlug->updateInputFromChildInputs( this );
		// and add a new child plug to any of its outputs to maintain
		// the output connections.
		const OutputContainer &outputs = newParentPlug->outputs();
		for( OutputContainer::const_iterator it = outputs.begin(), eIt = outputs.end(); it != eIt; ++it )
		{
			Plug *output = *it;
			PlugPtr outputChildPlug = createCounterpart( getName(), output->direction() );
			if( output->acceptsChild( outputChildPlug.get() ) )
			{
				{
					// We're adding the child so that the parent connection remains valid,
					// but the parent connection wouldn't be considered valid until the
					// child has both been added and had its input connected. We therefore
					// block the call to updateInputFromChildInputs() to keep the parent
					// connection intact.
					assert( output->m_skipNextUpdateInputFromChildInputs == false );
					ScopedAssignment<bool> blocker( output->m_skipNextUpdateInputFromChildInputs, true );
					output->addChild( outputChildPlug );
				}
				outputChildPlug->setInput( this, /* setChildInputs = */ true, /* updateParentInput = */ false );
			}
		}
	}

}

void Plug::parentChanged( Gaffer::GraphComponent *oldParent )
{
	GraphComponent::parentChanged( oldParent );

	if( node() )
	{
		// If a plug has been added to a node, we need to
		// propagate dirtiness.
		propagateDirtinessForParentChange( this );
	}
	// Pop the scope pushed in `parentChanging()`.
	popDirtyPropagationScope();
}

void Plug::propagateDirtinessForParentChange( Plug *plugToDirty )
{
	// When a plug is reparented, we need to take into account
	// all the descendants it brings with it, so we recurse to
	// find them, propagating dirtiness at the leaves.
	if( plugToDirty->children().size() )
	{
		for( PlugIterator it( plugToDirty ); !it.done(); ++it )
		{
			propagateDirtinessForParentChange( it->get() );
		}
	}
	else
	{
		propagateDirtiness( plugToDirty );
	}
}

//////////////////////////////////////////////////////////////////////////
// Dirty propagation
//////////////////////////////////////////////////////////////////////////

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
class Plug::DirtyPlugs
{

	public :

		DirtyPlugs()
			:	m_scopeCount( 0 ), m_emitting( false )
		{
		}

		void insert( Plug *plugToDirty )
		{
			if( m_emitting ) // see comment in emit()
			{
				return;
			}

			if( !insertVertex( plugToDirty ).second )
			{
				// Previously inserted, so we'll already
				// have visited the dependents.
				return;
			}

			for( DownstreamIterator it( plugToDirty ); !it.done(); ++it )
			{
				// The `const_casts()` are harmless because we're starting iteration from
				// a non-const plug. But they are necessary because DownstreamIterator
				// doesn't currently have a non-const form, and always yields const plugs.
				InsertedVertex v = insertVertex( const_cast<Plug *>( &*it ) );
				if( !it->getFlags( Plug::AcceptsDependencyCycles ) )
				{
					add_edge(
						v.first,
						insertVertex( const_cast<Plug *>( it.upstream() ) ).first,
						m_graph
					);
				}

				if( !v.second )
				{
					// Already visited this plug by another path,
					// so we can prune the iteration.
					it.prune();
				}
			}
		}

		void pushScope()
		{
			m_scopeCount++;
		}

		void popScope()
		{
			assert( m_scopeCount );
			if( --m_scopeCount == 0 )
			{
				if( !m_emitting ) // see comment in emit()
				{
					emit();
				}
			}
		}

		static DirtyPlugs &local()
		{
			static tbb::enumerable_thread_specific<Plug::DirtyPlugs> g_dirtyPlugs;
			return g_dirtyPlugs.local();
		}

	private :

		// We use this graph structure to keep track of the dirty propagation.
		// Vertices in the graph represent plugs which have been dirtied, and
		// edges represent the relationships that caused the dirtying - an
		// edge U,V indicates that U was dirtied by V. We do a depth_first_search
		// on the graph to give us an appropriate order to emit the dirty
		// signals in, so that dirtiness is only signalled for an affected plug
		// after it has been signalled for all upstream dirty plugs.
		typedef boost::adjacency_list<vecS, vecS, directedS, PlugPtr> Graph;
		typedef Graph::vertex_descriptor VertexDescriptor;
		typedef Graph::edge_descriptor EdgeDescriptor;

		typedef std::unordered_map<const Plug *, VertexDescriptor> PlugMap;

		// Equivalent to the return type for map::insert - the first
		// field is the vertex descriptor, and the second field is
		// false if the vertex was already there, true if it was
		// inserted.
		typedef std::pair<VertexDescriptor, bool> InsertedVertex;

		InsertedVertex insertVertex( Plug *plug )
		{
			// We need to hold a reference to the plug, because otherwise
			// it might be deleted between now and emit(). But if there is
			// no reference yet, the plug is still being constructed, and
			// we'd end up deleting it in emit() since we'd have sole
			// ownership. Nobody wants that. If we had weak pointers, this
			// would make for an ideal use.
			assert( plug->refCount() );

			PlugMap::const_iterator it = m_plugs.find( plug );
			if( it != m_plugs.end() )
			{
				return InsertedVertex( it->second, false );
			}

			VertexDescriptor result = add_vertex( m_graph );
			m_graph[result] = plug;
			m_plugs[plug] = result;

			// Insert parent plug.
			if( auto parent = plug->parent<Plug>() )
			{
				if( parent->refCount() )
				{
					VertexDescriptor parentVertex = insertVertex( parent ).first;
					add_edge( parentVertex, result, m_graph );
				}
				else
				{
					// We can end up here when constructing a SplinePlug,
					// because it calls setValue() in its constructor.
					// We don't want to increment the reference count on
					// an in-construction plug, because then we'll destroy
					// it in emit(). And there's no point signalling dirtiness
					// because the plug has no parent and therefore can have
					// no observers.
				}
			}

			return InsertedVertex( result, true );
		}

		struct EmitVisitor : public default_dfs_visitor
		{

			void back_edge( const EdgeDescriptor &e, const Graph &graph )
			{
				IECore::msg(
					IECore::Msg::Error, "Plug dirty propagation",
					boost::str(
						boost::format( "Cycle detected between %1% and %2%" ) %
							graph[boost::target( e, graph )]->fullName() %
							graph[boost::source( e, graph )]->fullName()
					)
				);
			}

			void finish_vertex( const VertexDescriptor &u, const Graph &graph )
			{
				Plug *plug = graph[u].get();
				plug->dirty();
				if( Node *node = plug->node() )
				{
					node->plugDirtiedSignal()( plug );
				}
			}

		};

		void emit()
		{
			// Because we hold a reference to the plugs via m_graph,
			// we may be the last owner. This means that when we clear
			// the graph below, those plugs may be destroyed, which can
			// trigger another dirty propagation as their child plugs are
			// removed etc.
			//
			// Additionally, emitting plugDirtiedSignal() can cause
			// ill-behaved code to trigger another dirty propagation
			// phase while we're emitting this one. This is explicitly
			// disallowed in the documentation for the Node class, but
			// unfortunately we can't control what the python interpreter
			// does - entering python via plugDirtiedSignal() can
			// trigger a garbage collection which might delete plugs
			// and trigger dirty propagation again as their children
			// and inputs are removed.
			//
			// We use the m_emitting flag to disable these unwanted
			// secondary propagations during emit(), since they're not
			// needed, and can cause crashes.

			ScopedAssignment<bool> scopedAssignment( m_emitting, true );

			try
			{
				depth_first_search( m_graph, visitor( EmitVisitor() ) );
			}
			catch( const std::exception &e )
			{
				IECore::msg( IECore::Msg::Error, "Plug dirty propagation", e.what() );
			}

			m_graph.clear();
			m_plugs.clear();
		}

		Graph m_graph;
		PlugMap m_plugs;
		size_t m_scopeCount;
		bool m_emitting;

};

void Plug::propagateDirtiness( Plug *plugToDirty )
{
	DirtyPropagationScope scope;
	DirtyPlugs::local().insert( plugToDirty );
}

void Plug::pushDirtyPropagationScope()
{
	DirtyPlugs::local().pushScope();
}

void Plug::popDirtyPropagationScope()
{
	DirtyPlugs::local().popScope();
}

void Plug::dirty()
{
}
