//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/UndoContext.h"
#include "Gaffer/ScriptNode.h"

#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/Nodule.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace GafferUI;
using namespace Imath;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( ConnectionGadget );

ConnectionGadget::ConnectionGadget( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule )
	:	Gadget( staticTypeName() ), m_srcNodule( srcNodule ), m_dstNodule( dstNodule ),
		m_dragEnd( Gaffer::Plug::Invalid )
{
	setPositionsFromNodules();
	
	buttonPressSignal().connect( boost::bind( &ConnectionGadget::buttonPress, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &ConnectionGadget::dragBegin, this, ::_1, ::_2 ) );
	dragUpdateSignal().connect( boost::bind( &ConnectionGadget::dragUpdate, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &ConnectionGadget::dragEnd, this, ::_1, ::_2 ) );
}

ConnectionGadget::~ConnectionGadget()
{
}

bool ConnectionGadget::acceptsParent( const Gaffer::GraphComponent *potentialParent ) const
{
	if( !Gadget::acceptsParent( potentialParent ) )
	{
		return false;
	}
	return IECore::runTimeCast<const GraphGadget>( potentialParent );
}	

NodulePtr ConnectionGadget::srcNodule()
{
	return m_srcNodule;
}

NodulePtr ConnectionGadget::dstNodule()
{
	return m_dstNodule;
}

void ConnectionGadget::setSrcPos( const Imath::V3f &p )
{
	if( m_srcPos!=p )
	{
		m_srcPos = p;
		renderRequestSignal()( this );
	}
}
		
void ConnectionGadget::setDstPos( const Imath::V3f &p )
{
	if( m_dstPos!=p )
	{
		m_dstPos = p;
		renderRequestSignal()( this );
	}
}

void ConnectionGadget::setPositionsFromNodules()
{
	const Gadget *p = parent<Gadget>();
	if( m_srcNodule && m_dragEnd!=Gaffer::Plug::Out )
	{
		M44f m = m_srcNodule->fullTransform( p );
		m_srcPos = V3f( 0 ) * m;
	}
	if( m_dstNodule && m_dragEnd!=Gaffer::Plug::In )
	{
		M44f m = m_dstNodule->fullTransform( p );
		m_dstPos = V3f( 0 ) * m;
	}
}
		
Imath::Box3f ConnectionGadget::bound() const
{
	Box3f r;
	r.extendBy( m_srcPos );
	r.extendBy( m_dstPos );
	return r;
}

void ConnectionGadget::doRender( IECore::RendererPtr renderer ) const
{
	const_cast<ConnectionGadget *>( this )->setPositionsFromNodules();
	getStyle()->renderConnection( renderer, m_srcPos, m_dstPos );
}

bool ConnectionGadget::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	if( event.buttons==ButtonEvent::Left )
	{
		// we have to accept button presses so we can initiate dragging
		return true;
	}
	return false;
}

IECore::RunTimeTypedPtr ConnectionGadget::dragBegin( GadgetPtr gadget, const DragDropEvent &event )
{
	setPositionsFromNodules();
	float length = ( m_srcPos - m_dstPos ).length();
	
	float dSrc = event.line.distanceTo( m_srcPos );
	float dDst = event.line.distanceTo( m_dstPos );
	
	float dMin = min( dSrc, dDst );
	if( dMin < length / 3.0f )
	{
		// close enough to the ends to consider
		if( dSrc < dDst )
		{
			m_dragEnd = Gaffer::Plug::Out;
			return m_dstNodule->plug();
		}
		else
		{
			if( m_dstNodule->plug()->acceptsInput( 0 ) )
			{
				m_dragEnd = Gaffer::Plug::In;
				return m_srcNodule->plug();
			}
		}
	}
	
	return 0;
}

bool ConnectionGadget::dragUpdate( GadgetPtr gadget, const DragDropEvent &event )
{
	if( m_dragEnd==Gaffer::Plug::Out )
	{
		m_srcPos = event.line.p0;
	}
	else
	{
		m_dstPos = event.line.p0;
	}
	renderRequestSignal()( this );
	return 0;
}

bool ConnectionGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	if( !event.destination )
	{
		// noone wanted the drop so we'll disconnect if the destination plug allows it
		if( m_dstNodule->plug()->acceptsInput( 0 ) )
		{
			Gaffer::UndoContext undoEnabler( m_dstNodule->plug()->ancestor<Gaffer::ScriptNode>() );
			m_dstNodule->plug()->setInput( 0 );
		}
	}
	else
	{
		// we let the Nodule do all the work when a drop has actually landed
	}

	m_dragEnd = Gaffer::Plug::Invalid;
	renderRequestSignal()( this );
	return true;
}

std::string ConnectionGadget::getToolTip() const
{
	std::string result = Gadget::getToolTip();
	if( result.size() )
	{
		return result;
	}
	
	if( !m_srcNodule || !m_dstNodule )
	{
		return result;
	}
	
	Gaffer::Plug *srcPlug = m_srcNodule->plug();
	Gaffer::Plug *dstPlug = m_dstNodule->plug();
	const Gaffer::GraphComponent *ancestor = srcPlug->commonAncestor<Gaffer::GraphComponent>( dstPlug );

	std::string srcName;
	std::string dstName;
	if( ancestor )
	{
		srcName = srcPlug->relativeName( ancestor );
		dstName = dstPlug->relativeName( ancestor );
	}
	else
	{
		srcName = srcPlug->fullName();
		dstName = dstPlug->fullName();
	}
	
	return srcName + " -> " + dstName;
}
