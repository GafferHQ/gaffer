//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/PlugAdder.h"

#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/ImageGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/Style.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/UndoScope.h"
#include "Gaffer/ScriptNode.h"

#include "IECoreGL/Selector.h"
#include "IECoreGL/Texture.h"

#include "boost/bind/bind.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const IECoreGL::Texture *texture( Style::State state )
{
	static IECoreGL::ConstTexturePtr normalTexture = ImageGadget::loadTexture( "plugAdder.png" );
	static IECoreGL::ConstTexturePtr highlightedTexture = ImageGadget::loadTexture( "plugAdderHighlighted.png" );
	return state == Style::HighlightedState ? highlightedTexture.get() : normalTexture.get();
}

V3f tangent( const PlugAdder *g )
{
	const NodeGadget *ng = g->ancestor<NodeGadget>();
	return ng ? ng->connectionTangent( g ) : V3f( 0 );
}

StandardNodeGadget::Edge tangentEdge( const V3f &tangent )
{
	auto tangents = {
		make_pair( V3f( 0, 1, 0 ), StandardNodeGadget::TopEdge ),
		make_pair( V3f( 0, -1, 0 ), StandardNodeGadget::BottomEdge ),
		make_pair( V3f( -1, 0, 0 ), StandardNodeGadget::LeftEdge ),
		make_pair( V3f( 1, 0, 0 ), StandardNodeGadget::RightEdge )
	};

	for( const auto &t : tangents )
	{
		if( tangent.dot( t.first ) > 0.9 )
		{
			return t.second;
		}
	}

	return StandardNodeGadget::TopEdge;
}

StandardNodeGadget::Edge oppositeEdge( StandardNodeGadget::Edge edge )
{
	switch( edge )
	{
		case StandardNodeGadget::TopEdge :
			return StandardNodeGadget::BottomEdge;
		case StandardNodeGadget::BottomEdge :
			return StandardNodeGadget::TopEdge;
		case StandardNodeGadget::LeftEdge :
			return StandardNodeGadget::RightEdge;
		default :
			return StandardNodeGadget::LeftEdge;
	}
}

const char *edgeName( StandardNodeGadget::Edge edge )
{
	switch( edge )
	{
		case StandardNodeGadget::TopEdge :
			return "top";
		case StandardNodeGadget::BottomEdge :
			return "bottom";
		case StandardNodeGadget::LeftEdge :
			return "left";
		default :
			return "right";
	}
}

void updateMetadata( Plug *plug, InternedString key, const char *value )
{
	ConstStringDataPtr s = Metadata::value<StringData>( plug, key );
	if( s && s->readable() == value )
	{
		// Metadata already has the value we want. No point adding on
		// an instance override with the exact same value.
		return;
	}

	Metadata::registerValue( plug, key, new StringData( value ) );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// PlugAdder
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( PlugAdder );

PlugAdder::PlugAdder()
	:	m_dragging( false )
{
	enterSignal().connect( boost::bind( &PlugAdder::enter, this, ::_1, ::_2 ) );
	leaveSignal().connect( boost::bind( &PlugAdder::leave, this, ::_1, ::_2 ) );
	buttonPressSignal().connect( boost::bind( &PlugAdder::buttonPress, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &PlugAdder::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &PlugAdder::dragEnter, this, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &PlugAdder::dragMove, this, ::_1, ::_2 ) );
	dragLeaveSignal().connect( boost::bind( &PlugAdder::dragLeave, this, ::_2 ) );
	dropSignal().connect( boost::bind( &PlugAdder::drop, this, ::_2 ) );
	dragEndSignal().connect( boost::bind( &PlugAdder::dragEnd, this, ::_2 ) );
}

PlugAdder::~PlugAdder()
{
}

Imath::Box3f PlugAdder::bound() const
{
	return Box3f( V3f( -0.5f, -0.5f, 0.0f ), V3f( 0.5f, 0.5f, 0.0f ) );
}

bool PlugAdder::canCreateConnection( const Gaffer::Plug *endpoint ) const
{
	if( endpoint->direction() == Plug::In && MetadataAlgo::readOnly( endpoint ) )
	{
		return false;
	}

	ConstStringDataPtr noduleType = Gaffer::Metadata::value<StringData>( endpoint, IECore::InternedString( "nodule:type" ) );
	if( noduleType )
	{
		if( noduleType->readable() == "GafferUI::CompoundNodule" )
		{
			return false;
		}
	}

	return true;
}

void PlugAdder::updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent )
{
	m_dragPosition = position;
	m_dragTangent = tangent;
	m_dragging = true;
	dirty( DirtyType::Render );
}

PlugAdder::PlugMenuSignal &PlugAdder::plugMenuSignal()
{
	static PlugMenuSignal *s = new PlugMenuSignal;
	return *s;
}

PlugAdder::MenuSignal &PlugAdder::menuSignal()
{
	static MenuSignal *s = new MenuSignal;
	return *s;
}

void PlugAdder::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	switch( layer )
	{
		case GraphLayer::Connections :
			if( m_dragging )
			{
				if( !isSelectionRender( reason ) )
				{
					const V3f srcTangent = tangent( this );
					style->renderConnection( V3f( 0 ), srcTangent, m_dragPosition, m_dragTangent, Style::HighlightedState );
				}
			}
			break;
		case GraphLayer::Nodes :
			if( !getHighlighted() )
			{
				const float radius = 0.75f;
				style->renderImage( Box2f( V2f( -radius ), V2f( radius ) ), texture( Style::NormalState ) );
			}
			break;
		case GraphLayer::Highlighting :
			if( getHighlighted() )
			{
				const float radius = 1.25f;
				style->renderImage( Box2f( V2f( -radius ), V2f( radius ) ), texture( Style::HighlightedState ) );
			}
			break;
		default:
			break;
	}
}

unsigned PlugAdder::layerMask() const
{
	return GraphLayer::Connections | GraphLayer::Nodes | GraphLayer::Highlighting;
}

Imath::Box3f PlugAdder::renderBound() const
{
	return bound();
}

void PlugAdder::applyEdgeMetadata( Gaffer::Plug *plug, bool opposite ) const
{
	const StandardNodeGadget::Edge edge = tangentEdge( tangent( this ) );
	updateMetadata( plug, "noduleLayout:section", edgeName( opposite ? oppositeEdge( edge ) : edge ) );
}

bool PlugAdder::couldCreateConnection() const
{
	// We actually have no idea which parent the plug will be added to -
	// that is known only by subclasses. But when it is read-only, we want to
	// avoid starting or accepting drags, because they will only end in
	// disappointment. Subclasses do consider their own read-onliness in
	// `canCreateConnection()`, but we can't call that until we've got a plug
	// to pass to it. We want to know if we could _ever_ create a connection
	// given the right plug. The best we can do right now is to cover the most
	// common case, where the root node in the GraphGadget is read-only, making
	// it impossible to edit _anything_ within.
	//
	/// \todo Extend the API so that we can detect the case where only the specific node
	/// the plug will be added to is read-only. Perhaps we could could just pass
	/// `nullptr` to `canCreateConnection()` since it should be checking read-onliness
	/// already?
	if( auto graphGadget = ancestor<GraphGadget>() )
	{
		if( Gaffer::MetadataAlgo::readOnly( graphGadget->getRoot() ) )
		{
			return false;
		}
	}
	return true;
}

void PlugAdder::enter( GadgetPtr gadget, const ButtonEvent &event )
{
	if( couldCreateConnection() )
	{
		setHighlighted( true );
	}
}

void PlugAdder::leave( GadgetPtr gadget, const ButtonEvent &event )
{
	setHighlighted( false );
}

bool PlugAdder::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	return event.buttons == ButtonEvent::Left;
}

IECore::RunTimeTypedPtr PlugAdder::dragBegin( GadgetPtr gadget, const ButtonEvent &event )
{
	return couldCreateConnection() ? this : nullptr;
}

bool PlugAdder::dragEnter( const DragDropEvent &event )
{
	if( event.buttons != DragDropEvent::Left )
	{
		return false;
	}

	if( event.sourceGadget == this )
	{
		updateDragEndPoint( V3f( event.line.p0.x, event.line.p0.y, 0 ), V3f( 0 ) );
		return true;
	}

	const Plug *plug = runTimeCast<Plug>( event.data.get() );
	if( !plug || !canCreateConnection( plug ) )
	{
		return false;
	}

	setHighlighted( true );

	if( auto connectionCreator = runTimeCast<ConnectionCreator>( event.sourceGadget.get() ) )
	{
		V3f center = V3f( 0.0f ) * fullTransform();
		center = center * connectionCreator->fullTransform().inverse();
		connectionCreator->updateDragEndPoint( center, tangent( this ) );
	}

	return true;
}

bool PlugAdder::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	m_dragPosition = V3f( event.line.p0.x, event.line.p0.y, 0 );
	dirty( DirtyType::Render );
	return true;
}

bool PlugAdder::dragLeave( const DragDropEvent &event )
{
	setHighlighted( false );
	return true;
}

bool PlugAdder::drop( const DragDropEvent &event )
{
	setHighlighted( false );

	if( Plug *plug = runTimeCast<Plug>( event.data.get() ) )
	{
		UndoScope undoScope( plug->ancestor<ScriptNode>() );
		createConnection( plug );
		return true;
	}

	return false;
}

bool PlugAdder::dragEnd( const DragDropEvent &event )
{
	m_dragging = false;
	dirty( DirtyType::Render );
	return false;
}
