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
#include "GafferUI/Nodule.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/Expression.h"

#include "IECoreGL/Selector.h"

#include "OpenEXR/ImathBoxAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
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

const Gadget *endGadget( const Plug *plug, const NodeGadget *nodeGadget )
{
	while( plug )
	{
		if( const Nodule *n = nodeGadget->nodule( plug ) )
		{
			return n;
		}
		plug = plug->parent<Plug>();
	}
	return nodeGadget;
}

template<typename Visitor>
void visitAuxiliaryConnections( const GraphGadget *graphGadget, const NodeGadget *dstNodeGadget, Visitor visitor )
{
	const Gaffer::Node *dstNode = dstNodeGadget->node();
	/// \todo Once the expression node refactor is done, it shouldn't be using
	/// private plugs for its inputs, and we can ignore all private plugs
	/// unconditionally.
	const bool ignorePrivatePlugs = !runTimeCast<const Expression>( dstNode );
	for( Gaffer::Plug::RecursiveIterator it( dstNode ); !it.done(); ++it )
	{
		const Gaffer::Plug *dstPlug = it->get();
		if( ignorePrivatePlugs && boost::starts_with( dstPlug->getName().c_str(), "__" ) )
		{
			it.prune();
			continue;
		}

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

		visitor(
			srcPlug, dstPlug,
			srcNodeGadget, dstNodeGadget,
			endGadget( srcPlug, srcNodeGadget ),
			endGadget( dstPlug, dstNodeGadget )
		);
	}
}

Box2f nodeFrame( const NodeGadget *nodeGadget )
{
	const Box3f b = nodeGadget->transformedBound( nullptr );
	return Box2f(
		V2f( b.min.x, b.min.y ),
		V2f( b.max.x, b.max.y )
	);
}

V2f gadgetCenter( const Gadget *gadget )
{
	Box3f b = gadget->bound();
	if( b.isEmpty() )
	{
		b = Box3f( V3f( 0 ) );
	}
	const V3f c = transform( b, gadget->fullTransform() ).center();
	return V2f( c.x, c.y );
}

string gadgetName( const Gadget *gadget )
{
	if( auto nodeGadget = runTimeCast<const NodeGadget>( gadget ) )
	{
		return nodeGadget->node()->getName().string();
	}
	else
	{
		auto plug = static_cast<const Nodule *>( gadget )->plug();
		return plug->node()->getName().string() + "." + plug->relativeName( plug->node() );
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// AuxiliaryConnectionsGadget
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( AuxiliaryConnectionsGadget );

AuxiliaryConnectionsGadget::AuxiliaryConnectionsGadget()
	:	Gadget( "AuxiliaryConnections" ), m_dirty( false )
{
}

AuxiliaryConnectionsGadget::~AuxiliaryConnectionsGadget()
{
}

bool AuxiliaryConnectionsGadget::hasConnection( const Gadget *srcGadget, const Gadget *dstGadget ) const
{
	updateConnections();
	return m_auxiliaryConnections.count( make_pair( srcGadget, dstGadget ) );
}

bool AuxiliaryConnectionsGadget::hasConnection( const Gaffer::Node *srcNode, const Gaffer::Node *dstNode ) const
{
	const NodeGadget *srcNodeGadget = graphGadget()->nodeGadget( srcNode );
	const NodeGadget *dstNodeGadget = graphGadget()->nodeGadget( dstNode );
	if( !srcNodeGadget || !dstNodeGadget )
	{
		return false;
	}

	updateConnections();

	auto srcRange = srcNodeGadgetIndex().equal_range( srcNodeGadget );
	for( auto it = srcRange.first; it != srcRange.second; ++it )
	{
		if( it->dstNodeGadget == dstNodeGadget )
		{
			return true;
		}
	}
	return false;
}

std::pair<Gadget *, Gadget *> AuxiliaryConnectionsGadget::connectionAt( const IECore::LineSegment3f &position )
{
	std::pair<const Gadget *, const Gadget *> c = const_cast<const AuxiliaryConnectionsGadget *>( this )->connectionAt( position );
	return { const_cast<Gadget *>( c.first ), const_cast<Gadget *>( c.second ) };
}

std::pair<const Gadget *, const Gadget *> AuxiliaryConnectionsGadget::connectionAt( const IECore::LineSegment3f &position ) const
{
	updateConnections();

	vector<IECoreGL::HitRecord> selection;
	vector<pair<const Gadget *, const Gadget *>> connections;

	{
		ViewportGadget::SelectionScope selectionScope( position, this, selection, IECoreGL::Selector::IDRender );
		IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();
		const Style *style = this->style();
		style->bind();
		GLuint name = 1; // Name 0 is invalid, so we start at 1

		for( auto &c : m_auxiliaryConnections )
		{
			connections.push_back( c.endpoints );
			selector->loadName( name++ );
			renderConnection( c, style );
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

	auto connection = connectionAt( position );
	if( !connection.first )
	{
		return "";
	}

	auto dstNodeGadget = runTimeCast<const NodeGadget>( connection.second );
	dstNodeGadget = dstNodeGadget ? dstNodeGadget : connection.second->ancestor<NodeGadget>();

	s += "Auxiliary connections from " + gadgetName( connection.first ) + " to " + gadgetName( connection.second ) + " : \n\n";
	visitAuxiliaryConnections(
		graphGadget(), dstNodeGadget,
		[ &s, &connection ] ( const Plug *srcPlug, const Plug *dstPlug, const NodeGadget *srcNodeGadget, const NodeGadget *dstNodeGadget, const Gadget *srcGadget, const Gadget *dstGadget )
		{
			if( srcGadget == connection.first && dstGadget == connection.second )
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

void AuxiliaryConnectionsGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	if( layer != GraphLayer::Connections )
	{
		return;
	}

	updateConnections();
	for( auto &c : m_auxiliaryConnections )
	{
		renderConnection( c, style );
	}
}

unsigned AuxiliaryConnectionsGadget::layerMask() const
{
	return (unsigned)GraphLayer::Connections;
}

Box3f AuxiliaryConnectionsGadget::renderBound() const
{
	Box3f b;
	b.makeInfinite();
	return b;
}

void AuxiliaryConnectionsGadget::renderConnection( const AuxiliaryConnection &c, const Style *style ) const
{
	const Style::State state = c.srcNodeGadget->getHighlighted() || c.dstNodeGadget->getHighlighted() ? Style::HighlightedState : Style::NormalState;
	if( c.srcNodeGadget == c.endpoints.first && c.dstNodeGadget == c.endpoints.second )
	{
		// Connection between nodes
		style->renderAuxiliaryConnection( nodeFrame( c.srcNodeGadget ), nodeFrame( c.dstNodeGadget ), state );
	}
	else
	{
		// Connection involving a least one nodule
		const V2f srcPos = gadgetCenter( c.endpoints.first );
		const V2f dstPos = gadgetCenter( c.endpoints.second );
		V2f srcTangent( 0 );
		V2f dstTangent( 0 );
		if( c.endpoints.first != c.srcNodeGadget )
		{
			const V3f v = c.srcNodeGadget->connectionTangent( static_cast<const Nodule *>( c.endpoints.first ) );
			srcTangent = V2f( v.x, v.y );
		}
		if( c.endpoints.second != c.dstNodeGadget )
		{
			const V3f v = c.dstNodeGadget->connectionTangent( static_cast<const Nodule *>( c.endpoints.second ) );
			dstTangent = V2f( v.x, v.y );
		}

		style->renderAuxiliaryConnection( srcPos, srcTangent, dstPos, dstTangent, state );
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
		dirtyInputConnections( nodeGadget );
		dirtyOutputConnections( nodeGadget );
		m_nodeGadgetConnections.erase( nodeGadget );
	}
}

void AuxiliaryConnectionsGadget::plugInputChanged( const Gaffer::Plug *plug )
{
	if( const NodeGadget *nodeGadget = graphGadget()->nodeGadget( plug->node() ) )
	{
		dirtyInputConnections( nodeGadget );
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
		dirtyInputConnections( nodeGadget );
		dirtyOutputConnections( nodeGadget );
	}
}

void AuxiliaryConnectionsGadget::noduleAdded( const NodeGadget *nodeGadget, const Nodule *nodule )
{
	dirtyInputConnections( nodeGadget );
	dirtyOutputConnections( nodeGadget );
}

void AuxiliaryConnectionsGadget::noduleRemoved( const NodeGadget *nodeGadget, const Nodule *nodule )
{
	dirtyInputConnections( nodeGadget );
	dirtyOutputConnections( nodeGadget );
}

void AuxiliaryConnectionsGadget::dirtyInputConnections( const NodeGadget *nodeGadget )
{
	auto it = m_nodeGadgetConnections.find( nodeGadget );
	// We only connect to signals for NodeGadgets we're tracking,
	// so we have a logic error somewhere if we don't already have
	// an entry for this particular node gadget.
	assert( it != m_nodeGadgetConnections.end() );

	auto &dstIndex = dstNodeGadgetIndex();
	auto dstRange = dstIndex.equal_range( nodeGadget );
	dstIndex.erase( dstRange.first, dstRange.second );
	it->second.dirty = true;

	if( m_dirty )
	{
		return;
	}
	m_dirty = true;
	dirty( DirtyType::Render );
}

void AuxiliaryConnectionsGadget::dirtyOutputConnections( const NodeGadget *nodeGadget )
{
	auto &srcIndex = srcNodeGadgetIndex();
	auto srcRange = srcIndex.equal_range( nodeGadget );
	for( auto it = srcRange.first; it != srcRange.second; ++it )
	{
		auto cIt = m_nodeGadgetConnections.find( it->dstNodeGadget );
		assert( cIt != m_nodeGadgetConnections.end() );
		cIt->second.dirty = true;
	}

	srcIndex.erase( srcRange.first, srcRange.second );

	if( m_dirty )
	{
		return;
	}
	m_dirty = true;
	dirty( DirtyType::Render );
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

		visitAuxiliaryConnections(
			graphGadget(), x.first,
			[this] ( const Plug *srcPlug, const Plug *dstPlug, const NodeGadget *srcNodeGadget, const NodeGadget *dstNodeGadget, const Gadget *srcGadget, const Gadget *dstGadget )
			{
				AuxiliaryConnection c = { srcNodeGadget, dstNodeGadget, { srcGadget, dstGadget } };
				m_auxiliaryConnections.insert( c );
			}
		);
		connections.dirty = false;
	}

	m_dirty = false;
}

AuxiliaryConnectionsGadget::SrcNodeGadgetIndex &AuxiliaryConnectionsGadget::srcNodeGadgetIndex() const
{
	return m_auxiliaryConnections.get<1>();
}

AuxiliaryConnectionsGadget::DstNodeGadgetIndex &AuxiliaryConnectionsGadget::dstNodeGadgetIndex() const
{
	return m_auxiliaryConnections.get<2>();
}
