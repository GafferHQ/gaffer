//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/SourceSet.h"

#include "GafferSceneUI/ContextAlgo.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneNode.h"

#include "Gaffer/MetadataAlgo.h"

#include "IECore/Exception.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace {

// This is a re-implementation of the python version
// in SceneHistoryUI.py as we couldn't find a sensible
// name for this in the public API
// TODO: Re-home in MetadataAlgo we can make it make sense...
Node *ancestorWithReadOnlyChildNodes( Node *node )
{
	Node *ancestor = nullptr;
	while( node )
	{
		if( MetadataAlgo::getChildNodesAreReadOnly( node ) )
		{
			ancestor = node;
		}
		node = runTimeCast<Node>( node->parent() );
	}
	return ancestor;
}

}


SourceSet::SourceSet(  ContextPtr context, SetPtr nodeSet )
{
	setContext( context );
	setNodeSet( nodeSet );
}

SourceSet::~SourceSet()
{
}

void SourceSet::setContext( ContextPtr context )
{
	if( context == m_context )
	{
		return;
	}

	m_context = context;
	m_contextChangedConnection = context->changedSignal().connect( boost::bind( &SourceSet::contextChanged, this, ::_2 ) );
	updateSourceNode();
}

Context *SourceSet::getContext() const
{
	return m_context.get();
}

void SourceSet::setNodeSet( SetPtr nodeSet )
{
	if( nodeSet == m_nodes )
	{
		return;
	}

	m_nodes = nodeSet;
	m_nodeAddedConnection = nodeSet->memberAddedSignal().connect( boost::bind( &SourceSet::updateScenePlug, this ) );
	m_nodeRemovedConnection = nodeSet->memberRemovedSignal().connect( boost::bind( &SourceSet::updateScenePlug, this ) );
	updateScenePlug();
}

Set *SourceSet::getNodeSet() const
{
	return m_nodes.get();
}


bool SourceSet::contains( const Member *object ) const
{
	return m_sourceNode && m_sourceNode.get() == object;
}

Set::Member *SourceSet::member( size_t index )
{
	return m_sourceNode.get();
}

const Set::Member *SourceSet::member( size_t index ) const
{
	return m_sourceNode.get();
}

size_t SourceSet::size() const
{
	return m_sourceNode ? 1 : 0;
}

void SourceSet::contextChanged( const IECore::InternedString &name )
{
	if( ContextAlgo::affectsLastSelectedPath( name ) )
	{
		updateSourceNode();
	}
}

void SourceSet::plugDirtied( const Gaffer::Plug *plug )
{
	if( m_scenePlug && m_scenePlug == plug )
	{
		updateSourceNode();
	}
}

void SourceSet::updateScenePlug()
{
	ScenePlug *newScenePlug = nullptr;
	if( m_nodes && m_nodes->size() > 0 )
	{
		// We want the last selected node rather than the first
		Node const *node = runTimeCast<Node>( m_nodes->member( m_nodes->size() - 1 ) );
		if( node )
		{
			OutputScenePlugIterator it( node );
			if( !it.done() )
			{
				newScenePlug = it->get();
			}
		}
	}

	if( newScenePlug != m_scenePlug )
	{
		m_plugDirtiedConnection.disconnect();
		if( newScenePlug )
		{
			m_plugDirtiedConnection = newScenePlug->node()->plugDirtiedSignal().connect( boost::bind( &SourceSet::plugDirtied, this, ::_1 ) );
		}

		m_scenePlug = newScenePlug;
	}

	// We always update this (even if we don't find a scene plug) to ensure we update
	// the presented node through consecutive selection of nodes without scene plugs.
	updateSourceNode();
}

void SourceSet::updateSourceNode()
{
	Node *newSourceNode = nullptr;

	if( m_context && m_scenePlug )
	{
		const ScenePlug::ScenePath path = ContextAlgo::getLastSelectedPath( m_context.get() );

		Context::Scope scope( m_context.get() );
		try
		{
			if( !path.empty() && m_scenePlug->exists( path ) )
			{
				if( ScenePlug *sourcePlug = SceneAlgo::source( m_scenePlug.get(), path ) )
				{
					Node* const firstEditableAncestor = ancestorWithReadOnlyChildNodes( sourcePlug->node() );
					newSourceNode = firstEditableAncestor ? firstEditableAncestor : sourcePlug->node();
				}
			}
			else
			{
				newSourceNode = m_scenePlug->node();
			}
		}
		catch( std::exception &e )
		{
			/* this will reported by Node::errorSignal() */
		}
	}
	else if( m_nodes && m_nodes->size() > 0 )
	{
		// If we don't have a valid context or scene plug, but do have a node,
		// just assume that's the source. This generally makes sense for non-
		// scene nodes.
		newSourceNode = runTimeCast<Node>( m_nodes->member( m_nodes->size() - 1 ) );
	}

	if( newSourceNode != m_sourceNode )
	{
		if( m_sourceNode )
		{
			NodePtr oldSourceNode = m_sourceNode;
			m_sourceNode.reset();
			memberRemovedSignal()( this, oldSourceNode.get() );
		}

		m_sourceNode = newSourceNode;

		if( newSourceNode )
		{
			memberAddedSignal()( this, newSourceNode );
		}
	}
}
