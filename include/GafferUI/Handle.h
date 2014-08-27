//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#ifndef GAFFERUI_HANDLE_H
#define GAFFERUI_HANDLE_H

#include "GafferUI/Gadget.h"

namespace GafferUI
{

class Handle : public Gadget
{

	public :

		enum Type
		{
			TranslateX = 0,
			TranslateY,
			TranslateZ
		};

		Handle( Type type );
		virtual ~Handle();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::Handle, HandleTypeId, Gadget );

		void setType( Type type );
		Type getType() const;

		float dragOffset( const DragDropEvent &event ) const;

		virtual Imath::Box3f bound() const;

	protected :

		virtual void doRender( const Style *style ) const;

	private :

		void enter();
		void leave();

		bool buttonPress( const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( const DragDropEvent &event );
		bool dragEnter( const DragDropEvent &event );

		float absoluteDragOffset( const DragDropEvent &event ) const;

		Type m_type;
		bool m_hovering;

		// When a drag starts, we store the line of our
		// handle here. We store it in world space so that
		// dragOffset() returns consistent results even if
		// our transform or the camera changes during the drag.
		IECore::LineSegment3f m_dragHandleWorld;
		// The initial offset at drag begin. We store this so
		// that dragOffset() can return relative rather than
		// absolute offsets.
		float m_dragBeginOffset;

};

IE_CORE_DECLAREPTR( Handle )

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<Handle> > HandleIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<Handle> > RecursiveHandleIterator;

} // namespace GafferUI

#endif // GAFFERUI_HANDLE_H
