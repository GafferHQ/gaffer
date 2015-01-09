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

#include "IECoreGL/Selector.h"

#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/Metadata.h"
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

using namespace GafferUI;
using namespace Gaffer;
using namespace Imath;

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
			if( entry.error.empty() || !boost::ends_with( error, "Previous attempt to get item failed." ) )
			{
				// Update the error message. Unfortunately the IECore::LRUCache at the
				// heart of Gaffer's caching  does not remember the details of exceptions that
				// occurred when the cache entry is in error - instead it throws a different
				// exception saying "Previous attempt to get item failed.". We ignore these less
				// helpful messages in favour of a previous messages if one exists.
				/// \todo Improve LRUCache behaviour and remove this workaround.
				entry.error = error;
			}
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

		virtual std::string getToolTip( const IECore::LineSegment3f &position ) const
		{
			std::string result = Gadget::getToolTip( position );
			if( !result.empty() )
			{
				return result;
			}
			for( PlugErrors::const_iterator it = m_errors.begin(); it != m_errors.end(); ++it )
			{
				result += it->second.error;
			}
			return result;
		}

	private :

		void parentChanged( GraphComponent *plug )
		{
			if( !plug->parent<GraphComponent>() )
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
static IECore::InternedString g_horizontalNoduleSpacingKey( "nodeGadget:horizontalNoduleSpacing"  );
static IECore::InternedString g_verticalNoduleSpacingKey( "nodeGadget:verticalNoduleSpacing"  );
static IECore::InternedString g_minWidthKey( "nodeGadget:minWidth"  );
static IECore::InternedString g_paddingKey( "nodeGadget:padding"  );
static IECore::InternedString g_nodulePositionKey( "nodeGadget:nodulePosition" );
static IECore::InternedString g_colorKey( "nodeGadget:color" );
static IECore::InternedString g_errorGadgetName( "__error" );

StandardNodeGadget::StandardNodeGadget( Gaffer::NodePtr node, LinearContainer::Orientation orientation )
	:	NodeGadget( node ),
		m_orientation( orientation ),
		m_nodeEnabled( true ),
		m_labelsVisibleOnHover( true ),
		m_dragDestinationProxy( 0 ),
		m_userColor( 0 )
{

	// build our ui structure
	////////////////////////////////////////////////////////

	float horizontalNoduleSpacing = 2.0f;
	float verticalNoduleSpacing = 0.2f;
	float minWidth = m_orientation == LinearContainer::X ? 10.0f : 0.0f;

	if( IECore::ConstFloatDataPtr d = Metadata::nodeValue<IECore::FloatData>( node.get(), g_horizontalNoduleSpacingKey ) )
	{
		horizontalNoduleSpacing = d->readable();
	}

	if( IECore::ConstFloatDataPtr d = Metadata::nodeValue<IECore::FloatData>( node.get(), g_verticalNoduleSpacingKey ) )
	{
		verticalNoduleSpacing = d->readable();
	}

	if( IECore::ConstFloatDataPtr d = Metadata::nodeValue<IECore::FloatData>( node.get(), g_minWidthKey ) )
	{
		minWidth = d->readable();
	}

	// four containers for nodules - one each for the top, bottom, left and right.
	// these contain spacers at either end to prevent nodules being placed in
	// the corners of the node gadget, and also to guarantee a minimim width for the
	// vertical containers and a minimum height for the horizontal ones.

	LinearContainerPtr topNoduleContainer = new LinearContainer( "topNoduleContainer", LinearContainer::X, LinearContainer::Centre, horizontalNoduleSpacing );
	topNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 0, 1, 0 ) ) ) );
	topNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 0, 1, 0 ) ) ) );

	LinearContainerPtr bottomNoduleContainer = new LinearContainer( "bottomNoduleContainer", LinearContainer::X, LinearContainer::Centre, horizontalNoduleSpacing );
	bottomNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 0, 1, 0 ) ) ) );
	bottomNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 0, 1, 0 ) ) ) );

	LinearContainerPtr leftNoduleContainer = new LinearContainer( "leftNoduleContainer", LinearContainer::Y, LinearContainer::Centre, verticalNoduleSpacing, LinearContainer::Decreasing );
	leftNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0, 0 ) ) ) );
	leftNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0, 0 ) ) ) );

	LinearContainerPtr rightNoduleContainer = new LinearContainer( "rightNoduleContainer", LinearContainer::Y, LinearContainer::Centre, verticalNoduleSpacing, LinearContainer::Decreasing );
	rightNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0, 0 ) ) ) );
	rightNoduleContainer->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( 1, 0, 0 ) ) ) );

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

	IndividualContainerPtr contentsContainer = new IndividualContainer();
	contentsContainer->setName( "contentsContainer" );

	contentsColumn->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( minWidth, 0, 0 ) ) ) );
	contentsColumn->addChild( contentsContainer );
	contentsColumn->addChild( new SpacerGadget( Box3f( V3f( 0 ), V3f( minWidth, 0, 0 ) ) ) );

	row->addChild( rightNoduleContainer );
	column->addChild( bottomNoduleContainer );

	addChild( column );
	setContents( new NameGadget( node ) );

	// nodules for all current plugs

	for( Gaffer::PlugIterator it( node.get() ); it!=it.end(); it++ )
	{
		addNodule( *it );
	}

	// connect to the signals we need in order to operate
	////////////////////////////////////////////////////////

	node->childAddedSignal().connect( boost::bind( &StandardNodeGadget::childAdded, this, ::_1,  ::_2 ) );
	node->childRemovedSignal().connect( boost::bind( &StandardNodeGadget::childRemoved, this, ::_1,  ::_2 ) );
	node->errorSignal().connect( boost::bind( &StandardNodeGadget::error, this, ::_1, ::_2, ::_3 ) );

	if( DependencyNode *dependencyNode = IECore::runTimeCast<DependencyNode>( node.get() ) )
	{
		const Gaffer::BoolPlug *enabledPlug = dependencyNode->enabledPlug();
		if( enabledPlug )
		{
			m_nodeEnabled = enabledPlug->getValue();
		}
		node->plugDirtiedSignal().connect( boost::bind( &StandardNodeGadget::plugDirtied, this, ::_1 ) );
	}

	dragEnterSignal().connect( boost::bind( &StandardNodeGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &StandardNodeGadget::dragMove, this, ::_1, ::_2 ) );
	dragLeaveSignal().connect( boost::bind( &StandardNodeGadget::dragLeave, this, ::_1, ::_2 ) );
	dropSignal().connect( boost::bind( &StandardNodeGadget::drop, this, ::_1, ::_2 ) );

	for( int e = FirstEdge; e <= LastEdge; e++ )
	{
		LinearContainer *c = noduleContainer( (Edge)e );
		c->enterSignal().connect( boost::bind( &StandardNodeGadget::enter, this, ::_1 ) );
		c->leaveSignal().connect( boost::bind( &StandardNodeGadget::leave, this, ::_1 ) );
	}

	Metadata::plugValueChangedSignal().connect( boost::bind( &StandardNodeGadget::plugMetadataChanged, this, ::_1, ::_2, ::_3 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &StandardNodeGadget::nodeMetadataChanged, this, ::_1, ::_2 ) );

	updateUserColor();
	updatePadding();
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

void StandardNodeGadget::doRender( const Style *style ) const
{
	// decide what state we're rendering in
	Style::State state = getHighlighted() ? Style::HighlightedState : Style::NormalState;

	// draw our background frame
	Box3f b = bound();
	style->renderNodeFrame(
		Box2f( V2f( b.min.x, b.min.y ) + V2f( g_borderWidth ), V2f( b.max.x, b.max.y ) - V2f( g_borderWidth ) ),
		g_borderWidth,
		state,
		m_userColor.get_ptr()
	);

	// draw our contents
	NodeGadget::doRender( style );

	// draw a strikethrough if we're disabled
	if( !m_nodeEnabled && !IECoreGL::Selector::currentSelector() )
	{
		/// \todo Replace renderLine() with a specific method (renderNodeStrikeThrough?) on the Style class
		/// so that styles can do customised drawing based on knowledge of what is being drawn.
		style->renderLine( IECore::LineSegment3f( V3f( b.min.x, b.min.y, 0 ), V3f( b.max.x, b.max.y, 0 ) ) );
	}
}

const Imath::Color3f *StandardNodeGadget::userColor() const
{
	return m_userColor.get_ptr();
}

Nodule *StandardNodeGadget::nodule( const Gaffer::Plug *plug )
{
	const GraphComponent *parent = plug->parent<GraphComponent>();
	if( !parent || parent == node() )
	{
		NoduleMap::iterator it = m_nodules.find( plug );
		if( it != m_nodules.end() )
		{
			return it->second;
		}
		return 0;
	}
	else if( const Plug *parentPlug = IECore::runTimeCast<const Plug>( parent ) )
	{
		CompoundNodule *compoundNodule = IECore::runTimeCast<CompoundNodule>( nodule( parentPlug ) );
		if( compoundNodule )
		{
			return compoundNodule->nodule( plug );
		}
	}
	return 0;
}

const Nodule *StandardNodeGadget::nodule( const Gaffer::Plug *plug ) const
{
	// naughty cast is better than repeating the above logic.
	return const_cast<StandardNodeGadget *>( this )->nodule( plug );
}

Imath::V3f StandardNodeGadget::noduleTangent( const Nodule *nodule ) const
{
	if( noduleContainer( LeftEdge )->isAncestorOf( nodule ) )
	{
		return V3f( -1, 0, 0 );
	}
	else if( noduleContainer( RightEdge )->isAncestorOf( nodule ) )
	{
		return V3f( 1, 0, 0 );
	}
	else if( noduleContainer( TopEdge )->isAncestorOf( nodule ) )
	{
		return V3f( 0, 1, 0 );
	}
	else
	{
		return V3f( 0, -1, 0 );
	}
}

StandardNodeGadget::Edge StandardNodeGadget::plugEdge( const Gaffer::Plug *plug )
{
	Edge edge = plug->direction() == Gaffer::Plug::In ? TopEdge : BottomEdge;
	if( m_orientation == LinearContainer::Y )
	{
		edge = edge == TopEdge ? LeftEdge : RightEdge;
	}

	if( IECore::ConstStringDataPtr d = Metadata::plugValue<IECore::StringData>( plug, g_nodulePositionKey ) )
	{
		if( d->readable() == "left" )
		{
			edge = LeftEdge;
		}
		else if( d->readable() == "right" )
		{
			edge = RightEdge;
		}
		else if( d->readable() == "bottom" )
		{
			edge = BottomEdge;
		}
		else
		{
			edge = TopEdge;
		}
	}

	return edge;
}

NodulePtr StandardNodeGadget::addNodule( Gaffer::PlugPtr plug )
{
	// create a Nodule if we actually want one

	if( plug->getName().string().compare( 0, 2, "__" )==0 )
	{
		return 0;
	}

	NodulePtr nodule = Nodule::create( plug );
	if( !nodule )
	{
		return 0;
	}

	// decide which nodule container to put it in

	LinearContainer *container = noduleContainer( plugEdge( plug.get() ) );

	// remove the spacer at the end, add the nodule, and replace the spacer at the end

	GadgetPtr endGadget = container->getChild<Gadget>( container->children().size() - 1 );
	container->removeChild( endGadget );
	container->addChild( nodule );
	container->addChild( endGadget );

	// remember our nodule

	m_nodules[plug.get()] = nodule.get();

	return nodule;
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

IndividualContainer *StandardNodeGadget::contentsContainer()
{
	return getChild<Gadget>( 0 ) // column
		->getChild<Gadget>( 1 ) // row
		->getChild<Gadget>( 1 ) // contentsColumn
		->getChild<IndividualContainer>( 1 );
}

const IndividualContainer *StandardNodeGadget::contentsContainer() const
{
	return const_cast<StandardNodeGadget *>( this )->contentsContainer();
}

void StandardNodeGadget::childAdded( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child )
{
	Gaffer::Plug *p = IECore::runTimeCast<Gaffer::Plug>( child );
	if( p )
	{
		addNodule( p );
	}
}

void StandardNodeGadget::childRemoved( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child )
{
	Gaffer::Plug *p = IECore::runTimeCast<Gaffer::Plug>( child );
	if( p )
	{
		Nodule *n = nodule( p );
		if( n )
		{
			n->parent<Gaffer::GraphComponent>()->removeChild( n );
			m_nodules.erase( p );
		}
	}
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
	LinearContainer *c = noduleContainer( edge );
	c->removeChild( c->getChild<Gadget>( c->children().size() - 1 ) );
	c->addChild( gadget );
}

Gadget *StandardNodeGadget::getEdgeGadget( Edge edge )
{
	LinearContainer *c = noduleContainer( edge );
	return c->getChild<Gadget>( c->children().size() - 1 );
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
	const DependencyNode *dependencyNode = IECore::runTimeCast<const DependencyNode>( plug->node() );
	if( dependencyNode && plug == dependencyNode->enabledPlug() )
	{
		m_nodeEnabled = static_cast<const Gaffer::BoolPlug *>( plug )->getValue();
		renderRequestSignal()( this );
	}

	if( ErrorGadget *e = errorGadget( /* createIfMissing = */ false ) )
	{
		e->removeError( plug );
	}
}

void StandardNodeGadget::enter( Gadget *gadget )
{
	if( m_labelsVisibleOnHover )
	{
		for( RecursiveStandardNoduleIterator it( gadget  ); it != it.end(); ++it )
		{
			(*it)->setLabelVisible( true );
		}
	}
}

void StandardNodeGadget::leave( Gadget *gadget )
{
	if( m_labelsVisibleOnHover )
	{
		for( RecursiveStandardNoduleIterator it( gadget  ); it != it.end(); ++it )
		{
			(*it)->setLabelVisible( false );
		}
	}
}

bool StandardNodeGadget::dragEnter( GadgetPtr gadget, const DragDropEvent &event )
{
	// we'll accept the drag if we know we can forward it on to a nodule
	// we own. we don't actually start the forwarding until dragMove, here we
	// just check there is something to forward to.
	if( closestCompatibleNodule( event ) )
	{
		return true;
	}

	return false;
}

bool StandardNodeGadget::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	Nodule *closest = closestCompatibleNodule( event );
	if( closest != m_dragDestinationProxy )
	{
		if( closest->dragEnterSignal()( closest, event ) )
		{
			if( m_dragDestinationProxy )
			{
				m_dragDestinationProxy->dragLeaveSignal()( m_dragDestinationProxy, event );
			}
			m_dragDestinationProxy = closest;
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
		m_dragDestinationProxy->dragLeaveSignal()( m_dragDestinationProxy, event );
	}
	m_dragDestinationProxy = NULL;

	return true;
}

bool StandardNodeGadget::drop( GadgetPtr gadget, const DragDropEvent &event )
{
	if( !m_dragDestinationProxy )
	{
		return false;
	}

	const bool result = m_dragDestinationProxy->dropSignal()( m_dragDestinationProxy, event );
	m_dragDestinationProxy = NULL;
	return result;
}

void StandardNodeGadget::plugMetadataChanged( IECore::TypeId nodeTypeId, const Gaffer::MatchPattern &plugPath, IECore::InternedString key )
{
	if(
		key != g_nodulePositionKey ||
		!node()->isInstanceOf( nodeTypeId )
	)
	{
		return;
	}

	for( NoduleMap::const_iterator it = m_nodules.begin(), eIt = m_nodules.end(); it != eIt; ++it )
	{
		const Gaffer::Plug *plug = it->first;
		if( match( plug->relativeName( node() ), plugPath ) )
		{
			Nodule *n = nodule( plug );
			if( !n )
			{
				continue;
			}

			LinearContainer *container = noduleContainer( plugEdge( plug ) );

			GadgetPtr endGadget = container->getChild<Gadget>( container->children().size() - 1 );
			container->removeChild( endGadget );
			container->addChild( n );
			container->addChild( endGadget );
		}
	}
}

Nodule *StandardNodeGadget::closestCompatibleNodule( const DragDropEvent &event )
{
	Nodule *result = 0;
	float maxDist = Imath::limits<float>::max();
	for( RecursiveNoduleIterator it( this ); it != it.end(); it++ )
	{
		if( noduleIsCompatible( it->get(), event ) )
		{
			Box3f noduleBound = (*it)->transformedBound( this );
			const V3f closestPoint = closestPointOnBox( event.line.p0, noduleBound );
			const float dist = ( closestPoint - event.line.p0 ).length2();
			if( dist < maxDist )
			{
				result = it->get();
				maxDist = dist;
			}
		}
	}

	return result;
}

bool StandardNodeGadget::noduleIsCompatible( const Nodule *nodule, const DragDropEvent &event )
{
	const Plug *dropPlug = IECore::runTimeCast<Gaffer::Plug>( event.data.get() );
	if( !dropPlug || dropPlug->node() == node() )
	{
		return 0;
	}

	const Plug *nodulePlug = nodule->plug();
	if( dropPlug->direction() == Plug::Out )
	{
		return nodulePlug->direction() == Plug::In && nodulePlug->acceptsInput( dropPlug );
	}
	else
	{
		return nodulePlug->direction() == Plug::Out && dropPlug->acceptsInput( nodulePlug );
	}
}

void StandardNodeGadget::nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key )
{
	if( !node()->isInstanceOf( nodeTypeId ) )
	{
		return;
	}

	if( key == g_colorKey )
	{
		if( updateUserColor() )
		{
			renderRequestSignal()( this );
		}
	}
	else if( key == g_paddingKey )
	{
		updatePadding();
	}
}

bool StandardNodeGadget::updateUserColor()
{
	boost::optional<Color3f> c;
	if( IECore::ConstColor3fDataPtr d = Metadata::nodeValue<IECore::Color3fData>( node(), g_colorKey ) )
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
	if( IECore::ConstFloatDataPtr d = Metadata::nodeValue<IECore::FloatData>( node(), g_paddingKey ) )
	{
		padding = d->readable();
	}

	contentsContainer()->setPadding( Box3f( V3f( -padding ), V3f( padding ) ) );
}

StandardNodeGadget::ErrorGadget *StandardNodeGadget::errorGadget( bool createIfMissing )
{
	if( ErrorGadget *result = getChild<ErrorGadget>( g_errorGadgetName ) )
	{
		return result;
	}

	if( !createIfMissing )
	{
		return NULL;
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
	// on the main thread.
	executeOnUIThread( boost::bind( &StandardNodeGadget::displayError, this, ConstPlugPtr( plug ), header + message ) );
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
