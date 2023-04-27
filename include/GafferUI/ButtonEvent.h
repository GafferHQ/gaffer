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

#pragma once

#include "GafferUI/ModifiableEvent.h"

#include "IECore/LineSegment.h"

namespace GafferUI
{

/// A class to represent events involving mouse buttons.
/// \todo Now this is being used to represent mouse movement and the scroll wheel,
/// it should be called MouseEvent.
/// \todo Add a `V2f point` field containing the Widget-relative position.
/// This will be convenient for 2d-only Widgets but also allow Gadgets to
/// get the original raster position for an event without jumping through
/// hoops and running the gauntlet of precision issues.
struct GAFFERUI_API ButtonEvent : public ModifiableEvent
{
	/// An enum to represent the mouse buttons.
	enum Buttons
	{
		None = 0,
		Left = 1,
		Middle = 2,
		Right = 4,
		LeftMiddle = Left | Middle,
		RightMiddle = Right | Middle,
		LeftRight = Left | Right,
		All = Left | Middle | Right
	};

	explicit ButtonEvent(
		Buttons button_ = None,
		Buttons buttons_ = None,
		const IECore::LineSegment3f &Line=IECore::LineSegment3f(),
		float w = 0.0f,
		Modifiers m = ModifiableEvent::None
	)
		:	ModifiableEvent( m ), button( button_ ), buttons( buttons_ ), line( Line ), wheelRotation( w )
	{
	};

	Buttons button; // the single button that caused the event
	Buttons buttons; // the button state when the event occurred
	IECore::LineSegment3f line;
	float wheelRotation; // delta in degrees

};

} // namespace GafferUI
