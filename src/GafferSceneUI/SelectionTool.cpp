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

#include "GafferUI/Style.h"
#include "GafferUI/Pointer.h"

#include "GafferScene/ScenePlug.h"

#include "GafferSceneUI/SelectionTool.h"
#include "GafferSceneUI/SceneView.h"

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

		virtual Imath::Box3f bound() const
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
			requestRender();
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
			requestRender();
		}

		const V3f &getEndPosition() const
		{
			return m_endPosition;
		}

	protected :

		virtual void doRender( const Style *style ) const
		{
			if( IECoreGL::Selector::currentSelector() )
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

	private :

		Imath::V3f m_startPosition;
		Imath::V3f m_endPosition;

};

//////////////////////////////////////////////////////////////////////////
// SelectionTool implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( SelectionTool );

SelectionTool::ToolDescription<SelectionTool, SceneView> SelectionTool::g_toolDescription;

SelectionTool::SelectionTool( SceneView *view, const std::string &name )
	:	Tool( view, name ), m_dragOverlay( new DragOverlay() )
{
	SceneGadget *sg = sceneGadget();

	sg->buttonPressSignal().connect( boost::bind( &SelectionTool::buttonPress, this, ::_2 ) );
	sg->dragBeginSignal().connect( boost::bind( &SelectionTool::dragBegin, this, ::_1, ::_2 ) );
	sg->dragEnterSignal().connect( boost::bind( &SelectionTool::dragEnter, this, ::_1, ::_2 ) );
	sg->dragMoveSignal().connect( boost::bind( &SelectionTool::dragMove, this, ::_2 ) );
	sg->dragEndSignal().connect( boost::bind( &SelectionTool::dragEnd, this, ::_2 ) );

	m_dragOverlay->setVisible( false );
	view->viewportGadget()->setChild( "__selectionOverlay", m_dragOverlay );
}

SelectionTool::~SelectionTool()
{
}

SceneGadget *SelectionTool::sceneGadget()
{
	return runTimeCast<SceneGadget>( view()->viewportGadget()->getPrimaryChild() );
}

bool SelectionTool::buttonPress( const GafferUI::ButtonEvent &event )
{
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

	PathMatcher &selection = const_cast<GafferScene::PathMatcherData *>( sg->getSelection() )->writable();

	const bool shiftHeld = event.modifiers && ButtonEvent::Shift;
	bool selectionChanged = false;
	if( !objectUnderMouse.size() )
	{
		// background click - clear the selection unless
		// shift is held in which case we might be starting
		// a drag to add more.
		if( !shiftHeld )
		{
			selection.clear();
			selectionChanged = true;
		}
	}
	else
	{
		const bool objectSelectedAlready = selection.match( objectUnderMouse ) & Filter::ExactMatch;

		if( objectSelectedAlready )
		{
			if( shiftHeld )
			{
				selection.removePath( objectUnderMouse );
				selectionChanged = true;
			}
		}
		else
		{
			if( !shiftHeld )
			{
				selection.clear();
			}
			selection.addPath( objectUnderMouse );
			selectionChanged = true;
		}
	}

	if( selectionChanged )
	{
		transferSelectionToContext();
	}

	return true;
}

IECore::RunTimeTypedPtr SelectionTool::dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	SceneGadget *sg = sceneGadget();
	ScenePlug::ScenePath objectUnderMouse;

	if( !sg->objectAt( event.line, objectUnderMouse ) )
	{
		// drag to select
		m_dragOverlay->setStartPosition( event.line.p0 );
		m_dragOverlay->setEndPosition( event.line.p0 );
		m_dragOverlay->setVisible( true );
		return gadget;
	}
	else
	{
		const PathMatcher &selection = sg->getSelection()->readable();
		if( selection.match( objectUnderMouse ) & Filter::ExactMatch )
		{
			// drag the selection somewhere
			IECore::StringVectorDataPtr dragData = new IECore::StringVectorData();
			selection.paths( dragData->writable() );
			Pointer::setCurrent( "objects" );
			return dragData;
		}
	}
	return NULL;
}

bool SelectionTool::dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
{
	return event.sourceGadget == gadget && event.data == gadget;
}

bool SelectionTool::dragMove( const GafferUI::DragDropEvent &event )
{
	m_dragOverlay->setEndPosition( event.line.p0 );
	return true;
}

bool SelectionTool::dragEnd( const GafferUI::DragDropEvent &event )
{
	Pointer::setCurrent( "" );
	if( !m_dragOverlay->getVisible() )
	{
		return false;
	}

	m_dragOverlay->setVisible( false );

	SceneGadget *sg = sceneGadget();
	PathMatcher &selection = const_cast<GafferScene::PathMatcherData *>( sg->getSelection() )->writable();

	if( sg->objectsAt( m_dragOverlay->getStartPosition(), m_dragOverlay->getEndPosition(), selection ) )
	{
		transferSelectionToContext();
	}

	return true;
}

void SelectionTool::transferSelectionToContext()
{
	StringVectorDataPtr s = new StringVectorData();
	sceneGadget()->getSelection()->readable().paths( s->writable() );
	view()->getContext()->set( "ui:scene:selectedPaths", s.get() );
}
