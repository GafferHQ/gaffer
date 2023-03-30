//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/StandardNodeGadget.h"

#include "GafferUI/CompoundNodule.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/ImageGadget.h"
#include "GafferUI/LinearContainer.h"
#include "GafferUI/NameGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/NoduleLayout.h"
#include "GafferUI/PlugAdder.h"
#include "GafferUI/SpacerGadget.h"
#include "GafferUI/StandardNodule.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/TypedObjectPlug.h"

#include "IECore/MessageHandler.h"

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathBoxAlgo.h"
#else
#include "Imath/ImathBoxAlgo.h"
#endif

// Don't include Qt macros that stomp over common names like "signals"
#define QT_NO_KEYWORDS
#include "QtCore/QTimer"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;

namespace {

const float g_borderWidth = 0.5f;
const float g_maxFocusWidth = 2.0f;

IECoreGL::Texture *focusIconTexture( bool focus, bool hover )
{
	static IECoreGL::TexturePtr focusIconTextures[4] = {};

	if( !focusIconTextures[0] )
	{
		focusIconTextures[0] = ImageGadget::textureLoader()->load( "focusOff.png" );
		focusIconTextures[1] = ImageGadget::textureLoader()->load( "focusOn.png" );
		focusIconTextures[2] = ImageGadget::textureLoader()->load( "focusOffHover.png" );
		focusIconTextures[3] = ImageGadget::textureLoader()->load( "focusOnHover.png" );

		for( int i = 0; i < 4; i++ )
		{
			IECoreGL::Texture::ScopedBinding binding( *focusIconTextures[i] );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR );
			glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_LOD_BIAS, -1.0 );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER );
		}
	}
	return focusIconTextures[focus + 2 * hover].get();
}

//////////////////////////////////////////////////////////////////////////
// FocusGadget
//////////////////////////////////////////////////////////////////////////

class FocusGadget : public Gadget
{
	public :

		FocusGadget( StandardNodeGadget* parent )
			:	m_oval( false ),
				m_mouseOver( false )
		{
			buttonPressSignal().connect( boost::bind( &FocusGadget::buttonPressed, this, ::_1,  ::_2 ) );
			buttonReleaseSignal().connect( boost::bind( &FocusGadget::buttonRelease, this, ::_1,  ::_2 ) );
			enterSignal().connect( boost::bind( &FocusGadget::mouseEntered, this, ::_1,  ::_2 ) );
			leaveSignal().connect( boost::bind( &FocusGadget::mouseLeft, this, ::_1,  ::_2 ) );
			buttonDoubleClickSignal().connect( boost::bind( &FocusGadget::buttonDoubleClick, this, ::_1,  ::_2 ) );
			parent->enterSignal().connect( boost::bind( &FocusGadget::nodeMouseEntered, this, ::_1,  ::_2 ) );
			parent->leaveSignal().connect( boost::bind( &FocusGadget::nodeMouseLeft, this, ::_1,  ::_2 ) );

			// FocusGadget always stays attached to its parent StandardNodeGadget, this must never change,
			// since we later assume that parent() is a StandardNodeGadget
			parent->addChild( this );
		}

		~FocusGadget() override
		{
			// Make sure we don't leave around a dangling raw pointer after we destruct
			if( g_pendingHoveredFocus == this )
			{
				g_pendingHoveredFocus = nullptr;
			}
		}

		void setOval( bool oval )
		{
			m_oval = oval;
			dirty( DirtyType::Render );
		}

		bool getOval() const
		{
			return m_oval;
		}

		Imath::Box3f bound() const override
		{
			return Box3f();
		}

	protected :

		void toggleFocus()
		{
			StandardNodeGadget* parentNodeGadget = static_cast<StandardNodeGadget*>( parent() );
			if( ScriptNode *script = parentNodeGadget->node()->ancestor<ScriptNode>() )
			{
				if( script->getFocus() != parentNodeGadget->node() )
				{
					script->setFocus( parentNodeGadget->node() );
				}
				else
				{
					// Unfocus if we click the icon on the focussed node
					script->setFocus( nullptr );
				}
			}
		}

		bool buttonPressed( GadgetPtr gadget, const ButtonEvent &event )
		{
			return true;
		}

		bool buttonRelease( GadgetPtr gadget, const ButtonEvent &event )
		{
			if( m_mouseOver && event.button == ButtonEvent::Left )
			{
				toggleFocus();
			}

			return true;
		}

		bool mouseEntered( GadgetPtr gadget, const ButtonEvent &event )
		{
			m_mouseOver = true;
			dirty( DirtyType::Render );
			return false;
		}

		bool mouseLeft( GadgetPtr gadget, const ButtonEvent &event )
		{
			m_mouseOver = false;
			dirty( DirtyType::Render );
			return false;
		}

		bool buttonDoubleClick( GadgetPtr gadget, const ButtonEvent &event )
		{
			if( event.buttons==ButtonEvent::Left )
			{
				// A user might rapidly click on the focus to toggle on and off - it's more consistent if
				// all clicks are treated the same, even if they come fast enough to be classified as a "double click"
				toggleFocus();
			}

			return true;
		}

		bool nodeMouseEntered( GadgetPtr gadget, const ButtonEvent &event )
		{
			static QTimer focusGadgetTimer;
			static QMetaObject::Connection focusGadgetTimerCallback = focusGadgetTimer.callOnTimeout(
				[]{
					if( g_pendingHoveredFocus )
					{
						StandardNodeGadget* parentNodeGadget = static_cast<StandardNodeGadget*>( g_pendingHoveredFocus->parent() );
						if( !parentNodeGadget )
						{
							IECore::msg( IECore::Msg::Error, "FocusGadget::nodeMouseEntered", "Focus gadget hover timer triggered on unparented FocusGadget" );
							return;
						}
						g_hoveredFocus = g_pendingHoveredFocus;
						g_hoveredFocusNodePosition = parentNodeGadget->getTransform();
						g_pendingHoveredFocus->dirty( DirtyType::Render );
					}
				}
			);
			focusGadgetTimer.stop();
			focusGadgetTimer.setSingleShot( true );
			g_pendingHoveredFocus = this;
			focusGadgetTimer.start( 500 );
			return false;
		}

		bool nodeMouseLeft( GadgetPtr gadget, const ButtonEvent &event )
		{
			g_pendingHoveredFocus = nullptr;
			if( g_hoveredFocus )
			{
				g_hoveredFocus = nullptr;
				dirty( DirtyType::Render );
			}
			return false;
		}

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			Gadget::renderLayer( layer, style, reason );

			const StandardNodeGadget* parentNodeGadget = static_cast<const StandardNodeGadget*>( parent() );

			if( this == g_hoveredFocus && parentNodeGadget->getTransform() != g_hoveredFocusNodePosition )
			{
				// If we have moved, then we are being dragged, and we don't treat ourselves as hovered
				// when the node is being dragged
				g_hoveredFocus = nullptr;
			}

			bool focussed = parentNodeGadget->node()->ancestor<ScriptNode>()->getFocus() == parentNodeGadget->node();
			if( this == g_hoveredFocus || m_mouseOver || focussed || ( reason == RenderReason::Select) )
			{
				Box3f b = parentNodeGadget->bound();

				float borderWidth = parentNodeGadget->focusBorderWidth();

				float nodeBorder = g_borderWidth;
				float radius = sqrtf( 2.0f ) * ( borderWidth + nodeBorder ) - nodeBorder;

				V2f size = V2f( radius );

				V2f center;

				if( m_oval )
				{
					const V3f s = b.size();
					float nodeRadius = 0.5f * std::min( s.x, s.y );

					float offset = (1.0f/sqrtf(2.0f)) * ( nodeRadius + radius ) - nodeRadius;

					center = V2f( b.max.x + offset, b.max.y + offset);
				}
				else
				{
					center = V2f( b.max.x + borderWidth, b.max.y + borderWidth );

				}

				if( !isSelectionRender( reason ) )
				{
					style->renderImage( Box2f( center - size, center + size ), focusIconTexture( focussed, m_mouseOver) );
				}
				else
				{
					if( reason == RenderReason::DragSelect )
					{
						// Not a target for dragging
						return;
					}

					// Render a circle for selection, instead of an icon which is treated as square by
					// the selection code
					style->renderFrame( Box2f( center, center ), size.x );
				}
			}
		}

		unsigned layerMask() const override
		{
			return (int)GraphLayer::Overlay;
		}

		Imath::Box3f renderBound() const override
		{
			// There should be a simple heuristic that would give a max bound, but it's actually bit
			// tricky to find one, so the quickest approach is just to duplicate the logic from renderLayer
			float nodeBorder = g_borderWidth;
			float maxRadius = sqrtf( 2.0f ) * ( g_maxFocusWidth + nodeBorder ) - nodeBorder;
			V3f center;
			const StandardNodeGadget* parentNodeGadget = static_cast<const StandardNodeGadget*>( parent() );
			Box3f b = parentNodeGadget->bound();
			if( m_oval )
			{
				const V3f s = b.size();
				float nodeRadius = 0.5f * std::min( s.x, s.y );

				float offset = (1.0f/sqrtf(2.0f)) * ( nodeRadius + maxRadius ) - nodeRadius;

				center = V3f( b.max.x + offset, b.max.y + offset, 0.0f );
			}
			else
			{
				center = V3f( b.max.x + g_maxFocusWidth, b.max.y + g_maxFocusWidth, 0.0f );

			}

			return Box3f( center - V3f( maxRadius ), center + V3f( maxRadius ) );
		}

	private :

		bool m_oval;
		bool m_mouseOver;

		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );

		// A focus gadget that the cursor is currently over, but we aren't going to show it as hovered
		// until a time duration has elapsed.  Must be cleared if the FocusGadget it points to is destructed
		static FocusGadget *g_pendingHoveredFocus;

		// This pointer is never dereferenced, only compared to, so we don't need to worry about cleaning it up
		static FocusGadget *g_hoveredFocus;

		// The position of the node the hoveredFocus is attached to - if this node is moved, that means we are
		// dragging the node currently, and we will no longer treat it as hovered.
		static M44f g_hoveredFocusNodePosition;

};

FocusGadget *FocusGadget::g_pendingHoveredFocus = nullptr;
FocusGadget *FocusGadget::g_hoveredFocus = nullptr;
M44f FocusGadget::g_hoveredFocusNodePosition;

} // namespace

//////////////////////////////////////////////////////////////////////////
// ErrorGadget implementation
//////////////////////////////////////////////////////////////////////////

class StandardNodeGadget::ErrorGadget : public Gadget
{

	public :

		ErrorGadget( const std::string &name = defaultName<ErrorGadget>() )
			:	Gadget( name ), m_image( new ImageGadget( "gadgetError.png" ) )
		{
			m_image->setTransform( M44f().scale( V3f( .025 ) ) );
			addChild( m_image );
		}

		void addError( PlugPtr plug, const std::string &error )
		{
			PlugEntry &entry = m_errors[plug];
			entry.error = error;
			if( !entry.parentChangedConnection.connected() )
			{
				entry.parentChangedConnection = plug->parentChangedSignal().connect( boost::bind( &ErrorGadget::plugParentChanged, this, ::_1 ) );
			}
			m_image->setVisible( true );
		}

		void removeError( const Plug *plug )
		{
			m_errors.erase( plug );
			m_image->setVisible( m_errors.size() );
		}

		std::string getToolTip( const IECore::LineSegment3f &position ) const override
		{
			std::string result = Gadget::getToolTip( position );
			if( !result.empty() )
			{
				return result;
			}

			std::set<std::string> reported;
			for( PlugErrors::const_iterator it = m_errors.begin(); it != m_errors.end(); ++it )
			{
				if( reported.find( it->second.error ) == reported.end() )
				{
					if( result.size() )
					{
						result += "\n";
					}
					result += it->second.error;
					reported.insert( it->second.error );
				}
			}
			return result;
		}

	private :

		void plugParentChanged( GraphComponent *plug )
		{
			if( !plug->parent() )
			{
				removeError( static_cast<Plug *>( plug ) );
			}
		}

		ImageGadgetPtr m_image;

		struct PlugEntry
		{
			std::string error;
			Signals::ScopedConnection parentChangedConnection;
		};

		using PlugErrors = std::map<ConstPlugPtr, PlugEntry>;
		PlugErrors m_errors;

};

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

bool canConnect( const DragDropEvent &event, const ConnectionCreator *destination )
{
	if( auto plug = IECore::runTimeCast<const Plug>( event.data.get() ) )
	{
		if( destination->canCreateConnection( plug ) )
		{
			return true;
		}
	}

	if( auto sourceCreator = IECore::runTimeCast<const ConnectionCreator>( event.sourceGadget.get() ) )
	{
		if( auto destinationNodule = IECore::runTimeCast<const Nodule>( destination ) )
		{
			return sourceCreator->canCreateConnection( destinationNodule->plug() );
		}
	}
	return false;
}

void connect( const DragDropEvent &event, ConnectionCreator *destination )
{
	if( auto plug = IECore::runTimeCast<Plug>( event.data.get() ) )
	{
		if( destination->canCreateConnection( plug ) )
		{
			UndoScope undoScope( plug->ancestor<ScriptNode>() );
			destination->createConnection( plug );
			return;
		}
	}

	if( auto sourceCreator = IECore::runTimeCast<ConnectionCreator>( event.sourceGadget.get() ) )
	{
		if( auto destinationNodule = IECore::runTimeCast<Nodule>( destination ) )
		{
			UndoScope undoScope( destinationNodule->plug()->ancestor<ScriptNode>() );
			sourceCreator->createConnection( destinationNodule->plug() );
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// StandardNodeGadget implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( StandardNodeGadget );

NodeGadget::NodeGadgetTypeDescription<StandardNodeGadget> StandardNodeGadget::g_nodeGadgetTypeDescription( Gaffer::Node::staticTypeId() );

static const float g_defaultMinWidth = 10.0f;
static IECore::InternedString g_minWidthKey( "nodeGadget:minWidth"  );
static IECore::InternedString g_paddingKey( "nodeGadget:padding"  );
static IECore::InternedString g_colorKey( "nodeGadget:color" );
static IECore::InternedString g_shapeKey( "nodeGadget:shape" );
static IECore::InternedString g_focusGadgetVisibleKey( "nodeGadget:focusGadgetVisible" );
static IECore::InternedString g_iconKey( "icon" );
static IECore::InternedString g_iconScaleKey( "iconScale" );
static IECore::InternedString g_errorGadgetName( "__error" );

StandardNodeGadget::StandardNodeGadget( Gaffer::NodePtr node )
	: StandardNodeGadget( node, false )
{
}


// \todo - Needing an auxiliary argument here isn't great - it's overly tight binding with AuxiliaryNodeGadget,
// and it should be possible to make NodeGadget's independent of StandardNodeGadget.  The right solution is
// probably to move more functionality for dealing with Focus and such into NodeGadget, so that other Gadgets
// can optionally use it without needing to inherit from StandardNodeGadget
StandardNodeGadget::StandardNodeGadget( Gaffer::NodePtr node, bool auxiliary  )
	:	NodeGadget( node ),
		m_nodeEnabled( true ),
		m_labelsVisibleOnHover( true ),
		m_dragDestination( nullptr ),
		m_userColor( 0 ),
		m_oval( false ),
		m_auxiliary( auxiliary ),
		m_focusGadget( new FocusGadget( this ) )
{

	// build our ui structure
	////////////////////////////////////////////////////////

	LinearContainerPtr contentsColumn = new LinearContainer(
		"contentsColumn",
		LinearContainer::Y,
		LinearContainer::Centre,
		0.0f,
		LinearContainer::Decreasing
	);

	LinearContainerPtr contentsRow = new LinearContainer(
		"paddingRow",
		LinearContainer::X,
		LinearContainer::Centre,
		0.5f
	);

	IndividualContainerPtr iconContainer = new IndividualContainer();
	iconContainer->setName( "iconContainer" );
	contentsRow->addChild( iconContainer );

	IndividualContainerPtr contentsContainer = new IndividualContainer();
	contentsContainer->setName( "contentsContainer" );
	contentsRow->addChild( contentsContainer );

	contentsColumn->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( g_defaultMinWidth, 0, 0 ) ) ) );
	contentsColumn->addChild( contentsRow );
	contentsColumn->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( g_defaultMinWidth, 0, 0 ) ) ) );


	if( auxiliary )
	{
		addChild( contentsColumn );
	}
	else
	{
		// four containers for nodules - one each for the top, bottom, left and right.
		// these contain spacers at either end to prevent nodules being placed in
		// the corners of the node gadget, and also to guarantee a minimim width for the
		// vertical containers and a minimum height for the horizontal ones.

		LinearContainerPtr topNoduleContainer = new LinearContainer( "topNoduleContainer", LinearContainer::X );
		LinearContainerPtr bottomNoduleContainer = new LinearContainer( "bottomNoduleContainer", LinearContainer::X );
		LinearContainerPtr leftNoduleContainer = new LinearContainer( "leftNoduleContainer", LinearContainer::Y, LinearContainer::Centre, 0.0f, LinearContainer::Decreasing );
		LinearContainerPtr rightNoduleContainer = new LinearContainer( "rightNoduleContainer", LinearContainer::Y, LinearContainer::Centre, 0.0f, LinearContainer::Decreasing );

		topNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 2, 1, 0 ) ) ) );
		topNoduleContainer->addChild( new NoduleLayout( node, "top" ) );
		topNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 2, 1, 0 ) ) ) );

		bottomNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 2, 1, 0 ) ) ) );
		bottomNoduleContainer->addChild( new NoduleLayout( node, "bottom" ) );
		bottomNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 2, 1, 0 ) ) ) );

		leftNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0.2, 0 ) ) ) );
		leftNoduleContainer->addChild( new NoduleLayout( node, "left" ) );
		leftNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0.2, 0 ) ) ) );

		rightNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0.2, 0 ) ) ) );
		rightNoduleContainer->addChild( new NoduleLayout( node, "right" ) );
		rightNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0.2, 0 ) ) ) );

		// column - this is our outermost structuring container

		LinearContainerPtr column = new LinearContainer(
			"column",
			LinearContainer::Y,
			LinearContainer::Centre,
			0.0f,
			LinearContainer::Decreasing
		);

		column->addChild( topNoduleContainer );

		LinearContainerPtr row = new LinearContainer(
			"row",
			LinearContainer::X,
			LinearContainer::Centre,
			0.0f
		);

		column->addChild( row );

		// central row - this holds our main contents, with the
		// nodule containers surrounding it.

		row->addChild( leftNoduleContainer );


		row->addChild( contentsColumn );
		row->addChild( rightNoduleContainer );
		column->addChild( bottomNoduleContainer );

		addChild( column );
	}

	setContents( new NameGadget( node ) );

	// connect to the signals we need in order to operate
	////////////////////////////////////////////////////////

	node->errorSignal().connect( boost::bind( &StandardNodeGadget::error, this, ::_1, ::_2, ::_3 ) );
	node->plugDirtiedSignal().connect( boost::bind( &StandardNodeGadget::plugDirtied, this, ::_1 ) );

	dragEnterSignal().connect( boost::bind( &StandardNodeGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &StandardNodeGadget::dragMove, this, ::_1, ::_2 ) );
	dragLeaveSignal().connect( boost::bind( &StandardNodeGadget::dragLeave, this, ::_1, ::_2 ) );
	dropSignal().connect( boost::bind( &StandardNodeGadget::drop, this, ::_1, ::_2 ) );

	for( int e = FirstEdge; e <= LastEdge; e++ )
	{
		NoduleLayout *l = noduleLayout( (Edge)e );
		if( l )
		{
			l->enterSignal().connect( boost::bind( &StandardNodeGadget::enter, this, ::_1 ) );
			l->leaveSignal().connect( boost::bind( &StandardNodeGadget::leave, this, ::_1 ) );
		}
	}

	Metadata::nodeValueChangedSignal( node.get() ).connect( boost::bind( &StandardNodeGadget::nodeMetadataChanged, this, ::_2 ) );

	// do our first update
	////////////////////////////////////////////////////////

	updateUserColor();
	updateMinWidth();
	updatePadding();
	updateNodeEnabled();
	updateIcon();
	updateShape();
	updateFocusGadgetVisibility();
}

StandardNodeGadget::~StandardNodeGadget()
{
}

Imath::Box3f StandardNodeGadget::bound() const
{
	Box3f b = getChild<Gadget>( 1 )->bound();

	// cheat a little - shave a bit off to make it possible to
	// select the node by having the drag region cover only the
	// background frame, and not the full extent of the nodules.
	b.min += V3f( g_borderWidth, g_borderWidth, 0 );
	b.max -= V3f( g_borderWidth, g_borderWidth, 0 );

	return b;
}

void StandardNodeGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	NodeGadget::renderLayer( layer, style, reason );

	switch( layer )
	{
		case GraphLayer::Nodes :
		{
			// decide what state we're rendering in
			Style::State state = getHighlighted() ? Style::HighlightedState : ( m_active ? Style::NormalState : Style::DisabledState );

			// draw our background frame
			const Box3f b = bound();
			float borderWidth = g_borderWidth;
			if( m_oval )
			{
				const V3f s = b.size();
				borderWidth = std::min( s.x, s.y ) / 2.0f;
			}

			style->renderNodeFrame(
				Box2f( V2f( b.min.x, b.min.y ) + V2f( borderWidth ), V2f( b.max.x, b.max.y ) - V2f( borderWidth ) ),
				borderWidth,
				state,
				userColor()
			);

			break;
		}
		case GraphLayer::Overlay :
		{
			const Box3f b = bound();

			if( !m_nodeEnabled && !isSelectionRender( reason ) )
			{
				/// \todo Replace renderLine() with a specific method (renderNodeStrikeThrough?) on the Style class
				/// so that styles can do customised drawing based on knowledge of what is being drawn.
				Imath::Color4f inactiveCol( 0.2f, 0.2f, 0.2f, 1.0 );
				style->renderLine(
					IECore::LineSegment3f( V3f( b.min.x, b.min.y, 0 ), V3f( b.max.x, b.max.y, 0 ) ),
					0.5f, m_active ? nullptr : &inactiveCol
				);
			}
			break;
		}
		case GraphLayer::OverBackdrops :
		{
			if( isSelectionRender( reason ) )
			{
				break; // Focus highlight not selectable
			}
			if( node()->ancestor<ScriptNode>()->getFocus() != node() )
			{
				break;
			}

			Box3f b = bound();
			float borderWidth = 0;

			if( m_oval )
			{
				const V3f s = b.size();
				borderWidth = std::min( s.x, s.y ) / 2.0f;
				b.min += V3f( borderWidth );
				b.max -= V3f( borderWidth );
			}

			style->renderNodeFocusRegion(
				Box2f( V2f( b.min.x, b.min.y ), V2f( b.max.x, b.max.y ) ),
				borderWidth + focusBorderWidth()
			);

			break;
		}
		default :
			break;
	}
}

float StandardNodeGadget::focusBorderWidth() const
{
	// Compute a fixed size in raster space, clamped to a maximum
	const ViewportGadget *viewport = ancestor<ViewportGadget>();
	const V3f p0 = viewport->rasterToGadgetSpace( V2f( 0 ), this ).p0;
	const V3f p1 = viewport->rasterToGadgetSpace( V2f( 0, 1.0f ), this ).p0;
	float pixelSize = ( p0 - p1 ).length();
	return min( g_maxFocusWidth, max( 0.75f, 8.0f * pixelSize ) );
}

void StandardNodeGadget::setHighlighted( bool highlighted )
{
	NodeGadget::setHighlighted( highlighted );
	updateTextDimming();
}

void StandardNodeGadget::activeForFocusNode( bool active )
{
	NodeGadget::activeForFocusNode( active );
	updateTextDimming();
}

void StandardNodeGadget::updateTextDimming()
{
	NameGadget *name = IECore::runTimeCast<NameGadget>( getContents() );
	if( name )
	{
		name->setDimmed( !( m_active || getHighlighted() ) );
	}
}

unsigned StandardNodeGadget::layerMask() const
{
	return GraphLayer::Nodes | GraphLayer::Overlay | GraphLayer::OverBackdrops;
}

Imath::Box3f StandardNodeGadget::renderBound() const
{
	Box3f b = bound();
	return Box3f(
		b.min - V3f( g_maxFocusWidth, g_maxFocusWidth, 0.f ),
		b.max + V3f( g_maxFocusWidth, g_maxFocusWidth, 0.f )
	);
}

const Imath::Color3f *StandardNodeGadget::userColor() const
{
	return m_userColor ? &m_userColor.value() : nullptr;
}

Nodule *StandardNodeGadget::nodule( const Gaffer::Plug *plug )
{
	for( int e = FirstEdge; e <= LastEdge; e++ )
	{
		NoduleLayout *l = noduleLayout( (Edge)e );
		if( l )
		{
			if( Nodule *n = l->nodule( plug ) )
			{
				return n;
			}
		}
	}
	return nullptr;
}

const Nodule *StandardNodeGadget::nodule( const Gaffer::Plug *plug ) const
{
	// naughty cast is better than repeating the above logic.
	return const_cast<StandardNodeGadget *>( this )->nodule( plug );
}

Imath::V3f StandardNodeGadget::connectionTangent( const ConnectionCreator *creator ) const
{
	if( m_auxiliary )
	{
		return V3f( 0, 0, 0 );
	}

	if( noduleContainer( LeftEdge )->isAncestorOf( creator ) )
	{
		return V3f( -1, 0, 0 );
	}
	else if( noduleContainer( RightEdge )->isAncestorOf( creator ) )
	{
		return V3f( 1, 0, 0 );
	}
	else if( noduleContainer( TopEdge )->isAncestorOf( creator ) )
	{
		return V3f( 0, 1, 0 );
	}
	else
	{
		return V3f( 0, -1, 0 );
	}
}

LinearContainer *StandardNodeGadget::noduleContainer( Edge edge )
{
	if( m_auxiliary )
	{
		return nullptr;
	}

	Gadget *column = getChild<Gadget>( 1 );

	if( edge == TopEdge )
	{
		return column->getChild<LinearContainer>( 0 );
	}
	else if( edge == BottomEdge )
	{
		return column->getChild<LinearContainer>( 2 );
	}

	Gadget *row = column->getChild<Gadget>( 1 );
	if( edge == LeftEdge )
	{
		return row->getChild<LinearContainer>( 0 );
	}
	else
	{
		return row->getChild<LinearContainer>( 2 );
	}
}

const LinearContainer *StandardNodeGadget::noduleContainer( Edge edge ) const
{
	return const_cast<StandardNodeGadget *>( this )->noduleContainer( edge );
}

NoduleLayout *StandardNodeGadget::noduleLayout( Edge edge )
{
	return m_auxiliary ? nullptr : noduleContainer( edge )->getChild<NoduleLayout>( 1 );
}

const NoduleLayout *StandardNodeGadget::noduleLayout( Edge edge ) const
{
	return m_auxiliary ? nullptr : noduleContainer( edge )->getChild<NoduleLayout>( 1 );
}

LinearContainer *StandardNodeGadget::contentsColumn()
{
	if( m_auxiliary )
	{
		return getChild<LinearContainer>( 1 );
	}
	else
	{
		return getChild<Gadget>( 1 ) // column
			->getChild<Gadget>( 1 ) // row
			->getChild<LinearContainer>( 1 )
		;
	}
}

const LinearContainer *StandardNodeGadget::contentsColumn() const
{
	return const_cast<StandardNodeGadget *>( this )->contentsColumn();
}

LinearContainer *StandardNodeGadget::paddingRow()
{
	return contentsColumn()->getChild<LinearContainer>( 1 );
}

const LinearContainer *StandardNodeGadget::paddingRow() const
{
	return const_cast<StandardNodeGadget *>( this )->paddingRow();
}

IndividualContainer *StandardNodeGadget::iconContainer()
{
	return paddingRow()->getChild<IndividualContainer>( 0 );
}

const IndividualContainer *StandardNodeGadget::iconContainer() const
{
	return paddingRow()->getChild<IndividualContainer>( 0 );
}

IndividualContainer *StandardNodeGadget::contentsContainer()
{
	return paddingRow()->getChild<IndividualContainer>( 1 );
}

const IndividualContainer *StandardNodeGadget::contentsContainer() const
{
	return paddingRow()->getChild<IndividualContainer>( 1 );
}

void StandardNodeGadget::setContents( GadgetPtr contents )
{
	contentsContainer()->setChild( contents );
}

Gadget *StandardNodeGadget::getContents()
{
	return contentsContainer()->getChild();
}

const Gadget *StandardNodeGadget::getContents() const
{
	return contentsContainer()->getChild();
}

void StandardNodeGadget::setEdgeGadget( Edge edge, GadgetPtr gadget )
{
	if( m_auxiliary )
	{
		return;
	}

	GadgetPtr previous = getEdgeGadget( edge );
	if( previous == gadget )
	{
		return;
	}

	if( IECore::runTimeCast<Nodule>( gadget ) )
	{
		throw IECore::Exception( "End Gadget can not be a Nodule." );
	}

	LinearContainer *c = noduleContainer( edge );

	GadgetPtr spacer = boost::static_pointer_cast<Gadget>( c->children().back() );
	c->removeChild( spacer );
	if( previous )
	{
		c->removeChild( previous );
	}
	if( gadget )
	{
		c->addChild( gadget );
	}
	c->addChild( spacer );
}

Gadget *StandardNodeGadget::getEdgeGadget( Edge edge )
{
	if( m_auxiliary )
	{
		return nullptr;
	}

	LinearContainer *c = noduleContainer( edge );
	const size_t s = c->children().size();
	if( s != 4 )
	{
		return nullptr;
	}

	return c->getChild<Gadget>( s - 2 );
}

const Gadget *StandardNodeGadget::getEdgeGadget( Edge edge ) const
{
	if( m_auxiliary )
	{
		return nullptr;
	}

	const LinearContainer *c = noduleContainer( edge );
	return c->getChild<Gadget>( c->children().size() - 1 );
}

void StandardNodeGadget::setLabelsVisibleOnHover( bool labelsVisible )
{
	m_labelsVisibleOnHover = labelsVisible;
}

bool StandardNodeGadget::getLabelsVisibleOnHover() const
{
	return m_labelsVisibleOnHover;
}

void StandardNodeGadget::plugDirtied( const Gaffer::Plug *plug )
{
	updateNodeEnabled( plug );
	if( ErrorGadget *e = errorGadget( /* createIfMissing = */ false ) )
	{
		e->removeError( plug );
	}
}

void StandardNodeGadget::enter( Gadget *gadget )
{
	if( m_labelsVisibleOnHover )
	{
		for( StandardNodule::RecursiveIterator it( gadget  ); !it.done(); ++it )
		{
			(*it)->setLabelVisible( true );
		}
	}
}

void StandardNodeGadget::leave( Gadget *gadget )
{
	if( m_labelsVisibleOnHover )
	{
		for( StandardNodule::RecursiveIterator it( gadget  ); !it.done(); ++it )
		{
			(*it)->setLabelVisible( false );
		}
	}
}

bool StandardNodeGadget::dragEnter( GadgetPtr gadget, const DragDropEvent &event )
{
	// Accept the drag if there's something we can connect it to.
	if( closestDragDestination( event ) )
	{
		// Display the labels for all the compatible nodules so the
		// user can see their options.
		for( StandardNodule::RecursiveIterator it( this ); !it.done(); ++it )
		{
			(*it)->setLabelVisible( canConnect( event, it->get() ) );
		}
		return true;
	}

	return false;
}

bool StandardNodeGadget::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	ConnectionCreator *closest = closestDragDestination( event );
	if( closest != m_dragDestination )
	{
		if( m_dragDestination )
		{
			m_dragDestination->setHighlighted( false );
		}
		m_dragDestination = closest;
		if( m_dragDestination )
		{
			if( ConnectionCreator *creator = IECore::runTimeCast<ConnectionCreator>( event.sourceGadget.get() ) )
			{
				V3f centre = V3f( 0 ) * m_dragDestination->fullTransform();
				centre = centre * creator->fullTransform().inverse();
				creator->updateDragEndPoint( centre, connectionTangent( m_dragDestination ) );
			}
			m_dragDestination->setHighlighted( true );
		}
	}
	return m_dragDestination;
}

bool StandardNodeGadget::dragLeave( GadgetPtr gadget, const DragDropEvent &event )
{
	if( !m_dragDestination )
	{
		return false;
	}

	if( m_dragDestination != event.destinationGadget )
	{
		m_dragDestination->setHighlighted( false );
		for( StandardNodule::RecursiveIterator it( this ); !it.done(); ++it )
		{
			(*it)->setLabelVisible( false );
		}
	}
	m_dragDestination = nullptr;

	return true;
}

bool StandardNodeGadget::drop( GadgetPtr gadget, const DragDropEvent &event )
{
	if( !m_dragDestination )
	{
		return false;
	}

	connect( event, m_dragDestination );

	m_dragDestination->setHighlighted( false );
	for( StandardNodule::RecursiveIterator it( this ); !it.done(); ++it )
	{
		(*it)->setLabelVisible( false );
	}
	m_dragDestination = nullptr;
	return true;
}

ConnectionCreator *StandardNodeGadget::closestDragDestination( const DragDropEvent &event ) const
{
	if( event.buttons != DragDropEvent::Left )
	{
		// See comments in StandardNodule::dragEnter()
		return nullptr;
	}

	ConnectionCreator *result = nullptr;
	float maxDist = std::numeric_limits<float>::max();

	for( ConnectionCreator::RecursiveIterator it( this ); !it.done(); it++ )
	{
		if( !(*it)->getVisible() )
		{
			it.prune();
			continue;
		}
		if( !canConnect( event, it->get() ) )
		{
			continue;
		}

		const Box3f bound = (*it)->transformedBound( this );
		if( bound.isEmpty() )
		{
			continue;
		}

		const V3f closestPoint = closestPointOnBox( event.line.p0, bound );
		const float dist = ( closestPoint - event.line.p0 ).length2();
		if( dist < maxDist )
		{
			result = it->get();
			maxDist = dist;
		}
	}

	return result;
}

void StandardNodeGadget::nodeMetadataChanged( IECore::InternedString key )
{
	if( key == g_colorKey )
	{
		if( updateUserColor() )
		{
			dirty( DirtyType::Render );
		}
	}
	else if( key == g_minWidthKey )
	{
		updateMinWidth();
	}
	else if( key == g_paddingKey )
	{
		updatePadding();
	}
	else if( key == g_iconKey || key == g_iconScaleKey )
	{
		updateIcon();
	}
	else if( key == g_shapeKey )
	{
		if( updateShape() )
		{
			dirty( DirtyType::Render );
		}
	}
	else if( key == g_focusGadgetVisibleKey )
	{
		updateFocusGadgetVisibility();
	}
}

bool StandardNodeGadget::updateUserColor()
{
	std::optional<Color3f> c;
	if( IECore::ConstColor3fDataPtr d = Metadata::value<IECore::Color3fData>( node(), g_colorKey ) )
	{
		c = d->readable();
	}

	if( c == m_userColor )
	{
		return false;
	}

	m_userColor = c;
	return true;
}

void StandardNodeGadget::updateMinWidth()
{
	float minWidth = g_defaultMinWidth;
	if( IECore::ConstFloatDataPtr d = Metadata::value<IECore::FloatData>( node(), g_minWidthKey ) )
	{
		minWidth = d->readable();
	}

	Gadget *contentsColumn = this->contentsColumn();
	const Box3f size( V3f( 0 ), V3f( minWidth, 0, 0 ) );
	contentsColumn->getChild<SpacerGadget>( 0 )->setSize( size );
	contentsColumn->getChild<SpacerGadget>( 2 )->setSize( size );
}

void StandardNodeGadget::updatePadding()
{
	float padding = 1.0f;
	if( IECore::ConstFloatDataPtr d = Metadata::value<IECore::FloatData>( node(), g_paddingKey ) )
	{
		padding = d->readable();
	}

	paddingRow()->setPadding( Box3f( V3f( -padding ), V3f( padding ) ) );
}

void StandardNodeGadget::updateNodeEnabled( const Gaffer::Plug *dirtiedPlug )
{
	DependencyNode *dependencyNode = IECore::runTimeCast<DependencyNode>( node() );
	if( !dependencyNode )
	{
		return;
	}

	const Gaffer::BoolPlug *enabledPlug = dependencyNode->enabledPlug();
	if( !enabledPlug )
	{
		return;
	}

	if( dirtiedPlug && dirtiedPlug != enabledPlug )
	{
		return;
	}

	const ValuePlug *source = enabledPlug->source<ValuePlug>();
	bool enabled = true;
	if( source->direction() != Plug::Out || !IECore::runTimeCast<const ComputeNode>( source->node() ) )
	{
		// Only evaluate `enabledPlug` if it won't trigger a compute.
		// We don't want to hang the UI waiting, and we don't really
		// know what context to perform the compute in anyway.
		/// \todo We could consider doing this in the background, using
		/// an upstream traversal from the focus node to determine context.
		enabled = enabledPlug->getValue();
	}

	if( enabled == m_nodeEnabled )
	{
		return;
	}

	m_nodeEnabled = enabled;
	dirty( DirtyType::Render );
}

void StandardNodeGadget::updateIcon()
{
	float scale = 1.5f;
	if( IECore::ConstFloatDataPtr d = Metadata::value<IECore::FloatData>( node(), g_iconScaleKey ) )
	{
		scale = d->readable();
	}


	ImageGadgetPtr image;
	if( IECore::ConstStringDataPtr d = Metadata::value<IECore::StringData>( node(), g_iconKey ) )
	{
		try
		{
			image = new ImageGadget( d->readable() );
		}
		catch( const std::exception &e )
		{
			IECore::msg( IECore::Msg::Error, "StandardNodeGadget::updateIcon", e.what() );
		}
	}

	if( image )
	{
		image->setTransform( M44f().scale( V3f( scale ) / image->bound().size().y ) );
	}

	iconContainer()->setChild( image );
}

bool StandardNodeGadget::updateShape()
{
	bool oval = false;
	if( m_auxiliary )
	{
		oval = true;
	}
	else
	{
		if( IECore::ConstStringDataPtr s = Metadata::value<IECore::StringData>( node(), g_shapeKey ) )
		{
			oval = s->readable() == "oval";
		}
	}

	if( oval == m_oval )
	{
		return false;
	}
	m_oval = oval;
	static_cast<FocusGadget *>( m_focusGadget.get() )->setOval( oval );
	return true;
}

void StandardNodeGadget::updateFocusGadgetVisibility()
{
	auto d = Metadata::value<IECore::BoolData>( node(), g_focusGadgetVisibleKey );
	m_focusGadget->setVisible( !d || d->readable() );
}

StandardNodeGadget::ErrorGadget *StandardNodeGadget::errorGadget( bool createIfMissing )
{
	if( ErrorGadget *result = getChild<ErrorGadget>( g_errorGadgetName ) )
	{
		return result;
	}

	if( !createIfMissing )
	{
		return nullptr;
	}

	ErrorGadgetPtr g = new ErrorGadget;
	setChild( g_errorGadgetName, g );
	return g.get();
}

void StandardNodeGadget::error( const Gaffer::Plug *plug, const Gaffer::Plug *source, const std::string &message )
{
	std::string header;
	if( source->node() == node() )
	{
		header = "Error on plug " + source->relativeName( node() );
	}
	else if( node()->isAncestorOf( source ) )
	{
		header = "Error on internal node " + source->node()->relativeName( node() );
	}
	else
	{
		header = "Error on upstream node " + source->node()->relativeName( source->ancestor<ScriptNode>() );
	}
	header = "# " + header + "\n\n";

	// We could be on any thread at this point, so we
	// use an idle callback to do the work of displaying the error
	// on the main thread. We _must_ use smart pointers for both
	// this and plug, because otherwise we have no guarantee that
	// they'll be alive later when the UI thread does its thing.
	ParallelAlgo::callOnUIThread( boost::bind( &StandardNodeGadget::displayError, StandardNodeGadgetPtr( this ), ConstPlugPtr( plug ), header + message ) );
}

void StandardNodeGadget::displayError( ConstPlugPtr plug, const std::string &message )
{
	// We need the const cast, because addError() needs non-const access to the plug
	// in order to be able to connect to its signals. The plug we were passed in
	// StandardNodeGadget::error() was const for a very good reason - we could be
	// on any thread so modifying the plug would be a big no-no. But now we're back
	// on the main thread, converting to non-const access is OK.
	errorGadget()->addError( boost::const_pointer_cast<Plug>( plug ), message );
}
