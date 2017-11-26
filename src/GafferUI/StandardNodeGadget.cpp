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

#include "boost/bind.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "OpenEXR/ImathBoxAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/AngleConversion.h"

#include "IECoreGL/Selector.h"

#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"

#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/NameGadget.h"
#include "GafferUI/LinearContainer.h"
#include "GafferUI/Style.h"
#include "GafferUI/CompoundNodule.h"
#include "GafferUI/StandardNodule.h"
#include "GafferUI/SpacerGadget.h"
#include "GafferUI/ImageGadget.h"
#include "GafferUI/PlugAdder.h"
#include "GafferUI/NoduleLayout.h"
#include "GafferUI/GraphGadget.h"

using namespace std;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;

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
				entry.parentChangedConnection = plug->parentChangedSignal().connect( boost::bind( &ErrorGadget::parentChanged, this, ::_1 ) );
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
					result += it->second.error;
					reported.insert( it->second.error );
				}
			}
			return result;
		}

	private :

		void parentChanged( GraphComponent *plug )
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
			boost::signals::scoped_connection parentChangedConnection;
		};

		typedef std::map<ConstPlugPtr, PlugEntry> PlugErrors;
		PlugErrors m_errors;

};

//////////////////////////////////////////////////////////////////////////
// StandardNodeGadget implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( StandardNodeGadget );

NodeGadget::NodeGadgetTypeDescription<StandardNodeGadget> StandardNodeGadget::g_nodeGadgetTypeDescription( Gaffer::Node::staticTypeId() );

static const float g_borderWidth = 0.5f;
static IECore::InternedString g_minWidthKey( "nodeGadget:minWidth"  );
static IECore::InternedString g_paddingKey( "nodeGadget:padding"  );
static IECore::InternedString g_colorKey( "nodeGadget:color" );
static IECore::InternedString g_shapeKey( "nodeGadget:shape" );
static IECore::InternedString g_iconKey( "icon" );
static IECore::InternedString g_iconScaleKey( "iconScale" );
static IECore::InternedString g_errorGadgetName( "__error" );

StandardNodeGadget::StandardNodeGadget( Gaffer::NodePtr node )
	:	NodeGadget( node ),
		m_nodeEnabled( true ),
		m_labelsVisibleOnHover( true ),
		m_dragDestinationProxy( nullptr ),
		m_userColor( 0 ),
		m_oval( false )
{

	// build our ui structure
	////////////////////////////////////////////////////////

	float minWidth = 10.0f;
	if( IECore::ConstFloatDataPtr d = Metadata::value<IECore::FloatData>( node.get(), g_minWidthKey ) )
	{
		minWidth = d->readable();
	}

	// four containers for nodules - one each for the top, bottom, left and right.
	// these contain spacers at either end to prevent nodules being placed in
	// the corners of the node gadget, and also to guarantee a minimim width for the
	// vertical containers and a minimum height for the horizontal ones.

	LinearContainerPtr topNoduleContainer = new LinearContainer( "topNoduleContainer", LinearContainer::X );
	topNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 2, 1, 0 ) ) ) );
	topNoduleContainer->addChild( new NoduleLayout( node, "top" ) );
	topNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 2, 1, 0 ) ) ) );

	LinearContainerPtr bottomNoduleContainer = new LinearContainer( "bottomNoduleContainer", LinearContainer::X );
	bottomNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 2, 1, 0 ) ) ) );
	bottomNoduleContainer->addChild( new NoduleLayout( node, "bottom" ) );
	bottomNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 2, 1, 0 ) ) ) );

	LinearContainerPtr leftNoduleContainer = new LinearContainer( "leftNoduleContainer", LinearContainer::Y, LinearContainer::Centre, 0.0f, LinearContainer::Decreasing );
	leftNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0.2, 0 ) ) ) );
	leftNoduleContainer->addChild( new NoduleLayout( node, "left" ) );
	leftNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0.2, 0 ) ) ) );

	LinearContainerPtr rightNoduleContainer = new LinearContainer( "rightNoduleContainer", LinearContainer::Y, LinearContainer::Centre, 0.0f, LinearContainer::Decreasing );
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

	LinearContainerPtr contentsColumn = new LinearContainer(
		"contentsColumn",
		LinearContainer::Y,
		LinearContainer::Centre,
		0.0f,
		LinearContainer::Decreasing
	);
	row->addChild( contentsColumn );

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

	contentsColumn->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( minWidth, 0, 0 ) ) ) );
	contentsColumn->addChild( contentsRow );
	contentsColumn->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( minWidth, 0, 0 ) ) ) );

	row->addChild( rightNoduleContainer );
	column->addChild( bottomNoduleContainer );

	addChild( column );
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
		l->enterSignal().connect( boost::bind( &StandardNodeGadget::enter, this, ::_1 ) );
		l->leaveSignal().connect( boost::bind( &StandardNodeGadget::leave, this, ::_1 ) );
	}

	Metadata::nodeValueChangedSignal().connect( boost::bind( &StandardNodeGadget::nodeMetadataChanged, this, ::_1, ::_2, ::_3 ) );

	// do our first update
	////////////////////////////////////////////////////////

	updateUserColor();
	updatePadding();
	updateNodeEnabled();
	updateIcon();
	updateShape();
}

StandardNodeGadget::~StandardNodeGadget()
{
}

Imath::Box3f StandardNodeGadget::bound() const
{
	Box3f b = getChild<Gadget>( 0 )->bound();

	// cheat a little - shave a bit off to make it possible to
	// select the node by having the drag region cover only the
	// background frame, and not the full extent of the nodules.
	b.min += V3f( g_borderWidth, g_borderWidth, 0 );
	b.max -= V3f( g_borderWidth, g_borderWidth, 0 );

	return b;
}

void StandardNodeGadget::doRenderLayer( Layer layer, const Style *style ) const
{
	switch( layer )
	{
	  case GraphLayer::Nodes :
		{
			// decide what state we're rendering in
			Style::State state = getHighlighted() ? Style::HighlightedState : Style::NormalState;

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
				m_userColor.get_ptr()
			);

			break;
		}

  	case GraphLayer::Highlighting :
		{
			// draw a strikethrough if we're disabled
			if( !m_nodeEnabled && !IECoreGL::Selector::currentSelector() )
			{
				const Box3f b = bound();
				/// \todo Replace renderLine() with a specific method (renderNodeStrikeThrough?) on the Style class
				/// so that styles can do customised drawing based on knowledge of what is being drawn.
				style->renderLine( IECore::LineSegment3f( V3f( b.min.x, b.min.y, 0 ), V3f( b.max.x, b.max.y, 0 ) ) );
			}

			// draw the labels for the nodules
			for( NoduleSet::const_iterator it = m_visibleNodules.begin(); it != m_visibleNodules.end(); ++it)
			{
				glPushMatrix();
				glMultMatrixf( (*it)->fullTransform( this ).getValue() );

				renderNoduleLabel( (*it), style );

				glPopMatrix();
			}

			break;
		}

	  default :
			break;
	}

	return NodeGadget::doRenderLayer( layer, style );
}

const Imath::Color3f *StandardNodeGadget::userColor() const
{
	return m_userColor.get_ptr();
}

Nodule *StandardNodeGadget::nodule( const Gaffer::Plug *plug )
{
	for( int e = FirstEdge; e <= LastEdge; e++ )
	{
		NoduleLayout *l = noduleLayout( (Edge)e );
		if( Nodule *n = l->nodule( plug ) )
		{
			return n;
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
	Gadget *column = getChild<Gadget>( 0 );

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
	return noduleContainer( edge )->getChild<NoduleLayout>( 1 );
}

const NoduleLayout *StandardNodeGadget::noduleLayout( Edge edge ) const
{
	return noduleContainer( edge )->getChild<NoduleLayout>( 1 );
}

LinearContainer *StandardNodeGadget::paddingRow()
{
	return getChild<Gadget>( 0 ) // column
		->getChild<Gadget>( 1 ) // row
		->getChild<Gadget>( 1 ) // contentsColumn
		->getChild<LinearContainer>( 1 )
	;
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
	return contentsContainer()->getChild<Gadget>();
}

const Gadget *StandardNodeGadget::getContents() const
{
	return contentsContainer()->getChild<Gadget>();
}

void StandardNodeGadget::setEdgeGadget( Edge edge, GadgetPtr gadget )
{
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
		for( RecursiveStandardNoduleIterator it( gadget  ); !it.done(); ++it )
		{
			setNoduleLabelVisible( (*it) );
		}
	}
}

void StandardNodeGadget::leave( Gadget *gadget )
{
	if( m_labelsVisibleOnHover )
	{
		setNoduleLabelsInvisible();
	}
}

bool StandardNodeGadget::dragEnter( GadgetPtr gadget, const DragDropEvent &event )
{
	// we'll accept the drag if we know we can forward it on to a nodule
	// we own. we don't actually start the forwarding until dragMove, here we
	// just check there is something to forward to.
	if( closestDragDestinationProxy( event ) )
	{
		return true;
	}

	return false;
}

bool StandardNodeGadget::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	ConnectionCreator *closest = closestDragDestinationProxy( event );
	if( closest != m_dragDestinationProxy )
	{
		if( m_dragDestinationProxy )
		{
			m_dragDestinationProxy->setHighlighted( false );
		}
		m_dragDestinationProxy = closest;
		if( m_dragDestinationProxy )
		{
			if( ConnectionCreator *creator = IECore::runTimeCast<ConnectionCreator>( event.sourceGadget.get() ) )
			{
				V3f centre = V3f( 0 ) * m_dragDestinationProxy->fullTransform();
				centre = centre * creator->fullTransform().inverse();

				if( ConnectionCreator *endpoint = IECore::runTimeCast<ConnectionCreator>( m_dragDestinationProxy ) )
				{
					creator->updateDragEndPoint( centre, connectionTangent( endpoint ) );
					setCompatibleNoduleLabelsVisible( creator );
				}
			}
			m_dragDestinationProxy->setHighlighted( true );
		}
	}
	return m_dragDestinationProxy;
}

bool StandardNodeGadget::dragLeave( GadgetPtr gadget, const DragDropEvent &event )
{
	if( !m_dragDestinationProxy )
	{
		return false;
	}

	if( m_dragDestinationProxy != event.destinationGadget )
	{
		m_dragDestinationProxy->setHighlighted( false );
		setNoduleLabelsInvisible();
	}

	m_dragDestinationProxy = nullptr;

	return true;
}

bool StandardNodeGadget::drop( GadgetPtr gadget, const DragDropEvent &event )
{
	if( !m_dragDestinationProxy )
	{
		return false;
	}

	PlugPtr plug = IECore::runTimeCast<Plug>( event.data );

	if( plug )
	{
		UndoScope undoScope( node()->scriptNode() );
		m_dragDestinationProxy->createConnection( plug.get() );
	}
	else
	{
		if( ConnectionCreator *creator = IECore::runTimeCast<ConnectionCreator>( event.sourceGadget.get() ) )
		{
			// see comment in closestDragDestinationProxy() about why this has to be a Nodule
			Nodule *nodule = IECore::runTimeCast<Nodule>( m_dragDestinationProxy );
			if( nodule )
			{
				UndoScope undoScope( nodule->plug()->ancestor<ScriptNode>() );
				creator->createConnection( nodule->plug() );
			}
		}
	}

	m_dragDestinationProxy->setHighlighted( false );
	m_dragDestinationProxy = nullptr;
	setNoduleLabelsInvisible();
	return true;
}

ConnectionCreator *StandardNodeGadget::closestDragDestinationProxy( const DragDropEvent &event ) const
{
	if( event.buttons != DragDropEvent::Left )
	{
		// See comments in StandardNodule::dragEnter()
		return nullptr;
	}

	ConnectionCreator *result = nullptr;
	float maxDist = Imath::limits<float>::max();

	Gaffer::Plug *eventPlug = IECore::runTimeCast<Gaffer::Plug>( event.data.get() );

	for( RecursiveGadgetIterator it( this ); !it.done(); it++ )
	{
		if( !(*it)->getVisible() )
		{
			it.prune();
			continue;
		}

		ConnectionCreator *creator = IECore::runTimeCast<ConnectionCreator>( it->get() );
		if( !creator )
		{
			continue;
		}

		// For a ConnectionCreator to be able to make a connection, one end needs to
		// be a plug. If the sourceGadget of the drag is able to provide one, we can
		// easily check if we can connect. If that's not the case we need to
		// determine if the source Gadget is able to make the connection - by
		// providing the Plug ourselves.

		if( eventPlug )
		{
			if( !creator->canCreateConnection( eventPlug ) )
			{
				continue;
			}
		}
		else
		{
			ConnectionCreator *creatorAtSource = IECore::runTimeCast<ConnectionCreator>( event.sourceGadget.get() );
			if( !creatorAtSource )
			{
				continue;
			}

			Nodule *destinationNodule = IECore::runTimeCast<Nodule>( it->get() );
			if( !destinationNodule )
			{
				continue;
			}

			if( !creatorAtSource->canCreateConnection( destinationNodule->plug() ) )
			{
				continue;
			}
		}

		const Box3f bound = (*it)->transformedBound( this );
		const V3f closestPoint = closestPointOnBox( event.line.p0, bound );
		const float dist = ( closestPoint - event.line.p0 ).length2();
		if( dist < maxDist )
		{
			result = creator;
			maxDist = dist;
		}
	}

	return result;
}

void StandardNodeGadget::nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, const Gaffer::Node *node )
{
	if( node && node != this->node() )
	{
		return;
	}

	if( !this->node()->isInstanceOf( nodeTypeId ) )
	{
		return;
	}

	if( key == g_colorKey )
	{
		if( updateUserColor() )
		{
 			requestRender();
		}
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
			requestRender();
		}
	}
}

bool StandardNodeGadget::updateUserColor()
{
	boost::optional<Color3f> c;
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

	bool enabled = true;
	try
	{
		enabled = enabledPlug->getValue();
	}
	catch( const std::exception &e )
	{
		// The error will be reported via Node::errorSignal() anyway.
		return;
	}


	if( enabled == m_nodeEnabled )
	{
		return;
	}

	m_nodeEnabled = enabled;
	requestRender();
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
	if( IECore::ConstStringDataPtr s = Metadata::value<IECore::StringData>( node(), g_shapeKey ) )
	{
		oval = s->readable() == "oval";
	}
	if( oval == m_oval )
	{
		return false;
	}
	m_oval = oval;
	return true;
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
	header = "<h3>" + header + "</h3>";

	// We could be on any thread at this point, so we
	// use an idle callback to do the work of displaying the error
	// on the main thread. We _must_ use smart pointers for both
	// this and plug, because otherwise we have no guarantee that
	// they'll be alive later when the UI thread does its thing.
	executeOnUIThread( boost::bind( &StandardNodeGadget::displayError, StandardNodeGadgetPtr( this ), ConstPlugPtr( plug ), header + message ) );
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

// todo: add some documentation
void StandardNodeGadget::setNoduleLabelVisible( const NodulePtr nodule )
{
	if( !nodule )
	{
		return;
	}

	m_visibleNodules.insert( nodule );
}

// todo: add some documentation
void StandardNodeGadget::setCompatibleNoduleLabelsVisible( const ConnectionCreator *creator )
{
	// clear current state
	setNoduleLabelsInvisible();

	if( !creator )
	{
		return;
	}

	for( RecursiveStandardNoduleIterator it( this ); !it.done(); ++it )
	{
		if( creator->canCreateConnection( it->get()->plug() ) )
		{
			m_visibleNodules.insert( (*it) );
		}
	}
}

// todo: add some documentation
void StandardNodeGadget::setNoduleLabelsInvisible()
{
	m_visibleNodules.clear();
}

// todo: add some documentation
void StandardNodeGadget::renderNoduleLabel( const NodulePtr nodule, const Style *style ) const
{
	// labelKey is a global variable in StandardNodule
	// static IECore::InternedString g_labelKey( "noduleLayout:label" );
	IECore::InternedString labelKey( "noduleLayout:label" );

	const std::string *label = nullptr;
	IECore::ConstStringDataPtr labelData = Metadata::value<IECore::StringData>( nodule->plug(), labelKey );
	if( labelData )
	{
		label = &labelData->readable();
	}
	else
	{
		label = &nodule->plug()->getName().string();
	}

	// we rotate the label based on the angle the connection exits the node at.
	V3f tangent = connectionTangent( nodule.get() );
	float theta = IECore::radiansToDegrees( atan2f( tangent.y, tangent.x ) );

	// but we don't want the text to be vertical, so we bend it away from the
	// vertical axis.
	if( ( theta > 0.0f && theta < 90.0f ) || ( theta < 0.0f && theta >= -90.0f ) )
	{
		theta = sign( theta ) * lerp( 0.0f, 45.0f, fabs( theta ) / 90.0f );
	}
	else
	{
		theta = sign( theta ) * lerp( 135.0f, 180.0f, (fabs( theta ) - 90.0f) / 90.0f );
	}

	// we also don't want the text to be upside down, so we correct the rotation
	// if that would be the case.
	Box3f labelBound = style->textBound( Style::LabelText, *label );
	V2f anchor( labelBound.min.x - 1.0f, labelBound.center().y );

	if( theta > 90.0f || theta < -90.0f )
	{
		theta = theta - 180.0f;
		anchor.x = labelBound.max.x + 1.0f;
	}

	// now we can actually do the rendering.

	if( nodule->getHighlighted() )
	{
		glScalef( 1.2, 1.2, 1.2 );
	}

	glRotatef( theta, 0, 0, 1.0f );
	glTranslatef( -anchor.x, -anchor.y, 0.0f );

	style->renderText( Style::LabelText, *label );
}
