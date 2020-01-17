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

#include "GafferSceneUI/CropWindowTool.h"

#include "GafferSceneUI/SceneView.h"

#include "GafferScene/Options.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"

#include "Gaffer/BlockedConnection.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/UndoScope.h"

#include "IECore/NullObject.h"

#include "boost/bind.hpp"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Overlay implementation
//////////////////////////////////////////////////////////////////////////

/// \todo This should become a public public class that
/// could be reused in other tools. The main obstacle
/// to that is that this is hardcoded to work in raster
/// space - see comments in doRender() for ideas as to
/// how we could avoid that.
class CropWindowTool::Rectangle : public GafferUI::Gadget
{

	public :

		enum RectangleChangedReason
		{
			Invalid,
			SetBound,
			DragBegin,
			DragMove,
			DragEnd
		};

		Rectangle()
			:	Gadget(), m_editable( true ), m_masked( false ), m_xDragEdge( 0 ), m_yDragEdge( 0 )
		{
			mouseMoveSignal().connect( boost::bind( &Rectangle::mouseMove, this, ::_2 ) );
			buttonPressSignal().connect( boost::bind( &Rectangle::buttonPress, this, ::_2 ) );
			dragBeginSignal().connect( boost::bind( &Rectangle::dragBegin, this, ::_1, ::_2 ) );
			dragEnterSignal().connect( boost::bind( &Rectangle::dragEnter, this, ::_1, ::_2 ) );
			dragMoveSignal().connect( boost::bind( &Rectangle::dragMove, this, ::_2 ) );
			dragEndSignal().connect( boost::bind( &Rectangle::dragEnd, this, ::_2 ) );
			leaveSignal().connect( boost::bind( &Rectangle::leave, this ) );
		}

		Imath::Box3f bound() const override
		{
			// We draw in raster space so don't have a sensible bound
			return Box3f();
		}

		void setRectangle( const Imath::Box2f &rectangle )
		{
			setRectangleInternal( rectangle, SetBound );
		}

		const Imath::Box2f &getRectangle() const
		{
			return m_rectangle;
		}

		void setEditable( bool editable )
		{
			m_editable = editable;
		}

		bool getEditable() const
		{
			return m_editable;
		}

		void setMasked( bool masked )
		{
			if( m_masked == masked )
			{
				return;
			}
			m_masked = masked;
			requestRender();
		}

		bool getMasked() const
		{
			return m_masked;
		}

		typedef boost::signal<void ( Rectangle *, RectangleChangedReason )> UnarySignal;
		UnarySignal &rectangleChangedSignal()
		{
			return m_rectangleChangedSignal;
		}

		void setCaption( const std::string &caption )
		{
			if( caption == m_caption )
			{
				return;
			}
			m_caption = caption;
			requestRender();
		}

		const std::string &getCaption() const
		{
			return m_caption;
		}

	protected :

		void doRenderLayer( Layer layer, const Style *style ) const override
		{
			if( layer != Layer::Main )
			{
				return;
			}

			if( m_rectangle.isEmpty() )
			{
				return;
			}

			/// \todo Would it make sense for the ViewportGadget to have a way
			/// of adding a child as an overlay, so we didn't have to do the
			/// raster scope bit manually? Maybe that would let us write more reusable
			/// gadgets, which could be used in any space, and we wouldn't need
			/// eventPosition().
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			ViewportGadget::RasterScope rasterScope( viewportGadget );

			glPushAttrib( GL_CURRENT_BIT | GL_LINE_BIT | GL_ENABLE_BIT );

				if( IECoreGL::Selector::currentSelector() )
				{
					if( m_editable )
					{
						style->renderSolidRectangle( m_rectangle );
					}
				}
				else
				{
					if( m_masked )
					{
						glColor4f( 0.0f, 0.0f, 0.0f, 0.5f );
						style->renderSolidRectangle( Box2f(
							V2f( m_rectangle.min.x - 100000, m_rectangle.min.y ),
							V2f( m_rectangle.max.x + 100000, m_rectangle.min.y - 100000 )
						) );
						style->renderSolidRectangle( Box2f(
							V2f( m_rectangle.min.x - 100000, m_rectangle.max.y ),
							V2f( m_rectangle.max.x + 100000, m_rectangle.max.y + 100000 )
						) );
						style->renderSolidRectangle( Box2f(
							V2f( m_rectangle.min.x - 100000, m_rectangle.min.y ),
							V2f( m_rectangle.min.x, m_rectangle.max.y )
						) );
						style->renderSolidRectangle( Box2f(
							V2f( m_rectangle.max.x, m_rectangle.min.y ),
							V2f( m_rectangle.max.x + 100000, m_rectangle.max.y )
						) );
					}

					glEnable( GL_LINE_SMOOTH );
					glLineWidth( 2.5f );
					glColor4f( 1.0f, 0.33f, 0.33f, 1.0f );
					style->renderRectangle( m_rectangle );

					if( m_caption.size() )
					{
						glPushMatrix();

							glTranslatef( m_rectangle.min.x + 5, m_rectangle.max.y + 10, 0.0f );
							glScalef( 10.0f, -10.0f, 10.0f );
							style->renderText( Style::LabelText, m_caption );

						glPopMatrix();
					}
				}

			glPopAttrib();

		}

	private :

		void setRectangleInternal( const Imath::Box2f &rectangle, RectangleChangedReason reason )
		{
			if( reason != DragBegin && reason != DragEnd && rectangle == m_rectangle )
			{
				// Early out if the value isn't changing. We never early out
				// for DragBegin or DragEnd because we want to always signal
				// those so a complete begin/move/end sequence is always
				// available.
				return;
			}
			m_rectangle = rectangle;
			rectangleChangedSignal()( this, reason );
			requestRender();
		}

		bool mouseMove( const ButtonEvent &event )
		{
			int x, y;
			hoveredEdges( event, x, y );
			if( x && y )
			{
				Pointer::setCurrent( x * y > 0 ? "moveDiagonallyDown" : "moveDiagonallyUp" );
			}
			else if( x )
			{
				Pointer::setCurrent( "moveHorizontally" );
			}
			else if( y )
			{
				Pointer::setCurrent( "moveVertically" );
			}
			else
			{
				Pointer::setCurrent( "" );
			}
			return false;
		}

		bool buttonPress( const GafferUI::ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left )
			{
				return false;
			}

			hoveredEdges( event, m_xDragEdge, m_yDragEdge );
			return m_xDragEdge || m_yDragEdge;
		}

		IECore::RunTimeTypedPtr dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			m_dragStartRectangle = m_rectangle;
			return IECore::NullObject::defaultNullObject();
		}

		bool dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			if( gadget != this )
			{
				return false;
			}

			updateDragRectangle( event, DragBegin );
			return true;
		}

		bool dragMove( const GafferUI::DragDropEvent &event )
		{
			updateDragRectangle( event, DragMove );
			return true;
		}

		bool dragEnd( const GafferUI::DragDropEvent &event )
		{
			updateDragRectangle( event, DragEnd );
			return true;
		}

		void updateDragRectangle( const GafferUI::DragDropEvent &event, RectangleChangedReason reason )
		{
			const V2f p = eventPosition( event );
			Box2f b = m_dragStartRectangle;
			if( m_xDragEdge == -1 )
			{
				b.min.x = p.x;
			}
			else if( m_xDragEdge == 1 )
			{
				b.max.x = p.x;
			}

			if( m_yDragEdge == -1 )
			{
				b.min.y = p.y;
			}
			else if( m_yDragEdge == 1 )
			{
				b.max.y = p.y;
			}

			// fix max < min issues
			Box2f c;
			c.extendBy( b.min );
			c.extendBy( b.max );

			setRectangleInternal( c, reason );
		}

		void leave()
		{
			Pointer::setCurrent( "" );
		}

		void hoveredEdges( const ButtonEvent &event, int &x, int &y ) const
		{
			const float threshold = 10;
			x = y = 0;

			const V2f p = eventPosition( event );

			const float xMinDelta = fabs( p.x - m_rectangle.min.x );
			const float xMaxDelta = fabs( p.x - m_rectangle.max.x );
			if( xMinDelta < xMaxDelta && xMinDelta < threshold )
			{
				x = -1;
			}
			else if( xMaxDelta < threshold )
			{
				x = 1;
			}

			const float yMinDelta = fabs( p.y - m_rectangle.min.y );
			const float yMaxDelta = fabs( p.y - m_rectangle.max.y );
			if( yMinDelta < yMaxDelta && yMinDelta < threshold )
			{
				y = -1;
			}
			else if( yMaxDelta < threshold )
			{
				y = 1;
			}
		}

		V2f eventPosition( const ButtonEvent &event ) const
		{
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			return viewportGadget->gadgetToRasterSpace( event.line.p1, this );
		}

		Imath::Box2f m_rectangle;
		UnarySignal m_rectangleChangedSignal;

		std::string m_caption;

		bool m_editable;
		bool m_masked;

		Imath::Box2f m_dragStartRectangle;
		int m_xDragEdge;
		int m_yDragEdge;

};

//////////////////////////////////////////////////////////////////////////
// CropWindowTool implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CropWindowTool );

size_t CropWindowTool::g_firstPlugIndex = 0;
CropWindowTool::ToolDescription<CropWindowTool, SceneView> CropWindowTool::g_toolDescription;

CropWindowTool::CropWindowTool( SceneView *view, const std::string &name )
	:	Tool( view, name ), m_needCropWindowPlugSearch( true ), m_overlayDirty( true ), m_overlay( new Rectangle() )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "__scene", Plug::In ) );
	scenePlug()->setInput( view->inPlug<ScenePlug>() );

	m_overlay->setVisible( false );
	m_overlay->setMasked( true );
	view->viewportGadget()->setChild( "__cropWindowOverlay", m_overlay );
	m_overlayRectangleChangedConnection = m_overlay->rectangleChangedSignal().connect( boost::bind( &CropWindowTool::overlayRectangleChanged, this, ::_2 ) );

	view->viewportGadget()->viewportChangedSignal().connect( boost::bind( &CropWindowTool::viewportChanged, this ) );
	view->viewportGadget()->preRenderSignal().connect( boost::bind( &CropWindowTool::preRender, this ) );
	plugDirtiedSignal().connect( boost::bind( &CropWindowTool::plugDirtied, this, ::_1 ) );

	Metadata::plugValueChangedSignal().connect( boost::bind( &CropWindowTool::metadataChanged, this, ::_3 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &CropWindowTool::metadataChanged, this, ::_2 ) );
}

CropWindowTool::~CropWindowTool()
{
}

GafferScene::ScenePlug *CropWindowTool::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *CropWindowTool::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

void CropWindowTool::viewportChanged()
{
	m_overlayDirty = true;
}

void CropWindowTool::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == activePlug() )
	{
		m_overlay->setVisible( activePlug()->getValue() );
		m_needCropWindowPlugSearch = m_overlayDirty = true;
	}
	else if( plug == scenePlug()->globalsPlug() )
	{
		m_needCropWindowPlugSearch = m_overlayDirty = true;
	}
	else if( plug == m_cropWindowPlug || plug == m_cropWindowEnabledPlug )
	{
		m_overlayDirty = true;
	}
}

void CropWindowTool::metadataChanged( IECore::InternedString key )
{
	if( !MetadataAlgo::readOnlyAffectedByChange( key ) || m_needCropWindowPlugSearch )
	{
		return;
	}

	m_needCropWindowPlugSearch = m_overlayDirty = true;
	view()->viewportGadget()->renderRequestSignal()(
		view()->viewportGadget()
	);
}

void CropWindowTool::overlayRectangleChanged( unsigned reason )
{
	if( !m_cropWindowPlug )
	{
		return;
	}

	if( reason != Rectangle::DragEnd )
	{
		// BoxPlug doesn't currently support the merging of undo events,
		// so we only set the value on drag end to avoid creating a whole
		// series of undo events.
		/// \todo Implement undo merging for BoxPlug, and set the value
		/// for all changes. This will fix the slightly annoying behaviour
		/// where the crop window can be dragged out of the 0-1 range and
		/// only snaps back at drag end. Once we've done this, we could
		/// also simplify our logic by removing m_overlayDirty and just
		/// unconditionally doing everything in preRender(). Updating the
		/// overlay is a quick operation, and the only real reason we have
		/// m_overlayDirty is so that we don't update during a drag, when
		/// the plugs don't currently reflect the dragged value.
		return;
	}

	Box2f b = m_overlay->getRectangle();
	Box2f resolutionGate = static_cast<SceneView *>( view() )->resolutionGate();
	b = Box2f(
		V2f(
			lerpfactor( b.min.x, resolutionGate.min.x, resolutionGate.max.x ),
			lerpfactor( b.min.y, resolutionGate.min.y, resolutionGate.max.y )
		),
		V2f(
			lerpfactor( b.max.x, resolutionGate.min.x, resolutionGate.max.x ),
			lerpfactor( b.max.y, resolutionGate.min.y, resolutionGate.max.y )
		)
	);

	UndoScope undoScope( m_cropWindowPlug->ancestor<ScriptNode>() );

	if( m_cropWindowEnabledPlug && !m_cropWindowEnabledPlug->getValue() )
	{
		m_cropWindowEnabledPlug->setValue( true );
	}

	m_cropWindowPlug->setValue( b );
	m_overlayDirty = true;
}

void CropWindowTool::preRender()
{
	const Box2f resolutionGate = static_cast<SceneView *>( view() )->resolutionGate();
	if( resolutionGate.isEmpty() )
	{
		m_overlay->setVisible( false );
		return;
	}

	if( !activePlug()->getValue() )
	{
		return;
	}

	m_overlay->setVisible( true );

	if( !m_overlayDirty )
	{
		return;
	}

	Box2f cropWindow( V2f( 0 ), V2f( 1 ) );
	findCropWindowPlug();
	if( m_cropWindowPlug )
	{
		cropWindow = m_cropWindowPlug->getValue();
	}

	BlockedConnection blockedConnection( m_overlayRectangleChangedConnection );
	m_overlay->setRectangle(
		Box2f(
			V2f(
				lerp( resolutionGate.min.x, resolutionGate.max.x, cropWindow.min.x ),
				lerp( resolutionGate.min.y, resolutionGate.max.y, cropWindow.min.y )
			),
			V2f(
				lerp( resolutionGate.min.x, resolutionGate.max.x, cropWindow.max.x ),
				lerp( resolutionGate.min.y, resolutionGate.max.y, cropWindow.max.y )
			)
		)
	);

	m_overlayDirty = false;
}

void CropWindowTool::findCropWindowPlug()
{
	if( !m_needCropWindowPlugSearch )
	{
		return;
	}

	m_cropWindowPlug = nullptr;

	Context::Scope scopedContext( view()->getContext() );

	const GafferScene::ScenePlug::ScenePath rootPath;
	SceneAlgo::History::Ptr history = SceneAlgo::history( scenePlug()->globalsPlug(), rootPath );
	if( history )
	{
		const bool foundAnEnabledPlug = findCropWindowPlug( history.get(), /* enabledOnly = */ true );
		// If we didn't find an enabled cropWindow plug upstream, or we did and it's
		// read-only, look again for any other plugs that could be edited, but aren't
		// enabled yet. We'll enable it if the user makes an edit.
		if( !foundAnEnabledPlug || MetadataAlgo::readOnly( m_cropWindowPlug.get() ) )
		{
			findCropWindowPlug( history.get(), /* enabledOnly = */ false );
		}
	}

	if( m_cropWindowPlug )
	{
		const std::string plugName =  m_cropWindowPlug->relativeName( m_cropWindowPlug->ancestor<ScriptNode>() );

		// Even after the second search, we could still be read-only
		if( MetadataAlgo::readOnly( m_cropWindowPlug.get() ) )
		{
			m_overlay->setEditable( false );
			m_overlay->setCaption( plugName + " is locked" );
		}
		else
		{
			bool plugEditable = m_cropWindowPlug->settable();

			// If our cropWindow plug hasn't been enabled, we need to check if it's corresponding 'enabled'
			// plug is editable, it could be expressioned or locked even if our value plug isn't.
			if( m_cropWindowEnabledPlug && m_cropWindowEnabledPlug->getValue() == false )
			{
				plugEditable &= ( m_cropWindowEnabledPlug->settable() && !MetadataAlgo::readOnly( m_cropWindowEnabledPlug.get() ) );
			}

			m_overlay->setEditable( plugEditable );
			m_overlay->setCaption( plugEditable ? plugName : ( plugName + " isn't editable" ) );
		}

		m_cropWindowPlugDirtiedConnection = m_cropWindowPlug->node()->plugDirtiedSignal().connect( boost::bind( &CropWindowTool::plugDirtied, this, ::_1 ) );
	}
	else
	{
		m_overlay->setEditable( false );
		m_overlay->setCaption( "No crop window found. Insert a StandardOptions node." );
		m_cropWindowPlugDirtiedConnection.disconnect();
	}

	m_needCropWindowPlugSearch = false;
}

bool CropWindowTool::findCropWindowPlug( const SceneAlgo::History *history, bool enabledOnly )
{
	if ( findCropWindowPlugFromNode( history->scene.get(), enabledOnly ) )
	{
		return true;
	}

	for( const auto &p : history->predecessors )
	{
		if( findCropWindowPlug( p.get(), enabledOnly ) )
		{
			return true;
		}
	}

	return false;
}


bool CropWindowTool::findCropWindowPlugFromNode( GafferScene::ScenePlug *scene, bool enabledOnly )
{
	const Options *options = runTimeCast<const Options>( scene->node() );
	if( !options )
	{
		return false;
	}

	if( !options->enabledPlug()->getValue() )
	{
		return false;
	}

	for( NameValuePlugIterator it( options->optionsPlug() ); !it.done(); ++it )
	{
		NameValuePlug *memberPlug = it->get();
		if( memberPlug->namePlug()->getValue() != "render:cropWindow" )
		{
			continue;
		}
		if( enabledOnly )
		{
			if( BoolPlug *enabledPlug = memberPlug->enabledPlug() )
			{
				if( !enabledPlug->getValue() )
				{
					continue;
				}
			}
		}
		m_cropWindowPlug = memberPlug->valuePlug<Box2fPlug>()->source<Box2fPlug>();
		m_cropWindowEnabledPlug = memberPlug->enabledPlug();
		m_cropWindowEnabledPlug = m_cropWindowEnabledPlug ? m_cropWindowEnabledPlug->source<BoolPlug>() : nullptr;
		return true;
	}

	return false;
}
