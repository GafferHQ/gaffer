//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/DotNodeGadget.h"

#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/SpacerGadget.h"
#include "GafferUI/Style.h"

#include "Gaffer/Dot.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/UndoScope.h"

#include "IECoreGL/GL.h"

#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( DotNodeGadget );

DotNodeGadget::NodeGadgetTypeDescription<DotNodeGadget> DotNodeGadget::g_nodeGadgetTypeDescription( Gaffer::Dot::staticTypeId() );

DotNodeGadget::DotNodeGadget( Gaffer::NodePtr node )
	:	StandardNodeGadget( node )
{
	if( !runTimeCast<Dot>( node ) )
	{
		throw Exception( "DotNodeGadget requires a Dot" );
	}

	// Set the contents to have a small size, so the size of the Dot is controlled
	// largely by the nodeGadget:padding Metadata.
	setContents( new SpacerGadget( Box3f( V3f( -0.25 ), V3f( 0.25 ) ) ) );

	node->plugDirtiedSignal().connect( boost::bind( &DotNodeGadget::plugDirtied, this, ::_1 ) );
	node->nameChangedSignal().connect( boost::bind( &DotNodeGadget::nameChanged, this, ::_1 ) );

	dragEnterSignal().connect( boost::bind( &DotNodeGadget::dragEnter, this, ::_2 ) );
	dropSignal().connect( boost::bind( &DotNodeGadget::drop, this, ::_2 ) );

	updateUpstreamNameChangedConnection();
	updateLabel();
}

DotNodeGadget::~DotNodeGadget()
{
}

Box3f DotNodeGadget::bound() const
{
	// Take base class bound, but make it square, since we always render as a perfect circle
	Box3f b = StandardNodeGadget::bound();
	const V3f s = b.size();
	V3f c = b.center();
	const float radius = std::min( s.x, s.y ) / 2.0f;
	V3f offset( radius, radius, 0.0f );
	return Box3f( c - offset, c + offset );
}

void DotNodeGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	StandardNodeGadget::renderLayer( layer, style, reason );

	if( layer != GraphLayer::Nodes )
	{
		if( !m_label.empty() && !isSelectionRender( reason ) )
		{
			glPushMatrix();
			IECoreGL::glTranslate( m_labelPosition );
			style->renderText( Style::LabelText, m_label );
			glPopMatrix();
		}
	}
}

Gaffer::Dot *DotNodeGadget::dotNode()
{
	return static_cast<Dot *>( node() );
}

const Gaffer::Dot *DotNodeGadget::dotNode() const
{
	return static_cast<const Dot *>( node() );
}

Gaffer::Node *DotNodeGadget::upstreamNode()
{
	Plug *plug = dotNode()->inPlug();
	while( plug && runTimeCast<Dot>( plug->node() ) )
	{
		plug = plug->getInput();
	}
	return plug ? plug->node() : nullptr;
}

void DotNodeGadget::plugDirtied( const Gaffer::Plug *plug )
{
	const Dot *dot = dotNode();
	if( plug == dot->labelTypePlug() || plug == dot->labelPlug() )
	{
		updateLabel();
	}
	else if( plug == dot->inPlug() )
	{
		updateUpstreamNameChangedConnection();
		updateLabel();
	}
}

void DotNodeGadget::nameChanged( const Gaffer::GraphComponent *graphComponent )
{
	updateLabel();
}

void DotNodeGadget::updateUpstreamNameChangedConnection()
{
	m_upstreamNameChangedConnection.disconnect();
	if( Node *n = upstreamNode() )
	{
		m_upstreamNameChangedConnection = n->nameChangedSignal().connect( boost::bind( &DotNodeGadget::nameChanged, this, ::_1 ) );
	}
}

void DotNodeGadget::updateLabel()
{
	const Dot *dot = dotNode();

	try
	{
		const Dot::LabelType labelType = (Dot::LabelType)dot->labelTypePlug()->getValue();
		if( labelType == Dot::None )
		{
			m_label.clear();
		}
		else if( labelType == Dot::NodeName )
		{
			m_label = dot->getName();
		}
		else if( labelType == Dot::UpstreamNodeName )
		{
			const Node *n = upstreamNode();
			m_label = n ? n->getName() : "";
		}
		else
		{
			const auto script = dot->scriptNode();
			const Context *context = script ? script->context() : nullptr;
			Context::Scope scope( context );
			m_label = dot->labelPlug()->getValue();
			if( context )
			{
				m_label = context->substitute( m_label );
			}
		}
	}
	catch( const Gaffer::ProcessException &e )
	{
		m_label = "Error";
	}

	Edge labelEdge = RightEdge;
	if( const Plug *p = dot->inPlug() )
	{
		if( connectionTangent( nodule( p ) ).x != 0 )
		{
			labelEdge = TopEdge;
		}
	}

	const Imath::Box3f thisBound = bound();
	if( labelEdge == TopEdge )
	{
		const Imath::Box3f labelBound = style()->textBound( Style::LabelText, m_label );
		m_labelPosition = V2f(
			-labelBound.size().x / 2.0,
			thisBound.max.y + 1.0
		);
	}
	else
	{
		const Imath::Box3f characterBound = style()->characterBound( Style::LabelText );
		m_labelPosition = V2f(
			thisBound.max.x,
			thisBound.center().y - characterBound.size().y / 2.0
		);
	}

	dirty( DirtyType::Render );
}

bool DotNodeGadget::dragEnter( const DragDropEvent &event )
{
	if( MetadataAlgo::readOnly( dotNode() ) )
	{
		return false;
	}

	if( dotNode()->inPlug() )
	{
		// We've already got our plugs set up - StandardNodeGadget
		// behaviour will take care of everything.
		return false;
	}

	const Plug *plug = runTimeCast<Plug>( event.data.get() );
	if( !plug )
	{
		return false;
	}

	const GraphGadget *graphGadget = ancestor<GraphGadget>();
	if( !graphGadget )
	{
		return false;
	}

	const NodeGadget *nodeGadget = graphGadget->nodeGadget( plug->node() );
	if( !nodeGadget )
	{
		return false;
	}

	const Nodule *nodule = nodeGadget->nodule( plug );
	if( !nodule )
	{
		return false;
	}

	if( auto connectionCreator = runTimeCast<ConnectionCreator>( event.sourceGadget.get() ) )
	{
		V3f tangent = -nodeGadget->connectionTangent( nodule );
		V3f position = ( tangent * bound().size().x / 2.0f ) * fullTransform();
		position = position * connectionCreator->fullTransform().inverse();
		connectionCreator->updateDragEndPoint( position, tangent );
	}

	return true;
}

bool DotNodeGadget::drop( const DragDropEvent &event )
{
	if( dotNode()->inPlug() )
	{
		// We've already got our plugs set up - StandardNodeGadget
		// behaviour will take care of everything.
		return false;
	}

	Plug *plug = runTimeCast<Plug>( event.data.get() );
	if( !plug )
	{
		return false;
	}

	Gaffer::UndoScope undoEnabler( node()->ancestor<ScriptNode>() );

	dotNode()->setup( plug );
	if( plug->direction() == Plug::In )
	{
		plug->setInput( dotNode()->outPlug() );
	}
	else
	{
		dotNode()->inPlug()->setInput( plug );
	}

	return true;
}
