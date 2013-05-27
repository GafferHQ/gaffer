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

#include "OpenEXR/ImathBoxAlgo.h"

#include "IECoreGL/Selector.h"

#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/DependencyNode.h"

#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/NameGadget.h"
#include "GafferUI/LinearContainer.h"
#include "GafferUI/Style.h"
#include "GafferUI/CompoundNodule.h"
#include "GafferUI/StandardNodule.h"

using namespace GafferUI;
using namespace Gaffer;
using namespace Imath;

IE_CORE_DEFINERUNTIMETYPED( StandardNodeGadget );

NodeGadget::NodeGadgetTypeDescription<StandardNodeGadget> StandardNodeGadget::g_nodeGadgetTypeDescription( Gaffer::Node::staticTypeId() );

static const float g_borderWidth = 0.5f;
static const float g_minWidth = 10.0f;
static const float g_spacing = 0.5f;

StandardNodeGadget::StandardNodeGadget( Gaffer::NodePtr node, LinearContainer::Orientation orientation )
	:	NodeGadget( node ), m_nodeEnabled( true ), m_labelsVisibleOnHover( true ), m_dragDestinationProxy( 0 )
{
	LinearContainer::Orientation oppositeOrientation = orientation == LinearContainer::X ? LinearContainer::Y : LinearContainer::X;

	LinearContainerPtr mainContainer = new LinearContainer(
		"mainContainer",
		oppositeOrientation,
		LinearContainer::Centre,
		g_spacing,
		orientation == LinearContainer::X ? LinearContainer::Increasing : LinearContainer::Decreasing
	);

	const float noduleSpacing = orientation == LinearContainer::X ? 2.0f : 0.2f;
	LinearContainer::Direction noduleDirection = orientation == LinearContainer::X ? LinearContainer::Increasing : LinearContainer::Decreasing;
	LinearContainerPtr inputNoduleContainer = new LinearContainer( "inputNoduleContainer", orientation, LinearContainer::Centre, noduleSpacing, noduleDirection );
	LinearContainerPtr outputNoduleContainer = new LinearContainer( "outputNoduleContainer", orientation, LinearContainer::Centre, noduleSpacing, noduleDirection );

	mainContainer->addChild( outputNoduleContainer );
	
	IndividualContainerPtr contentsContainer = new IndividualContainer();
	contentsContainer->setName( "contentsContainer" );
	contentsContainer->setPadding( Box3f( V3f( -g_borderWidth ), V3f( g_borderWidth ) ) );
	
	mainContainer->addChild( contentsContainer );
	mainContainer->addChild( inputNoduleContainer );

	setChild( mainContainer );
	setContents( new NameGadget( node ) );
	
	Gaffer::ScriptNodePtr script = node->scriptNode();
	if( script )
	{
		script->selection()->memberAddedSignal().connect( boost::bind( &StandardNodeGadget::selectionChanged, this, ::_1,  ::_2 ) );
		script->selection()->memberRemovedSignal().connect( boost::bind( &StandardNodeGadget::selectionChanged, this, ::_1,  ::_2 ) );
	}
	
	node->childAddedSignal().connect( boost::bind( &StandardNodeGadget::childAdded, this, ::_1,  ::_2 ) );
	node->childRemovedSignal().connect( boost::bind( &StandardNodeGadget::childRemoved, this, ::_1,  ::_2 ) );
	
	for( Gaffer::PlugIterator it( node ); it!=it.end(); it++ )
	{
		addNodule( *it );
	}
	
	if( DependencyNode *dependencyNode = IECore::runTimeCast<DependencyNode>( node ) )
	{
		const Gaffer::BoolPlug *enabledPlug = dependencyNode->enabledPlug();
		if( enabledPlug )
		{
			m_nodeEnabled = enabledPlug->getValue();
			node->plugSetSignal().connect( boost::bind( &StandardNodeGadget::plugSet, this, ::_1 ) );
			node->plugDirtiedSignal().connect( boost::bind( &StandardNodeGadget::plugSet, this, ::_1 ) );
		}
	}
	
	
	dragEnterSignal().connect( boost::bind( &StandardNodeGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &StandardNodeGadget::dragMove, this, ::_1, ::_2 ) );
	dragLeaveSignal().connect( boost::bind( &StandardNodeGadget::dragLeave, this, ::_1, ::_2 ) );
	dropSignal().connect( boost::bind( &StandardNodeGadget::drop, this, ::_1, ::_2 ) );
	
	inputNoduleContainer->enterSignal().connect( boost::bind( &StandardNodeGadget::enter, this, ::_1 ) );
	inputNoduleContainer->leaveSignal().connect( boost::bind( &StandardNodeGadget::leave, this, ::_1 ) );

	outputNoduleContainer->enterSignal().connect( boost::bind( &StandardNodeGadget::enter, this, ::_1 ) );
	outputNoduleContainer->leaveSignal().connect( boost::bind( &StandardNodeGadget::leave, this, ::_1 ) );
}

StandardNodeGadget::~StandardNodeGadget()
{
}

Imath::Box3f StandardNodeGadget::bound() const
{
	Box3f b = IndividualContainer::bound();
	
	LinearContainer::Orientation orientation = inputNoduleContainer()->getOrientation();

	if( orientation == LinearContainer::X )
	{
		// enforce a minimum width
		float width = std::max( b.size().x, g_minWidth );
		float c = b.center().x;
		b.min.x = c - width / 2.0f;
		b.max.x = c + width / 2.0f;
	}
	
	// add the missing spacing to the border if we have no nodules on a given side
			
	Box3f inputContainerBound = inputNoduleContainer()->transformedBound( this );
	Box3f outputContainerBound = outputNoduleContainer()->transformedBound( this );
	if( inputContainerBound.isEmpty() )
	{
		if( orientation == LinearContainer::X )
		{
			b.max.y += g_spacing + g_borderWidth;
		}
		else
		{
			b.min.x -= g_spacing + g_borderWidth;		
		}
	}
	
	if( outputContainerBound.isEmpty() )
	{
		if( orientation == LinearContainer::X )
		{
			b.min.y -= g_spacing + g_borderWidth;
		}
		else
		{
			b.max.x += g_spacing + g_borderWidth;
		}
	}
	
	// add on a little bit in the major axis, so that the nodules don't get drawn in the frame corner
	
	if( orientation == LinearContainer::X )
	{
		b.min.x -= g_borderWidth;
		b.max.x += g_borderWidth;
	}
	else
	{
		b.min.y -= g_borderWidth;
		b.max.y += g_borderWidth;
	}
	
	return b;
}

void StandardNodeGadget::doRender( const Style *style ) const
{
	// decide what state we're rendering in
	Gaffer::ConstScriptNodePtr script = node()->scriptNode();
	
	Style::State state = Style::NormalState;
	if( script && script->selection()->contains( node() ) )
	{
		state = Style::HighlightedState;
	}
	
	// draw 
	Box3f b = bound();

	LinearContainer::Orientation orientation = inputNoduleContainer()->getOrientation();
	
	Box3f inputContainerBound = inputNoduleContainer()->transformedBound( this );
	Box3f outputContainerBound = outputNoduleContainer()->transformedBound( this );
	
	if( !inputContainerBound.isEmpty() )
	{
		if( orientation == LinearContainer::X )
		{
			b.max.y -= inputContainerBound.size().y / 2.0f;
		}
		else
		{
			b.min.x += inputContainerBound.size().x / 2.0f;
		}
	}
	if( !outputContainerBound.isEmpty() )
	{
		if( orientation == LinearContainer::X )
		{
			b.min.y += outputContainerBound.size().y / 2.0f;
		}
		else
		{
			b.max.x -= outputContainerBound.size().x / 2.0f;		
		}
	}

	style->renderFrame( Box2f( V2f( b.min.x, b.min.y ) + V2f( g_borderWidth ), V2f( b.max.x, b.max.y ) - V2f( g_borderWidth ) ), g_borderWidth, state );
	
	NodeGadget::doRender( style );
	
	if( !m_nodeEnabled && !IECoreGL::Selector::currentSelector() )
	{
		style->renderLine( IECore::LineSegment3f( V3f( b.min.x, b.min.y, 0 ), V3f( b.max.x, b.max.y, 0 ) ) );	
	}
}

Nodule *StandardNodeGadget::nodule( const Gaffer::Plug *plug )
{	
	const GraphComponent *parent = plug->parent<GraphComponent>();
	if( parent == node() )
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
	LinearContainer::Orientation orientation = inputNoduleContainer()->getOrientation();
	Plug::Direction direction = nodule->plug()->direction();
	if( orientation == LinearContainer::X )
	{
		return direction == Plug::In ? V3f( 0, 1, 0 ) : V3f( 0, -1, 0 );
	}
	return direction == Plug::In ? V3f( -1, 0, 0 ) : V3f( 1, 0, 0 );
}

NodulePtr StandardNodeGadget::addNodule( Gaffer::PlugPtr plug )
{
	if( plug->getName().string().compare( 0, 2, "__" )==0 )
	{
		return 0;
	}
	
	NodulePtr nodule = Nodule::create( plug );
	if( !nodule )
	{
		return 0;
	}
	
	if( plug->direction()==Gaffer::Plug::In )
	{
		inputNoduleContainer()->addChild( nodule );
	}
	else
	{
		outputNoduleContainer()->addChild( nodule );
	}
	
	m_nodules[plug.get()] = nodule.get();
	
	return nodule;
}

LinearContainer *StandardNodeGadget::outputNoduleContainer()
{
	return getChild<Gadget>()->getChild<LinearContainer>( 0 );
}

const LinearContainer *StandardNodeGadget::outputNoduleContainer() const
{
	return getChild<Gadget>()->getChild<LinearContainer>( 0 );
}

IndividualContainer *StandardNodeGadget::contentsContainer()
{
	return getChild<Gadget>()->getChild<IndividualContainer>( 1 );

}

const IndividualContainer *StandardNodeGadget::contentsContainer() const
{
	return getChild<Gadget>()->getChild<IndividualContainer>( 1 );
}

LinearContainer *StandardNodeGadget::inputNoduleContainer()
{
	return getChild<Gadget>()->getChild<LinearContainer>( 2 );
}

const LinearContainer *StandardNodeGadget::inputNoduleContainer() const
{
	return getChild<Gadget>()->getChild<LinearContainer>( 2 );
}

void StandardNodeGadget::selectionChanged( Gaffer::Set *selection, IECore::RunTimeTyped *n )
{
	if( n==node() )
	{
		renderRequestSignal()( this );
	}
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

void StandardNodeGadget::setLabelsVisibleOnHover( bool labelsVisible )
{
	m_labelsVisibleOnHover = labelsVisible;
}

bool StandardNodeGadget::getLabelsVisibleOnHover() const
{
	return m_labelsVisibleOnHover;
}

void StandardNodeGadget::plugSet( const Gaffer::Plug *plug )
{
	const DependencyNode *dependencyNode = IECore::runTimeCast<const DependencyNode>( plug->node() );
	if( dependencyNode && plug == dependencyNode->enabledPlug() )
	{
		m_nodeEnabled = static_cast<const Gaffer::BoolPlug *>( plug )->getValue();
		renderRequestSignal()( this );
	}
}

void StandardNodeGadget::plugDirtied( const Gaffer::Plug *plug )
{
	const DependencyNode *dependencyNode = IECore::runTimeCast<const DependencyNode>( plug->node() );
	if( dependencyNode && plug == dependencyNode->enabledPlug() )
	{
		m_nodeEnabled = static_cast<const Gaffer::BoolPlug *>( plug )->getValue();
		renderRequestSignal()( this );
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
	return true;
}

bool StandardNodeGadget::dragLeave( GadgetPtr gadget, const DragDropEvent &event )
{
	if( m_dragDestinationProxy && m_dragDestinationProxy != event.destinationGadget )
	{
		m_dragDestinationProxy->dragLeaveSignal()( m_dragDestinationProxy, event );
	}
	m_dragDestinationProxy = 0;

	return true;
}

bool StandardNodeGadget::drop( GadgetPtr gadget, const DragDropEvent &event )
{
	bool result = true;
	if( m_dragDestinationProxy )
	{
		result = m_dragDestinationProxy->dropSignal()( m_dragDestinationProxy, event );
		m_dragDestinationProxy = 0;
	}
	return result;
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
	const Plug *dropPlug = IECore::runTimeCast<Gaffer::Plug>( event.data );
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
