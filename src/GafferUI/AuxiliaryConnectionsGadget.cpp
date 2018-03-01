//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/AuxiliaryConnectionsGadget.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "IECoreGL/Selector.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace GafferUI;
using namespace Gaffer;
using namespace IECore;
using namespace Imath;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename Visitor>
void visitAuxiliaryConnections( const GraphGadget *graphGadget, const NodeGadget *dstNodeGadget, Visitor visitor )
{
	const Gaffer::Node *dstNode = dstNodeGadget->node();
	for( Gaffer::RecursivePlugIterator it( dstNode ); !it.done(); ++it )
	{
		const Gaffer::Plug *dstPlug = it->get();
		const Gaffer::Plug *srcPlug = dstPlug->getInput();
		if( !srcPlug )
		{
			continue;
		}

		it.prune();
		if( srcPlug->node() == dstNode )
		{
			continue;
		}

		const NodeGadget *srcNodeGadget = graphGadget->nodeGadget( srcPlug->node() );
		if( !srcNodeGadget )
		{
			continue;
		}
		if( dstNodeGadget->nodule( dstPlug ) )
		{
			continue;
		}

		visitor( srcPlug, dstPlug, srcNodeGadget, dstNodeGadget );
	}
}

Box2f nodeFrame( const NodeGadget *nodeGadget )
{
	const Box3f b = nodeGadget->transformedBound();
	return Box2f(
		V2f( b.min.x, b.min.y ),
		V2f( b.max.x, b.max.y )
	);
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// AuxiliaryConnectionsGadget
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( AuxiliaryConnectionsGadget );

AuxiliaryConnectionsGadget::AuxiliaryConnectionsGadget()
	:	Gadget( "AuxiliaryConnections" ), m_dirty( false )
{
}

AuxiliaryConnectionsGadget::~AuxiliaryConnectionsGadget()
{
}

bool AuxiliaryConnectionsGadget::hasConnection( const NodeGadget *srcNodeGadget, const NodeGadget *dstNodeGadget ) const
{
	updateConnections();
	auto it = m_nodeGadgetConnections.find( dstNodeGadget );
	return it != m_nodeGadgetConnections.end() && it->second.sourceGadgets.count( srcNodeGadget );
}

bool AuxiliaryConnectionsGadget::hasConnection( const Gaffer::Node *srcNode, const Gaffer::Node *dstNode ) const
{
	const NodeGadget *srcNodeGadget = graphGadget()->nodeGadget( srcNode );
	const NodeGadget *dstNodeGadget = graphGadget()->nodeGadget( dstNode );
	if( !srcNodeGadget || !dstNodeGadget )
	{
		return false;
	}
	return hasConnection( srcNodeGadget, dstNodeGadget );
}

std::pair<NodeGadget *, NodeGadget *> AuxiliaryConnectionsGadget::connectionAt( const IECore::LineSegment3f &position )
{
	std::pair<const NodeGadget *, const NodeGadget *> c = const_cast<const AuxiliaryConnectionsGadget *>( this )->connectionAt( position );
	return { const_cast<NodeGadget *>( c.first ), const_cast<NodeGadget *>( c.second ) };
}

std::pair<const NodeGadget *, const NodeGadget *> AuxiliaryConnectionsGadget::connectionAt( const IECore::LineSegment3f &position ) const
{
	updateConnections();

	vector<IECoreGL::HitRecord> selection;
	vector<pair<const NodeGadget *, const NodeGadget *>> connections;

	{
		ViewportGadget::SelectionScope selectionScope( position, this, selection, IECoreGL::Selector::IDRender );
		IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();
		const Style *style = this->style();
		style->bind();
		GLuint name = 1; // Name 0 is invalid, so we start at 1
		for( auto &x : m_nodeGadgetConnections )
		{
			const NodeGadget *dstNodeGadget = x.first;
			const Box2f dstFrame = nodeFrame( dstNodeGadget );
			for( auto &srcNodeGadget : x.second.sourceGadgets )
			{
				connections.push_back( { srcNodeGadget, dstNodeGadget } );
				selector->loadName( name++ );
				style->renderAuxiliaryConnection( nodeFrame( srcNodeGadget ), dstFrame, Style::NormalState );
			}
		}
	}

	if( !selection.size() )
	{
		return { nullptr, nullptr };
	}

	return connections[selection[0].name-1];
}

bool AuxiliaryConnectionsGadget::acceptsParent( const GraphComponent *potentialParent ) const
{
	return runTimeCast<const GraphGadget>( potentialParent );
}

void AuxiliaryConnectionsGadget::parentChanging( Gaffer::GraphComponent *newParent )
{
	m_nodeGadgetConnections.clear();
	m_graphGadgetChildAddedConnection.disconnect();
	m_graphGadgetChildRemovedConnection.disconnect();
	if( newParent )
	{
		m_graphGadgetChildAddedConnection = newParent->childAddedSignal().connect(
			boost::bind( &AuxiliaryConnectionsGadget::graphGadgetChildAdded, this, ::_2 )
		);
		m_graphGadgetChildRemovedConnection = newParent->childRemovedSignal().connect(
			boost::bind( &AuxiliaryConnectionsGadget::graphGadgetChildRemoved, this, ::_2 )
		);
	}
}

std::string AuxiliaryConnectionsGadget::getToolTip( const IECore::LineSegment3f &position ) const
{
	string s = Gadget::getToolTip( position );
	if( !s.empty() )
	{
		return s;
	}

	pair<const NodeGadget *, const NodeGadget *> connection = connectionAt( position );
	if( !connection.first )
	{
		return "";
	}

	s += "Auxiliary connections from " + connection.first->node()->getName().string() + " to " + connection.second->node()->getName().string() + " : \n\n";
	visitAuxiliaryConnections(
		graphGadget(), connection.second,
		[ &s, &connection ] ( const Plug *srcPlug, const Plug *dstPlug, const NodeGadget *srcNodeGadget, const NodeGadget *dstNodeGadget )
		{
			if( srcNodeGadget == connection.first )
			{
				s +=
					"\t" +
					srcPlug->relativeName( srcNodeGadget->node() ) +
					" -> " +
					dstPlug->relativeName( dstNodeGadget->node() ) +
					"\n"
				;
			}
		}
	);

	return s;
}

void AuxiliaryConnectionsGadget::doRenderLayer( Layer layer, const Style *style ) const
{
	if( layer != GraphLayer::Connections )
	{
		return;
	}

	updateConnections();
	for( auto &x : m_nodeGadgetConnections )
	{
		bool dstHighlighted = x.first->getHighlighted();
		const Box2f dstFrame = nodeFrame( x.first );
		for( auto &srcNodeGadget : x.second.sourceGadgets )
		{
			Style::State state = dstHighlighted || srcNodeGadget->getHighlighted() ? Style::HighlightedState : Style::NormalState;
			style->renderAuxiliaryConnection( nodeFrame( srcNodeGadget ), dstFrame, state );
		}
	}
}

GraphGadget *AuxiliaryConnectionsGadget::graphGadget()
{
	return parent<GraphGadget>();
}

const GraphGadget *AuxiliaryConnectionsGadget::graphGadget() const
{
	return parent<GraphGadget>();
}

void AuxiliaryConnectionsGadget::graphGadgetChildAdded( GraphComponent *child )
{
	if( NodeGadget *nodeGadget = runTimeCast<NodeGadget>( child ) )
	{
		Connections &connections = m_nodeGadgetConnections[nodeGadget];

		connections.plugInputChangedConnection = nodeGadget->node()->plugInputChangedSignal().connect(
			boost::bind( &AuxiliaryConnectionsGadget::plugInputChanged, this, ::_1 )
		);
		connections.noduleAddedConnection = nodeGadget->noduleAddedSignal().connect(
			boost::bind( &AuxiliaryConnectionsGadget::noduleAdded, this, ::_1, ::_2 )
		);
		connections.noduleRemovedConnection = nodeGadget->noduleRemovedSignal().connect(
			boost::bind( &AuxiliaryConnectionsGadget::noduleRemoved, this, ::_1, ::_2 )
		);
		connections.childRemovedConnection = nodeGadget->node()->childRemovedSignal().connect(
			boost::bind( &AuxiliaryConnectionsGadget::childRemoved, this, ::_1, ::_2 )
		);

		connections.dirty = true;
		m_dirty = true;
	}
}

void AuxiliaryConnectionsGadget::graphGadgetChildRemoved( const GraphComponent *child )
{
	if( const NodeGadget *nodeGadget = runTimeCast<const NodeGadget>( child ) )
	{
		m_nodeGadgetConnections.erase( nodeGadget );
	}
}

void AuxiliaryConnectionsGadget::plugInputChanged( const Gaffer::Plug *plug )
{
	if( const NodeGadget *nodeGadget = graphGadget()->nodeGadget( plug->node() ) )
	{
		dirty( nodeGadget );
	}
}

void AuxiliaryConnectionsGadget::childRemoved( const Gaffer::GraphComponent *node, const Gaffer::GraphComponent *child )
{
	if( !runTimeCast<const Plug>( child ) )
	{
		return;
	}
	if( const NodeGadget *nodeGadget = graphGadget()->nodeGadget( static_cast<const Node *>( node ) ) )
	{
		dirty( nodeGadget );
	}
}

void AuxiliaryConnectionsGadget::noduleAdded( const NodeGadget *nodeGadget, const Nodule *nodule )
{
	dirty( nodeGadget );
}

void AuxiliaryConnectionsGadget::noduleRemoved( const NodeGadget *nodeGadget, const Nodule *nodule )
{
	dirty( nodeGadget );
}

void AuxiliaryConnectionsGadget::dirty( const NodeGadget *nodeGadget )
{
	auto it = m_nodeGadgetConnections.find( nodeGadget );
	// We only connect to signals for NodeGadgets we're tracking,
	// so we have a logic error somewhere if we don't already have
	// an entry for this particular node gadget.
	assert( it != m_nodeGadgetConnections.end() );
	if( it->second.dirty )
	{
		return;
	}
	it->second.dirty = true;
	if( m_dirty )
	{
		return;
	}
	m_dirty = true;
	requestRender();
}

void AuxiliaryConnectionsGadget::updateConnections() const
{
	if( !m_dirty )
	{
		return;
	}

	for( auto &x : m_nodeGadgetConnections )
	{
		Connections &connections = x.second;
		if( !connections.dirty )
		{
			continue;
		}

		connections.sourceGadgets.clear();
		visitAuxiliaryConnections(
			graphGadget(), x.first,
			[&connections] ( const Plug *srcPlug, const Plug *dstPlug, const NodeGadget *srcNodeGadget, const NodeGadget *dstNodeGadget )
			{
				connections.sourceGadgets.insert( srcNodeGadget );
			}
		);

		connections.dirty = false;
	}

	m_dirty = false;
}

