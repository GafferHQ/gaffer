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

#include "tbb/enumerable_thread_specific.h"

#include "boost/format.hpp"
#include "boost/bind.hpp"
#include "boost/graph/adjacency_list.hpp"
#include "boost/graph/topological_sort.hpp"

#include "IECore/Exception.h"

#include "Gaffer/Plug.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/Action.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Metadata.h"

using namespace boost;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// ScopedAssignment utility class
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

} // namespace

//////////////////////////////////////////////////////////////////////////
// Plug implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Plug );

Plug::Plug( const std::string &name, Direction direction, unsigned flags )
	:	GraphComponent( name ), m_direction( direction ), m_input( 0 ), m_flags( None ), m_skipNextUpdateInputFromChildInputs( false )
{
	setFlags( flags );
	parentChangedSignal().connect( boost::bind( &Plug::parentChanged, this ) );
}

Plug::~Plug()
{
	setInputInternal( 0, false );
	for( OutputContainer::iterator it=m_outputs.begin(); it!=m_outputs.end(); )
	{
	 	// get the next iterator now, as the call to setInputInternal invalidates
		// the current iterator.
		OutputContainer::iterator next = it; next++;
		(*it)->setInputInternal( 0, true );
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
	return p->direction()==direction();
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

	if( (flags & ReadOnly) && direction() == Out )
	{
		throw IECore::Exception( "Output plug cannot be read only" );
	}

	m_flags = flags;

	if( Node *n = node() )
	{
		n->plugFlagsChangedSignal()( this );
	}
}

void Plug::setFlags( unsigned flags, bool enable )
{
	setFlags( (m_flags & ~flags) | ( enable ? flags : 0 ) );
}

bool Plug::acceptsInput( const Plug *input ) const
{
	if( !getFlags( AcceptsInputs ) || getFlags( ReadOnly ) )
	{
		return false;
	}

	if( input == this )
	{
		return false;
	}

	if( const Node *n = node() )
	{
		if( !n->acceptsInput( this, input ) )
		{
			return false;
		}
	}

	for( OutputContainer::const_iterator it=m_outputs.begin(), eIt=m_outputs.end(); it!=eIt; ++it )
	{
		if( !(*it)->acceptsInput( input ) )
		{
			return false;
		}
	}

	if( input )
	{
		if( children().size() > input->children().size() )
		{
			return false;
		}
		for( PlugIterator it1( this ), it2( input ); it1!=it1.end(); ++it1, ++it2 )
		{
			if( !( *it1 )->acceptsInput( it2->get() ) )
			{
				return false;
			}
		}
	}

	return true;
}

void Plug::setInput( PlugPtr input )
{
	setInput( input, /* setChildInputs = */ true, /* updateParentInput = */ true );
}

void Plug::setInput( PlugPtr input, bool setChildInputs, bool updateParentInput )
{
	if( input.get()==m_input )
	{
		return;
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
			for( PlugIterator it( this ); it!=it.end(); ++it )
			{
				(*it)->setInput( NULL, /* setChildInputs = */ true, /* updateParentInput = */ false );
			}
		}
		else
		{
			for( PlugIterator it1( this ), it2( input.get() ); it1!=it1.end(); ++it1, ++it2 )
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
		Node *n = node();
		if( n )
		{
			n->plugInputChangedSignal()( this );
		}
		propagateDirtiness( this );
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

	Plug *input = checkFirst->getInput<Plug>();
	if( !input || !input->parent<Plug>() )
	{
		setInput( NULL, /* setChildInputs = */ false, /* updateParentInput = */ true );
		return;
	}

	Plug *commonParent = input->parent<Plug>();
	if( !acceptsInput( commonParent ) )
	{
		// if we're never going to accept the candidate input anyway, then
		// don't even bother checking to see if all the candidate's children
		// are connected to our children.
		setInput( NULL, /* setChildInputs = */ false, /* updateParentInput = */ true );
		return;
	}

	for( PlugIterator it( this ); it!=it.end(); ++it )
	{
		input = (*it)->getInput<Plug>();
		if( !input || input->parent<Plug>()!=commonParent )
		{
			setInput( NULL, /* setChildInputs = */ false, /* updateParentInput = */ true );
			return;
		}
	}

	setInput( commonParent, /* setChildInputs = */ false, /* updateParentInput = */ true );
}

void Plug::removeOutputs()
{
	for( OutputContainer::iterator it = m_outputs.begin(); it!=m_outputs.end();  )
	{
		Plug *p = *it++;
		p->setInput( 0 );
	}
}

const Plug::OutputContainer &Plug::outputs() const
{
	return m_outputs;
}

PlugPtr Plug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new Plug( name, direction, getFlags() );
	for( PlugIterator it( this ); it != it.end(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

void Plug::parentChanging( Gaffer::GraphComponent *newParent )
{
	if( getFlags( Dynamic ) )
	{
		// When a dynamic plug is removed from a node, we
		// need to propagate dirtiness based on that. We
		// must call DependencyNode::affects() now, while the
		// plug is still a child of the node, but we push
		// scope so that the emission of plugDirtiedSignal()
		// is deferred until parentChanged() when the operation
		// is complete. It is essential that exceptions don't
		// prevent us getting to parentChanged() where we pop
		// scope, so propateDirtiness() takes care of handling
		// exceptions thrown by DependencyNode::affects().
		pushDirtyPropagationScope();
		if( node() )
		{
			propagateDirtinessForParentChange( this );
		}
	}

	// This method manages the connections between plugs when
	// additional child plugs are added or removed. We only
	// want to react to these changes when they are first made -
	// after this our own actions will have been recorded in the
	// undo buffer anyway and will be undone/redone automatically.
	// So here we early out if we're in such an Undo/Redo situation.

	ScriptNode *scriptNode = ancestor<ScriptNode>();
	scriptNode = scriptNode ? scriptNode : ( newParent ? newParent->ancestor<ScriptNode>() : NULL );
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
		setInput( 0 );
		// Deal with outputs whose parent is an output of our parent.
		// For these we actually remove the destination plug itself,
		// so that the parent plugs may remain connected.
		if( Plug *oldParent = parent<Plug>() )
		{
			for( OutputContainer::iterator it = m_outputs.begin(); it!=m_outputs.end();  )
			{
				Plug *output = *it++;
				Plug *outputParent = output->parent<Plug>();
				if( outputParent && outputParent->getInput<Plug>() == oldParent )
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
			if( output->acceptsChild( this ) )
			{
				PlugPtr outputChildPlug = createCounterpart( getName(), direction() );
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

void Plug::parentChanged()
{
	if( getFlags( Dynamic ) )
	{
		if( node() )
		{
			// If a dynamic plug has been added to a
			// node, we need to propagate dirtiness.
			propagateDirtinessForParentChange( this );
		}
		// Pop the scope pushed in parentChanging().
		popDirtyPropagationScope();
	}
}

void Plug::propagateDirtinessForParentChange( Plug *plugToDirty )
{
	// When a plug is reparented, we need to take into account
	// all the descendants it brings with it, so we recurse to
	// find them, propagating dirtiness at the leaves.
	if( plugToDirty->children().size() )
	{
		for( PlugIterator it( plugToDirty ); it != it.end(); ++it )
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
			:	m_scopeCount( 0 ), m_clearing( false )
		{
		}

		void insert( Plug *plugToDirty )
		{
			if( !m_clearing ) // see comment in clear()
			{
				insertInternal( plugToDirty );
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
				if( !m_clearing ) // see comment in clear()
				{
					emit();
					clear();
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
		// edge U,V indicates that U was dirtied by V. We do a topological
		// sort on the graph to give us an appropriate order to emit the dirty
		// signals in, so that dirtiness is only signalled for an affected plug
		// after it has been signalled for all upstream dirty plugs.
		typedef boost::adjacency_list<vecS, vecS, directedS, PlugPtr> Graph;
		typedef Graph::vertex_descriptor VertexDescriptor;

		typedef std::map<const Plug *, VertexDescriptor> PlugMap;

		// Inserts a vertex representing plugToDirty into the graph, and
		// then inserts all affected plugs.
		VertexDescriptor insertInternal( Plug *plugToDirty )
		{
			// We need to hold a reference to the plug, because otherwise
			// it might be deleted between now and emit(). But if there is
			// no reference yet, the plug is still being constructed, and
			// we'd end up deleting it in clear() since we'd have sole
			// ownership. Nobody wants that. If we had weak pointers, this
			// would make for an ideal use.
			assert( plugToDirty->refCount() );

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

			// Insert all ancestor plugs.
			Plug *child = plugToDirty;
			VertexDescriptor childVertex = result;
			while( Plug *parent = child->parent<Plug>() )
			{
				if( !parent->refCount() )
				{
					// We can end up here when constructing a SplinePlug,
					// because it calls setValue() in its constructor.
					// We don't want to increment the reference count on
					// an in-construction plug, because then we'll destroy
					// it in clear(). And there's no point signalling dirtiness
					// because the plug has no parent and therefore can have
					// no observers.
					break;
				}

				VertexDescriptor parentVertex = insertInternal( parent );
				add_edge( parentVertex, childVertex, m_graph );

				child = parent;
				childVertex = parentVertex;
			}

			// Propagate dirtiness to output plugs and affected plugs.
			// We only propagate dirtiness along leaf level plugs, because
			// they are the only plugs which can be the target of the affects(),
			// and compute() methods. We must handle any exceptions thrown by
			// DependencyNode::affects() so that we don't leave the graph in
			// an unexpected state - propagateDirtiness() is called in the middle
			// of addChild(), setInput() and setValue() methods, and we want those
			// to succeed at all costs.
			if( !plugToDirty->isInstanceOf( (IECore::TypeId)CompoundPlugTypeId ) )
			{
				for( Plug::OutputContainer::const_iterator it=plugToDirty->outputs().begin(), eIt=plugToDirty->outputs().end(); it!=eIt; ++it )
				{
					VertexDescriptor outputVertex = insertInternal( const_cast<Plug *>( *it ) );
					add_edge( outputVertex, result, m_graph );
				}

				const DependencyNode *dependencyNode = plugToDirty->ancestor<DependencyNode>();
				if( dependencyNode )
				{
					DependencyNode::AffectedPlugsContainer affected;
					try
					{
						dependencyNode->affects( plugToDirty, affected );
					}
					catch( const std::exception &e )
					{
						IECore::msg(
							IECore::Msg::Error,
							dependencyNode->relativeName( dependencyNode->scriptNode() ) + "::affects()",
							e.what()
						);
					}
					catch( ... )
					{
						IECore::msg(
							IECore::Msg::Error,
							dependencyNode->relativeName( dependencyNode->scriptNode() ) + "::affects()",
							"Unknown exception"
						);
					}

					for( DependencyNode::AffectedPlugsContainer::const_iterator it=affected.begin(); it!=affected.end(); it++ )
					{
						if( ( *it )->isInstanceOf( (IECore::TypeId)Gaffer::CompoundPlugTypeId ) )
						{
							// DependencyNode::affects() implementations are only allowed to place leaf plugs in the outputs,
							// so we helpfully report any mistakes.
							IECore::msg(
								IECore::Msg::Error,
								dependencyNode->relativeName( dependencyNode->scriptNode() ) + "::affects()",
								"Non-leaf plug " + (*it)->relativeName( dependencyNode ) + " returned by affects()"
							);
							continue;
						}
						// cast is ok - AffectedPlugsContainer only holds const pointers so that
						// affects() can be const to discourage implementations from having side effects.
						VertexDescriptor affectedVertex = insertInternal( const_cast<Plug *>( *it ) );
						add_edge( affectedVertex, result, m_graph );
					}
				}
			}

			return result;
		}

		void emit()
		{
			std::vector<VertexDescriptor> sorted;
			topological_sort( m_graph, std::back_inserter( sorted ) );
			for( std::vector<VertexDescriptor>::const_iterator it = sorted.begin(), eIt = sorted.end(); it != eIt; ++it )
			{
				Plug *plug = m_graph[*it].get();
				plug->dirty();
				if( Node *node = plug->node() )
				{
					node->plugDirtiedSignal()( plug );
				}
			}
		}

		void clear()
		{
			// Because we hold a reference to the plugs via the graph,
			// we may be the last owner. This means that when we call
			// clear, those plugs may be destroyed, which can trigger
			// a dirty propagation as their child plugs are removed
			// etc. We use the m_clearing flag to disable this propagation,
			// since it's not needed, and can cause crashes. In an ideal
			// world we'd have weak pointers, and could use those in
			// the graph, so that we'd have no ownership of the plugs at
			// all.
			ScopedAssignment<bool> scopedAssignment( m_clearing, true );
			m_graph.clear();
			m_plugs.clear();
		}

		Graph m_graph;
		PlugMap m_plugs;
		size_t m_scopeCount;
		bool m_clearing;

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
