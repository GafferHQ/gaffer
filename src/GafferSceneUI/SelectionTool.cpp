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

#include "GafferSceneUI/SelectionTool.h"

#include "GafferSceneUI/ContextAlgo.h"
#include "GafferSceneUI/SceneView.h"

#include "GafferScene/ScenePlug.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"

#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// DragOverlay implementation
//////////////////////////////////////////////////////////////////////////

class SelectionTool::DragOverlay : public GafferUI::Gadget
{

	public :

		DragOverlay()
			:	Gadget()
		{
		}

		Imath::Box3f bound() const override
		{
			// we draw in raster space so don't have a sensible bound
			return Box3f();
		}

		void setStartPosition( const V3f &p )
		{
			if( m_startPosition == p )
			{
				return;
			}
			m_startPosition = p;
			dirty( DirtyType::Render );
		}

		const V3f &getStartPosition() const
		{
			return m_startPosition;
		}

		void setEndPosition( const V3f &p )
		{
			if( m_endPosition == p )
			{
				return;
			}
			m_endPosition = p;
			dirty( DirtyType::Render );
		}

		const V3f &getEndPosition() const
		{
			return m_endPosition;
		}

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			assert( layer == Layer::MidFront );

			if( isSelectionRender( reason ) )
			{
				return;
			}

			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			ViewportGadget::RasterScope rasterScope( viewportGadget );

			Box2f b;
			b.extendBy( viewportGadget->gadgetToRasterSpace( m_startPosition, this ) );
			b.extendBy( viewportGadget->gadgetToRasterSpace( m_endPosition, this ) );

			style->renderSelectionBox( b );
		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::MidFront;
		}

		Imath::Box3f renderBound() const override
		{
			// we draw in raster space so don't have a sensible bound
			Box3f b;
			b.makeInfinite();
			return b;
		}

	private :

		Imath::V3f m_startPosition;
		Imath::V3f m_endPosition;

};

//////////////////////////////////////////////////////////////////////////
// SelectionTool implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( SelectionTool );

SelectionTool::ToolDescription<SelectionTool, SceneView> SelectionTool::g_toolDescription;
static IECore::InternedString g_dragOverlayName( "__selectionToolDragOverlay" );

SelectionTool::SelectionTool( SceneView *view, const std::string &name )
	:	Tool( view, name )
{
	SceneGadget *sg = sceneGadget();

	sg->buttonPressSignal().connect( boost::bind( &SelectionTool::buttonPress, this, ::_2 ) );
	sg->buttonReleaseSignal().connect( boost::bind( &SelectionTool::buttonRelease, this, ::_2 ) );
	sg->dragBeginSignal().connect( boost::bind( &SelectionTool::dragBegin, this, ::_1, ::_2 ) );
	sg->dragEnterSignal().connect( boost::bind( &SelectionTool::dragEnter, this, ::_1, ::_2 ) );
	sg->dragMoveSignal().connect( boost::bind( &SelectionTool::dragMove, this, ::_2 ) );
	sg->dragEndSignal().connect( boost::bind( &SelectionTool::dragEnd, this, ::_2 ) );
}

SelectionTool::~SelectionTool()
{
}

SceneGadget *SelectionTool::sceneGadget()
{
	return runTimeCast<SceneGadget>( view()->viewportGadget()->getPrimaryChild() );
}

SelectionTool::DragOverlay *SelectionTool::dragOverlay()
{
	// All instances of SelectionTool share a single drag overlay - this
	// allows SelectionTool to be subclassed for the creation of other tools.
	DragOverlay *result = view()->viewportGadget()->getChild<DragOverlay>( g_dragOverlayName );
	if( !result )
	{
		result = new DragOverlay;
		view()->viewportGadget()->setChild( g_dragOverlayName, result );
		result->setVisible( false );
	}
	return result;
}

bool SelectionTool::buttonPress( const GafferUI::ButtonEvent &event )
{
	m_acceptedButtonPress = false;
	m_initiatedDrag = false;

	if( event.buttons != ButtonEvent::Left )
	{
		return false;
	}

	if( !activePlug()->getValue() )
	{
		return false;
	}

	SceneGadget *sg = sceneGadget();
	ScenePlug::ScenePath objectUnderMouse;
	sg->objectAt( event.line, objectUnderMouse );

	PathMatcher selection = sg->getSelection();

	const bool shiftHeld = event.modifiers & ButtonEvent::Shift;
	const bool controlHeld = event.modifiers & ButtonEvent::Control;
	if( !objectUnderMouse.size() )
	{
		// background click - clear the selection unless a modifier is held, in
		// which case we might be starting a drag to add more or remove some.
		if( !shiftHeld && !controlHeld )
		{
			ContextAlgo::setSelectedPaths( view()->getContext(), IECore::PathMatcher() );
		}
	}
	else
	{
		const bool objectSelectedAlready = selection.match( objectUnderMouse ) & PathMatcher::ExactMatch;

		if( objectSelectedAlready )
		{
			if( controlHeld )
			{
				selection.removePath( objectUnderMouse );
				ContextAlgo::setSelectedPaths( view()->getContext(), selection );
			}
		}
		else
		{
			if( !controlHeld && !shiftHeld )
			{
				ContextAlgo::setSelectedPaths( view()->getContext(), IECore::PathMatcher() );
			}
			ContextAlgo::setLastSelectedPath( view()->getContext(), objectUnderMouse );
		}
	}

	m_acceptedButtonPress = true;
	return true;
}

bool SelectionTool::buttonRelease( const GafferUI::ButtonEvent &event )
{
	m_acceptedButtonPress = false;
	m_initiatedDrag = false;
	return false;
}

IECore::RunTimeTypedPtr SelectionTool::dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	// Derived classes may wish to override the handling of buttonPress. To
	// consume the event, they must return true from it. This also tells the
	// drag system that they may wish to start a drag later, and so it will
	// then call 'dragBegin'. If they have no interest in actually performing
	// a drag (as maybe they just wanted to do something on click) this is a
	// real pain as now they also have to implement dragBegin to prevent the
	// code below from doing its thing. To avoid this boilerplate overhead,
	// we only start our own drag if we know we were the one who returned
	// true from buttonPress. We also track whether we initiated a drag so
	// the other drag methods can early-out accordingly.
	m_initiatedDrag = false;
	if( !m_acceptedButtonPress )
	{
		return nullptr;
	}
	m_acceptedButtonPress = false;

	SceneGadget *sg = sceneGadget();
	ScenePlug::ScenePath objectUnderMouse;

	if( !sg->objectAt( event.line, objectUnderMouse ) )
	{
		// drag to select
		dragOverlay()->setStartPosition( event.line.p1 );
		dragOverlay()->setEndPosition( event.line.p1 );
		dragOverlay()->setVisible( true );
		m_initiatedDrag = true;
		return gadget;
	}
	else
	{
		const PathMatcher &selection = sg->getSelection();
		if( selection.match( objectUnderMouse ) & PathMatcher::ExactMatch )
		{
			// drag the selection somewhere
			IECore::StringVectorDataPtr dragData = new IECore::StringVectorData();
			selection.paths( dragData->writable() );
			Pointer::setCurrent( "objects" );
			m_initiatedDrag = true;
			return dragData;
		}
	}
	return nullptr;
}

bool SelectionTool::dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	return m_initiatedDrag && event.sourceGadget == gadget && event.data == gadget;
}

bool SelectionTool::dragMove( const GafferUI::DragDropEvent &event )
{
	if( !m_initiatedDrag )
	{
		return false;
	}

	dragOverlay()->setEndPosition( event.line.p1 );
	return true;
}

bool SelectionTool::dragEnd( const GafferUI::DragDropEvent &event )
{
	if( !m_initiatedDrag )
	{
		return false;
	}

	Pointer::setCurrent( "" );
	if( !dragOverlay()->getVisible() )
	{
		return false;
	}

	dragOverlay()->setVisible( false );

	SceneGadget *sg = sceneGadget();
	PathMatcher selection = sg->getSelection();
	PathMatcher inDragRegion;

	if( sg->objectsAt( dragOverlay()->getStartPosition(), dragOverlay()->getEndPosition(), inDragRegion ) )
	{
		if( event.modifiers & DragDropEvent::Control )
		{
			selection.removePaths( inDragRegion );
		}
		else
		{
			selection.addPaths( inDragRegion );
		}

		ContextAlgo::setSelectedPaths( view()->getContext(), selection );
	}

	return true;
}
