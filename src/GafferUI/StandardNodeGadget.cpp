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

#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/CompoundPlug.h"

#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/NameGadget.h"
#include "GafferUI/LinearContainer.h"
#include "GafferUI/Style.h"
#include "GafferUI/CompoundNodule.h"

using namespace GafferUI;
using namespace Gaffer;
using namespace Imath;

IE_CORE_DEFINERUNTIMETYPED( StandardNodeGadget );

NodeGadget::NodeGadgetTypeDescription<StandardNodeGadget> StandardNodeGadget::g_nodeGadgetTypeDescription( Gaffer::Node::staticTypeId() );

static const float g_borderWidth = 0.5f;
static const float g_minWidth = 10.0f;
static const float g_spacing = 0.5f;

StandardNodeGadget::StandardNodeGadget( Gaffer::NodePtr node, LinearContainer::Orientation orientation )
	:	NodeGadget( node )
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
}

NodulePtr StandardNodeGadget::nodule( Gaffer::ConstPlugPtr plug )
{	
	NoduleMap::iterator it = m_nodules.find( plug.get() );
	if( it==m_nodules.end() )
	{
		/// \todo This needs to be generalised so other compound nodule types
		/// are possible, and so we can do nested compounds too.
		Gaffer::ConstCompoundPlugPtr compoundParent = plug->parent<Gaffer::CompoundPlug>();
		if( compoundParent )
		{
			it = m_nodules.find( compoundParent.get() );
			if( it!=m_nodules.end() )
			{
				CompoundNodulePtr compoundNodule = IECore::runTimeCast<CompoundNodule>( it->second );
				if( compoundNodule )
				{
					return compoundNodule->nodule( plug );
				}
			}
		}
		return 0;
	}
	return it->second;
}

ConstNodulePtr StandardNodeGadget::nodule( Gaffer::ConstPlugPtr plug ) const
{
	NoduleMap::const_iterator it = m_nodules.find( plug.get() );
	if( it==m_nodules.end() )
	{
		return 0;
	}
	return it->second;
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
	if( plug->getName().compare( 0, 2, "__" )==0 )
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

void StandardNodeGadget::selectionChanged( Gaffer::SetPtr selection, IECore::RunTimeTypedPtr n )
{
	if( n==node() )
	{
		renderRequestSignal()( this );
	}
}

void StandardNodeGadget::childAdded( Gaffer::GraphComponentPtr parent, Gaffer::GraphComponentPtr child )
{
	Gaffer::PlugPtr p = IECore::runTimeCast<Gaffer::Plug>( child );
	if( p )
	{
		addNodule( p );
	}
}

void StandardNodeGadget::childRemoved( Gaffer::GraphComponentPtr parent, Gaffer::GraphComponentPtr child )
{
	Gaffer::PlugPtr p = IECore::runTimeCast<Gaffer::Plug>( child );
	if( p )
	{
		NodulePtr n = nodule( p );
		if( n )
		{
			n->parent<Gaffer::GraphComponent>()->removeChild( n );
			m_nodules.erase( p.get() );
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

