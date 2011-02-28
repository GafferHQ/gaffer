//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/NameGadget.h"
#include "GafferUI/LinearContainer.h"
#include "GafferUI/Style.h"

using namespace GafferUI;
using namespace Imath;

IE_CORE_DEFINERUNTIMETYPED( StandardNodeGadget );

NodeGadget::NodeGadgetTypeDescription<StandardNodeGadget> StandardNodeGadget::g_nodeGadgetTypeDescription( Gaffer::Node::staticTypeId() );

static const float g_borderWidth = 0.5f;
static const float g_minWidth = 10.0f;
static const float g_verticalSpacing = 0.5f;

StandardNodeGadget::StandardNodeGadget( Gaffer::NodePtr node )
	:	NodeGadget( node ), m_nodeHasObjectPlugs( false )
{
	LinearContainerPtr column = new LinearContainer( "column", LinearContainer::Y, LinearContainer::Centre, g_verticalSpacing );

	LinearContainerPtr inputNoduleRow = new LinearContainer( "inputNoduleRow", LinearContainer::X, LinearContainer::Centre, 2.0f );
	LinearContainerPtr outputNoduleRow = new LinearContainer( "outputNoduleRow", LinearContainer::X, LinearContainer::Centre, 2.0f );

	column->addChild( outputNoduleRow );
	column->addChild( new NameGadget( node ) );
	column->addChild( inputNoduleRow );

	setChild( column );
	
	Gaffer::ObjectPlugIterator it( node->children().begin(), node->children().end() );
	while( it!=node->children().end() )
	{
		m_nodeHasObjectPlugs = true;
		break;
	}
	
	Gaffer::ScriptNodePtr script = node->scriptNode();
	if( script )
	{
		script->selection()->memberAddedSignal().connect( boost::bind( &StandardNodeGadget::selectionChanged, this, ::_1,  ::_2 ) );
		script->selection()->memberRemovedSignal().connect( boost::bind( &StandardNodeGadget::selectionChanged, this, ::_1,  ::_2 ) );
	}
	
	node->childAddedSignal().connect( boost::bind( &StandardNodeGadget::childAdded, this, ::_1,  ::_2 ) );
	node->childRemovedSignal().connect( boost::bind( &StandardNodeGadget::childRemoved, this, ::_1,  ::_2 ) );
	
	for( Gaffer::PlugIterator it=node->plugsBegin(); it!=node->plugsEnd(); it++ )
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
	float width = std::max( b.size().x + 2 * g_borderWidth, g_minWidth );
	float c = b.center().x;
	b.min.x = c - width / 2.0f;
	b.max.x = c + width / 2.0f;

	Box3f inputRowBound = getChild<Gadget>()->getChild<LinearContainer>( "inputNoduleRow" )->transformedBound( this );
	Box3f outputRowBound = getChild<Gadget>()->getChild<LinearContainer>( "outputNoduleRow" )->transformedBound( this );
	if( inputRowBound.isEmpty() )
	{
		b.max.y += g_verticalSpacing + g_borderWidth;
	}
	
	if( outputRowBound.isEmpty() )
	{
		b.min.y -= g_verticalSpacing + g_borderWidth;
	}
	
	return b;
}

void StandardNodeGadget::doRender( IECore::RendererPtr renderer ) const
{
	
	renderer->attributeBegin();
	
		Gaffer::ConstScriptNodePtr script = node()->scriptNode();
		if( script && script->selection()->contains( node() ) )
		{
			renderer->setAttribute( Style::stateAttribute(), Style::stateValueSelected() );
		}
		else
		{
			renderer->setAttribute( Style::stateAttribute(), Style::stateValueNormal() );		
		}
		
		Box3f b = bound();
		Box3f inputRowBound = getChild<Gadget>()->getChild<LinearContainer>( "inputNoduleRow" )->transformedBound( this );
		Box3f outputRowBound = getChild<Gadget>()->getChild<LinearContainer>( "outputNoduleRow" )->transformedBound( this );
		
		if( !inputRowBound.isEmpty() )
		{
			b.max.y -= inputRowBound.size().y / 2.0f;
		}
		if( !outputRowBound.isEmpty() )
		{
			b.min.y += outputRowBound.size().y / 2.0f;
		}

		getStyle()->renderFrame( renderer, Box2f( V2f( b.min.x, b.min.y ) + V2f( g_borderWidth ), V2f( b.max.x, b.max.y ) - V2f( g_borderWidth ) ), g_borderWidth );
		
		NodeGadget::doRender( renderer );

	renderer->attributeEnd();

}

NodulePtr StandardNodeGadget::nodule( Gaffer::ConstPlugPtr plug )
{
	NoduleMap::iterator it = m_nodules.find( plug.get() );
	if( it==m_nodules.end() )
	{
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

NodulePtr StandardNodeGadget::addNodule( Gaffer::PlugPtr plug )
{
	if( plug->getName().compare( 0, 2, "__" )==0 )
	{
		return 0;
	}

	if( m_nodeHasObjectPlugs && !plug->isInstanceOf( Gaffer::ObjectPlug::staticTypeId() ) )
	{
		return 0;
	}
	
	NodulePtr nodule = new Nodule( plug );
	
	if( plug->direction()==Gaffer::Plug::In )
	{
		getChild<Gadget>()->getChild<LinearContainer>( "inputNoduleRow" )->addChild( nodule );
	}
	else
	{
		getChild<Gadget>()->getChild<LinearContainer>( "outputNoduleRow" )->addChild( nodule );
	}
	
	m_nodules[plug.get()] = nodule.get();
	
	return nodule;
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
