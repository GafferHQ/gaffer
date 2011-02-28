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

#include "GafferUI/Nodule.h"
#include "GafferUI/Style.h"
#include "GafferUI/ConnectionGadget.h"

#include "Gaffer/Plug.h"
#include "Gaffer/UndoContext.h"
#include "Gaffer/ScriptNode.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace GafferUI;
using namespace Imath;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( Nodule );

Nodule::Nodule( Gaffer::PlugPtr plug )
	:	Gadget( staticTypeName() ), m_dragging( false ), m_plug( plug )
{
	buttonPressSignal().connect( boost::bind( &Nodule::buttonPress, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &Nodule::dragBegin, this, ::_1, ::_2 ) );
	dragUpdateSignal().connect( boost::bind( &Nodule::dragUpdate, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &Nodule::dragEnd, this, ::_1, ::_2 ) );

	dropSignal().connect( boost::bind( &Nodule::drop, this, ::_1, ::_2 ) );
}

Nodule::~Nodule()
{
}

Gaffer::PlugPtr Nodule::plug()
{
	return m_plug;
}

Gaffer::ConstPlugPtr Nodule::plug() const
{
	return m_plug;
}

Imath::Box3f Nodule::bound() const
{
	return Box3f( V3f( -0.5, -0.5, 0 ), V3f( 0.5, 0.5, 0 ) );
}

void Nodule::doRender( IECore::RendererPtr renderer ) const
{
	if( m_dragging )
	{
		// technically we shouldn't be drawing outside of our bound like this.
		// for the gl renderer it shouldn't matter. for others it might - at that
		// point we'll have to maintain a separate gagdet parented to the graph
		// just to draw this line. it seems like unecessary effort now though.
		getStyle()->renderConnection( renderer, V3f( 0 ), m_dragPosition );
	}
	
	getStyle()->renderNodule( renderer, 0.5 );
}

bool Nodule::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	// we handle the button press so we can get the dragBegin event.
	return true;
}

IECore::RunTimeTypedPtr Nodule::dragBegin( GadgetPtr gadget, const ButtonEvent &event )
{
	m_dragging = true;
	m_dragPosition = event.line.p0;
	renderRequestSignal()( this );
	return m_plug;
}

bool Nodule::dragUpdate( GadgetPtr gadget, const DragDropEvent &event )
{
	m_dragPosition = event.line.p0;
	renderRequestSignal()( this );
	return true;
}

bool Nodule::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	m_dragging = false;
	renderRequestSignal()( this );
	return true;
}

bool Nodule::drop( GadgetPtr gadget, const DragDropEvent &event )
{
	Gaffer::PlugPtr plug = IECore::runTimeCast<Gaffer::Plug>( event.data );
	if( plug )
	{
		if( m_plug->direction()!=plug->direction() )
		{
			Gaffer::PlugPtr input = 0;
			Gaffer::PlugPtr output = 0;
			if( m_plug->direction()==Gaffer::Plug::In )
			{
				input = m_plug;
				output = plug;
			}
			else
			{
				input = plug;
				output = m_plug;
			}
						
			if( input->acceptsInput( output ) )
			{
				Gaffer::UndoContext undoEnabler( input->ancestor<Gaffer::ScriptNode>() );

					ConnectionGadgetPtr connection = IECore::runTimeCast<ConnectionGadget>( event.source );
					if( connection && m_plug->direction()==Gaffer::Plug::In )
					{
						connection->dstNodule()->plug()->setInput( 0 );
					}

					input->setInput( output );
					
				return true;
			}
		}
	}
	return false;
}
