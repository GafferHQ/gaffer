//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2013, John Haddon. All rights reserved.
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

#include "boost/python.hpp"

#include "GafferUIBindings/ButtonEventBinding.h"
#include "GafferUI/ButtonEvent.h"

using namespace boost::python;
using namespace GafferUIBindings;
using namespace GafferUI;

void GafferUIBindings::bindButtonEvent()
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
		.value( "Left", ButtonEvent::Left )
		.value( "Middle", ButtonEvent::Middle )
		.value( "Right", ButtonEvent::Right )
		.value( "LeftMiddle", ButtonEvent::LeftMiddle )
		.value( "RightMiddle", ButtonEvent::RightMiddle )
		.value( "LeftRight", ButtonEvent::LeftRight )
		.value( "All", ButtonEvent::All )
	;
}
