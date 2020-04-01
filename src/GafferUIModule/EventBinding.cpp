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

#include "boost/python.hpp"

#include "EventBinding.h"

#include "GafferUI/ButtonEvent.h"
#include "GafferUI/DragDropEvent.h"
#include "GafferUI/Event.h"
#include "GafferUI/Gadget.h"
#include "GafferUI/KeyEvent.h"

using namespace boost::python;
using namespace GafferUI;

namespace
{

GadgetPtr getSourceGadget( DragDropEvent &d )
{
	return d.sourceGadget;
}

void setSourceGadget( DragDropEvent &d, GadgetPtr s )
{
	d.sourceGadget = s;
}

IECore::RunTimeTypedPtr getData( DragDropEvent &d )
{
	return d.data;
}

void setData( DragDropEvent &d, IECore::RunTimeTypedPtr s )
{
	d.data = s;
}

GadgetPtr getDestinationGadget( DragDropEvent &d )
{
	return d.destinationGadget;
}

void setDestinationGadget( DragDropEvent &d, GadgetPtr s )
{
	d.destinationGadget = s;
}

} // namespace

void GafferUIModule::bindEvent()
{

	class_<Event>( "Event" )
	;

	{
		scope s = class_<ModifiableEvent, bases<Event> >( "ModifiableEvent" )
			.def( init<ModifiableEvent::Modifiers>() )
			.def_readwrite( "modifiers", &ModifiableEvent::modifiers )
		;

		enum_<ModifiableEvent::Modifiers>( "Modifiers" )
			.value( "None", ModifiableEvent::None )
			.value( "None_", ModifiableEvent::None )
			.value( "Shift", ModifiableEvent::Shift )
			.value( "Control", ModifiableEvent::Control )
			.value( "Alt", ModifiableEvent::Alt )
			.value( "ShiftControl", ModifiableEvent::ShiftControl )
			.value( "ShiftAlt", ModifiableEvent::ShiftAlt )
			.value( "ControlAlt", ModifiableEvent::ControlAlt )
			.value( "All", ModifiableEvent::All )
		;
	}

	class_<KeyEvent, bases<ModifiableEvent> >( "KeyEvent" )
		.def( init<const char *>() )
		.def( init<const char *, ModifiableEvent::Modifiers>() )
		.def_readwrite( "key", &KeyEvent::key )
		.def( self == self )
		.def( self != self )
	;

	{
		scope s = class_<ButtonEvent, bases<ModifiableEvent> >( "ButtonEvent" )
			.def( init<ButtonEvent::Buttons, ButtonEvent::Buttons>() )
			.def( init<ButtonEvent::Buttons, ButtonEvent::Buttons, const IECore::LineSegment3f &>() )
			.def( init<ButtonEvent::Buttons, ButtonEvent::Buttons, const IECore::LineSegment3f &, float>() )
			.def( init<ButtonEvent::Buttons, ButtonEvent::Buttons, const IECore::LineSegment3f &, float, ModifiableEvent::Modifiers>() )
			.def_readwrite( "button", &ButtonEvent::button )
			.def_readwrite( "buttons", &ButtonEvent::buttons )
			.def_readwrite( "line", &ButtonEvent::line )
			.def_readwrite( "wheelRotation", &ButtonEvent::wheelRotation )
		;

		enum_<ButtonEvent::Buttons>( "Buttons" )
			.value( "None", ButtonEvent::None )
			.value( "None_", ButtonEvent::None )
			.value( "Left", ButtonEvent::Left )
			.value( "Middle", ButtonEvent::Middle )
			.value( "Right", ButtonEvent::Right )
			.value( "LeftMiddle", ButtonEvent::LeftMiddle )
			.value( "RightMiddle", ButtonEvent::RightMiddle )
			.value( "LeftRight", ButtonEvent::LeftRight )
			.value( "All", ButtonEvent::All )
		;
	}

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
