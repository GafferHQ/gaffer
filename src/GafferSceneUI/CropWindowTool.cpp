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

#include "GafferImageUI/ImageGadget.h"

#include "GafferSceneUI/SceneView.h"

#include "GafferScene/Options.h"
#include "GafferScene/ScenePlug.h"

#include "GafferImage/ImagePlug.h"

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
using namespace GafferImage;
using namespace GafferImageUI;


//////////////////////////////////////////////////////////////////////////
// Helpers
//////////////////////////////////////////////////////////////////////////

namespace
{

void flipNDCOrigin( Box2f &box )
{
	const float tmp = box.min.y;
	box.min.y = 1.0f - box.max.y;
	box.max.y = 1.0f - tmp;
}

// This may well be useful in other tools. It simply finds the 'in' (or failing
// that, 'out') ScenePlug of the node that produced the supplied image, based
// on the render node reference in the image's metadata.
GafferScene::ScenePlug *findSceneForImage( GafferImage::ImagePlug *image, std::string &message )
{
	const std::string scenePlugName = SceneAlgo::sourceSceneName( image );
	if( scenePlugName.empty() )
	{
		message = "Error: No <b>gaffer:sourceScene</b> metadata in image";
		return nullptr;
	}

	ScenePlug *scenePlug = SceneAlgo::sourceScene( image );
	if( !scenePlug )
	{
		// Often the source plug is an internal plug such as __adaptedIn, we don't
		// want to show this to users, so we just use the node name.
		size_t separatorPos = scenePlugName.rfind( "." );
		message = "Error: Unable to find the source node <b>" + scenePlugName.substr( 0, separatorPos ) + "</b>";
		return nullptr;
	}
	return scenePlug;
}

} // namespace


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

		Rectangle( bool rasterSpace )
			:	Gadget(), m_rasterSpace( rasterSpace ), m_editable( true ), m_masked( false ), m_dragInside( false ), m_xDragEdge( 0 ), m_yDragEdge( 0 )
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
			return Box3f();
			if( m_rasterSpace )
			{
				// We draw in raster space so don't have a sensible bound
				return Box3f();
			}
			else
			{
				return Box3f(
					V3f( m_rectangle.min.x, m_rectangle.min.y, 0 ),
					V3f( m_rectangle.max.x, m_rectangle.max.y, 0 )
				);
			}
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
			boost::optional<ViewportGadget::RasterScope> rasterScope;
			if( m_rasterSpace )
			{
				rasterScope.emplace( ancestor<ViewportGadget>() );
			}

			glPushAttrib( GL_CURRENT_BIT | GL_LINE_BIT | GL_ENABLE_BIT );

				if( IECoreGL::Selector::currentSelector() )
				{
					if( m_editable )
					{
						static const Box2f extents( V2f( -100000 ), V2f( 100000 ) );
						style->renderSolidRectangle( extents );
					}
				}
				else
				{
					if( m_masked )
					{
						glColor4f( 0.0f, 0.0f, 0.0f, 0.2f );
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
			bool inside;

			hoveredEdges( event, x, y, inside );

			if( !inside || event.modifiers == ButtonEvent::Modifiers::Shift )
			{
				Pointer::setCurrent( "crossHair" );
			}
			else if( x && y )
			{
				const bool isDown = m_rasterSpace ? ( x * y > 0 ) : ( x * y < 0 );
				Pointer::setCurrent( isDown ? "moveDiagonallyDown" : "moveDiagonallyUp" );
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
				Pointer::setCurrent( "move" );
			}

			return false;
		}

		bool buttonPress( const GafferUI::ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left )
			{
				return false;
			}

			hoveredEdges( event, m_xDragEdge, m_yDragEdge, m_dragInside );
			return true;
		}

		IECore::RunTimeTypedPtr dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			m_dragStart = eventPosition( event );
			m_dragStartRectangle = m_rectangle;
			return IECore::NullObject::defaultNullObject();
		}

		bool dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			if( event.sourceGadget != this )
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

			if( !m_dragInside || event.modifiers == ButtonEvent::Modifiers::Shift )
			{
				b.min = m_dragStart;
				b.max = p;
			}
			else if( m_xDragEdge || m_yDragEdge )
			{
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
			}
			else
			{
				const V2f offset = p - m_dragStart;
				b.min += offset;
				b.max += offset;
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

		void hoveredEdges( const ButtonEvent &event, int &x, int &y, bool &inside ) const
		{
			static const float threshold = 10;
			static const V2f threshold2f( threshold );

			x = y = 0;

			const V2f p = eventPosition( event );

			Box2f thresholdRegion = m_rectangle;
			thresholdRegion.min -= threshold2f;
			thresholdRegion.max += threshold2f;

			inside = thresholdRegion.intersects( p );

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
			if( m_rasterSpace )
			{
				return viewportGadget->gadgetToRasterSpace( event.line.p1, this );
			}
			else
			{
				const ImageGadget *imageGadget = static_cast<const ImageGadget *>( viewportGadget->getPrimaryChild() );
				V2f pixel = imageGadget->pixelAt( event.line );
				Context::Scope contextScope( imageGadget->getContext() );
				pixel.x *= imageGadget->getImage()->format().getPixelAspect();
				return pixel;
			}
		}

		bool m_rasterSpace;

		Imath::Box2f m_rectangle;
		UnarySignal m_rectangleChangedSignal;

		bool m_editable;
		bool m_masked;

		Imath::Box2f m_dragStartRectangle;
		Imath::V2f m_dragStart;
		bool m_dragInside;
		int m_xDragEdge;
		int m_yDragEdge;

};

//////////////////////////////////////////////////////////////////////////
// CropWindowTool implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CropWindowTool );

size_t CropWindowTool::g_firstPlugIndex = 0;
CropWindowTool::ToolDescription<CropWindowTool, SceneView> CropWindowTool::g_sceneToolDescription;
CropWindowTool::ToolDescription<CropWindowTool, ImageView> CropWindowTool::g_imageToolDescription;

CropWindowTool::CropWindowTool( View *view, const std::string &name )
	:	Tool( view, name ), m_needScenePlugSearch( true ), m_needCropWindowPlugSearch( true ), m_overlayDirty( true )
{
	const bool rasterSpace = runTimeCast<SceneView>( view );
	m_overlay = new Rectangle( rasterSpace );

	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "__scene", Plug::In ) );
	addChild( new ImagePlug( "__image", Plug::In ) );
	scenePlug()->setInput( view->inPlug<ScenePlug>() );
	imagePlug()->setInput( view->inPlug<ImagePlug>() );

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

std::string CropWindowTool::status() const
{
	return getOverlayVisible() ? m_overlayMessage : m_errorMessage;
}

CropWindowTool::StatusChangedSignal &CropWindowTool::statusChangedSignal()
{
	return m_statusChangedSignal;
}

GafferScene::ScenePlug *CropWindowTool::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *CropWindowTool::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

GafferImage::ImagePlug *CropWindowTool::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 1 );
}

const GafferImage::ImagePlug *CropWindowTool::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 1 );
}

//////////////////////////////////////////////////////////////////////////
// Overlay management and messaging
//////////////////////////////////////////////////////////////////////////

// We consider the tool to have two states, one where the overlay is visible and
// the tool is considered 'working', the other when we hide the overlay for
// some error reason.
// Ideally, we'd just have a single message. When used with a SceneView though,
// we need to consider both the input scene, and the viewers look-through
// camera. This means that our resolution gate may vary independently of our
// other dirty tracking for our scene/cropWindow plugs.
// In order to be as lazy as possible, we check the gate is valid in preRender.
// Most common status messages are generated during the search for either the
// scene or crop window plug. If only the gate has changed (ie. the user has
// changed the look-through camera), there is no need to go looking for any
// plugs again. This is only ever an error state. If we over-wrote the 'working'
// message for the overlay, we'd have to re-do our whole setup process even though
// nothing has changed just to get the status message back.
// Instead, we make the separation of an 'error message' (when the overlay
// is hidden as we don't have enough information), and an 'overlay message', when
// we have enough knowledge to present the tool to the user.
// The public `status` method returns the appropriate message depending on
// the state of the overlay.
// This isn't great by any stretch of the imagination and there will most certainly
// be some edge cases in here, were soon to have a revamp of tool status though as
// part of Edit Scopes, so here it lies for now.

void CropWindowTool::setOverlayMessage( const std::string &message )
{
	m_overlayMessage = message;
	statusChangedSignal()( *this );
}

void CropWindowTool::setErrorMessage( const std::string &message )
{
	m_errorMessage = message;
	statusChangedSignal()( *this );
}

void CropWindowTool::setOverlayVisible( bool visible )
{
	if( visible != getOverlayVisible() )
	{
		m_overlay->setVisible( visible );
		statusChangedSignal()( *this );
	}
}

bool CropWindowTool::getOverlayVisible() const
{
	return m_overlay->getVisible();
}

//////////////////////////////////////////////////////////////////////////
// State tracking
//////////////////////////////////////////////////////////////////////////

// NOTE: The whole way we track and report state here needs refactoring.
// There are too many side effects. We need to prepare the state lazily on demand
// for either status/preRender, rather than status being a push side effect of
// render-driven state updates.

void CropWindowTool::viewportChanged()
{
	m_overlayDirty = true;
}

void CropWindowTool::plugDirtied( const Gaffer::Plug *plug )
{
	// When hosted in an ImageView, the view isn't dirtied by scene changes
	// (naturally) so just flagging the overlay dirty isn't enough.
	bool requestRender = false;

	if( plug == activePlug() )
	{
		m_needScenePlugSearch = m_needCropWindowPlugSearch = m_overlayDirty = true;
	}
	else if( plug == scenePlug()->globalsPlug() )
	{
		requestRender = m_needCropWindowPlugSearch = m_overlayDirty = true;
	}
	else if( plug == imagePlug()->metadataPlug() )
	{
		m_needScenePlugSearch = m_needCropWindowPlugSearch = m_overlayDirty = true;
	}
	else if( plug == m_cropWindowPlug || plug == m_cropWindowEnabledPlug || plug == imagePlug()->formatPlug() )
	{
		requestRender = m_overlayDirty = true;
	}

	if( requestRender && runTimeCast<ImageView>( view() ) )
	{
		view()->viewportGadget()->renderRequestSignal()(
			view()->viewportGadget()
		);
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
	const Box2f r = resolutionGate();
	b = Box2f(
		V2f(
			lerpfactor( b.min.x, r.min.x, r.max.x ),
			lerpfactor( b.min.y, r.min.y, r.max.y )
		),
		V2f(
			lerpfactor( b.max.x, r.min.x, r.max.x ),
			lerpfactor( b.max.y, r.min.y, r.max.y )
		)
	);

	if( runTimeCast<ImageView>( view() ) )
	{
		flipNDCOrigin( b );
	}

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
	if( !activePlug()->getValue() )
	{
		m_overlay->setVisible( false );
		return;
	}

	try
	{
		const Box2f r = resolutionGate();

		if( runTimeCast<SceneView>( view() ) )
		{
			// This is the only check we have that tells us whether we have an
			// appropriate camera to support the presentation of a crop window.
			// We don't have any other signals tied to this, hence the need to
			// check here before render.
			if( r.isEmpty() )
			{
				setErrorMessage( "Error: No applicable crop window for this view" );
				setOverlayVisible( false );
				return;
			}

			setOverlayVisible( true );
		}

		if( !m_overlayDirty )
		{
			return;
		}
		m_overlayDirty = false;

		findScenePlug();

		// This occurs in the ImageView hosted case, when we don't know which node
		// may have rendered the image being viewed.
		if( !scenePlug()->getInput() )
		{
			setOverlayVisible( false );
			return;
		}

		Box2f cropWindow( V2f( 0 ), V2f( 1 ) );
		findCropWindowPlug();
		if( m_cropWindowPlug )
		{
			cropWindow = m_cropWindowPlug->getValue();
		}
		if( runTimeCast<ImageView>( view() ) )
		{
			flipNDCOrigin( cropWindow );
		}

		BlockedConnection blockedConnection( m_overlayRectangleChangedConnection );
		m_overlay->setRectangle(
			Box2f(
				V2f(
					lerp( r.min.x, r.max.x, cropWindow.min.x ),
					lerp( r.min.y, r.max.y, cropWindow.min.y )
				),
				V2f(
					lerp( r.min.x, r.max.x, cropWindow.max.x ),
					lerp( r.min.y, r.max.y, cropWindow.max.y )
				)
			)
		);

		setOverlayVisible( true );

	}
	catch( const std::exception &e )
	{
		setErrorMessage( std::string("Error: ") + e.what() );
		setOverlayVisible( false );
	}
}

void CropWindowTool::findScenePlug()
{
	if ( !m_needScenePlugSearch )
	{
		return;
	}

	if( runTimeCast<ImageView>( view() ) )
	{
		std::string msg;
		ScenePlug *scene = nullptr;

		try
		{
			scene = findSceneForImage( imagePlug(), msg );
		}
		catch( const std::exception &e )
		{
			msg = std::string( "Error: " ) + e.what();
		}

		scenePlug()->setInput( scene );
		if( !scene )
		{
			setErrorMessage( msg );
		}
	}

	m_needScenePlugSearch = false;
}



void CropWindowTool::findCropWindowPlug()
{
	if( !m_needCropWindowPlugSearch )
	{
		return;
	}

	m_cropWindowPlug = nullptr;

	Context::Scope scopedContext( view()->getContext() );

	findScenePlug();

	try
	{
		const GafferScene::ScenePlug::ScenePath rootPath;
		SceneAlgo::History::Ptr history = SceneAlgo::history( scenePlug()->globalsPlug(), rootPath );
		const bool foundAnEnabledPlug = findCropWindowPlug( history.get(), /* enabledOnly = */ true );
		// If we didn't find an enabled cropWindow plug upstream, or we did and it's
		// read-only, look again for any other plugs that could be edited, but aren't
		// enabled yet. We'll enable it if the user makes an edit.
		if( !foundAnEnabledPlug || MetadataAlgo::readOnly( m_cropWindowPlug.get() ) )
		{
			findCropWindowPlug( history.get(), /* enabledOnly = */ false );
		}

		if( m_cropWindowPlug )
		{
			const std::string plugName =  m_cropWindowPlug->relativeName( m_cropWindowPlug->ancestor<ScriptNode>() );

			// Even after the second search, we could still be read-only
			if( MetadataAlgo::readOnly( m_cropWindowPlug.get() ) )
			{
				m_overlay->setEditable( false );
				setOverlayMessage( "Warning: <b>" + plugName + "</b> is locked" );
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
				setOverlayMessage( plugEditable
					? ( "Info: Editing <b>" + plugName + "</b>" )
					: ( "Warning: <b>" + plugName + "</b> isn't editable" )
				);
			}

			m_cropWindowPlugDirtiedConnection = m_cropWindowPlug->node()->plugDirtiedSignal().connect( boost::bind( &CropWindowTool::plugDirtied, this, ::_1 ) );
		}
		else
		{
			// Though this is an 'error' for the user, `setErrorMessage` is used in situations when the
			// tool has failed such that the overlay is hidden. As we still show the overlay without a plug
			// (as the crop is still defined in the scene), we use the overlay message instead.
			setOverlayMessage( "Error: No crop window found. Insert a <b>StandardOptions</b> node." );
		}

	}
	catch( const std::exception &e )
	{
		m_cropWindowPlug = nullptr;
		setOverlayMessage( std::string("Error: ") + e.what() );
	}

	if( !m_cropWindowPlug )
	{
		m_overlay->setEditable( false );
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
	if( !options || scene != options->outPlug() )
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

Box2f CropWindowTool::resolutionGate() const
{
	Box2f resolutionGate;
	if( const SceneView *sceneView = runTimeCast<const SceneView>( view() ) )
	{
		resolutionGate = sceneView->resolutionGate();
	}
	else if( const ImageView *imageView = runTimeCast<const ImageView>( view() ) )
	{
		if( const ImagePlug *in = imageView->inPlug<ImagePlug>() )
		{
			Context::Scope contextScope( imageView->getContext() );
			const Format format = in->format();
			resolutionGate = Box2f( V2f( 0 ), V2f( format.width() * format.getPixelAspect(), format.height() ) );
		}
	}
	return resolutionGate;
}
