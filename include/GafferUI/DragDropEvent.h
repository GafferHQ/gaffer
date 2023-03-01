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

#pragma once

#include "GafferUI/ButtonEvent.h"

#include "IECore/RunTimeTyped.h"

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Gadget )

struct GAFFERUI_API DragDropEvent : public ButtonEvent
{

	DragDropEvent(
		Buttons button = None,
		Buttons buttons = None,
		const IECore::LineSegment3f &Line=IECore::LineSegment3f(),
		Modifiers m = ModifiableEvent::None
	)
		:	ButtonEvent( button, buttons, Line, 0, m ), sourceGadget( nullptr ), data( nullptr ), destinationGadget( nullptr ), dropResult( false )
	{
	};

	/// The Gadget where the drag originated.
	GafferUI::GadgetPtr sourceGadget;
	/// An object representing the data being dragged.
	IECore::RunTimeTypedPtr data;
	/// The Gadget where the drag ends.
	GafferUI::GadgetPtr destinationGadget;
	/// The result returned from the drop signal handler on the destination.
	bool dropResult;
};

} // namespace GafferUI
