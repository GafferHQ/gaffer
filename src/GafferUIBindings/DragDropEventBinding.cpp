//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2013, John Haddon. All rights reserved.
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

#include "boost/python.hpp"

#include "GafferUIBindings/DragDropEventBinding.h"
#include "GafferUI/DragDropEvent.h"
#include "GafferUI/Gadget.h"

using namespace boost::python;
using namespace GafferUIBindings;
using namespace GafferUI;

static GadgetPtr getSourceGadget( DragDropEvent &d )
{
	return d.sourceGadget;
}

static void setSourceGadget( DragDropEvent &d, GadgetPtr s )
{
	d.sourceGadget = s;
}

static IECore::RunTimeTypedPtr getData( DragDropEvent &d )
{
	return d.data;
}

static void setData( DragDropEvent &d, IECore::RunTimeTypedPtr s )
{
	d.data = s;
}

static GadgetPtr getDestinationGadget( DragDropEvent &d )
{
	return d.destinationGadget;
}

static void setDestinationGadget( DragDropEvent &d, GadgetPtr s )
{
	d.destinationGadget = s;
}

void GafferUIBindings::bindDragDropEvent()
{
	class_<DragDropEvent, bases<ButtonEvent> >( "DragDropEvent" )
		.def( init<ButtonEvent::Buttons, ButtonEvent::Buttons>() )
		.def( init<ButtonEvent::Buttons, ButtonEvent::Buttons, const IECore::LineSegment3f &>() )
		.def( init<ButtonEvent::Buttons, ButtonEvent::Buttons, const IECore::LineSegment3f &, ModifiableEvent::Modifiers>() )
		.add_property( "sourceGadget", &getSourceGadget, &setSourceGadget )
		.add_property( "data", &getData, &setData )
		.add_property( "destinationGadget", &getDestinationGadget, &setDestinationGadget )
		.def_readwrite( "dropResult", &DragDropEvent::dropResult )
	;	
}
