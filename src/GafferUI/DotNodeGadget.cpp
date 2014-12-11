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

#include "boost/bind.hpp"

#include "Gaffer/Dot.h"
#include "Gaffer/UndoContext.h"
#include "Gaffer/ScriptNode.h"

#include "GafferUI/DotNodeGadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/SpacerGadget.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( DotNodeGadget );

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

	dragEnterSignal().connect( boost::bind( &DotNodeGadget::dragEnter, this, ::_2 ) );
	dropSignal().connect( boost::bind( &DotNodeGadget::drop, this, ::_2 ) );
}

DotNodeGadget::~DotNodeGadget()
{
}

void DotNodeGadget::doRender( const Style *style ) const
{
	Style::State state = getHighlighted() ? Style::HighlightedState : Style::NormalState;

	const Box3f b = bound();
	const V3f s = b.size();
	style->renderFrame( Box2f( V2f( 0 ), V2f( 0 ) ), std::min( s.x, s.y ) / 2.0f, state );

	NodeGadget::doRender( style );
}

Gaffer::Dot *DotNodeGadget::dotNode()
{
	return static_cast<Dot *>( node() );
}

const Gaffer::Dot *DotNodeGadget::dotNode() const
{
	return static_cast<const Dot *>( node() );
}

bool DotNodeGadget::dragEnter( const DragDropEvent &event )
{
	if( dotNode()->inPlug<Plug>() )
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

	V3f tangent = -nodeGadget->noduleTangent( nodule );
	V3f position = ( tangent * bound().size().x / 2.0f ) * fullTransform();
	position = position * event.sourceGadget->fullTransform().inverse();

	if( Nodule *sourceNodule = runTimeCast<Nodule>( event.sourceGadget.get() ) )
	{
		sourceNodule->updateDragEndPoint( position, tangent );
	}
	else if( ConnectionGadget *sourceConnection = runTimeCast<ConnectionGadget>( event.sourceGadget.get() ) )
	{
		sourceConnection->updateDragEndPoint( position, tangent );
	}

	return true;
}

bool DotNodeGadget::drop( const DragDropEvent &event )
{
	if( dotNode()->inPlug<Plug>() )
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

	Gaffer::UndoContext undoEnabler( node()->ancestor<ScriptNode>() );

	dotNode()->setup( plug );
	if( plug->direction() == Plug::In )
	{
		plug->setInput( dotNode()->outPlug<Plug>() );
	}
	else
	{
		dotNode()->inPlug<Plug>()->setInput( plug );
	}

	return true;
}
