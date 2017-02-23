//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
#include "GafferUI/Style.h"

namespace GafferUI
{

class Handle : public Gadget
{

	public :

		virtual ~Handle();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::Handle, HandleTypeId, Gadget );

		void setRasterScale( float rasterScale );
		float getRasterScale() const;

		virtual Imath::Box3f bound() const;

	protected :

		Handle( const std::string &name=defaultName<Handle>() );

		// Implemented to call renderHandle() after applying
		// the raster scale.
		virtual void doRender( const Style *style ) const;

		// Must be implemented by derived classes to draw their
		// handle.
		virtual void renderHandle( const Style *style, Style::State state ) const = 0;

		// Called whenever a drag on the handle is initiated.
		// Should be implemented by derived classes to initialise
		// any state they need to track the drag.
		virtual void dragBegin( const DragDropEvent &event ) = 0;

		// Helper for performing linear drags. Should be constructed
		// in `dragBegin()` and then `position()` should be used
		// to measure the progress of the drag.
		struct LinearDrag
		{

			LinearDrag();
			// Line is specified in Gadget space.
			LinearDrag( const Gadget *gadget, const IECore::LineSegment3f &line, const DragDropEvent &dragBeginEvent );

			float startPosition() const;
			float position( const DragDropEvent &event ) const;

			private :

				const Gadget *m_gadget;
				// We store the line of the drag in world space so that
				// `position()` returns consistent results even if
				// the gadget transform or the camera changes during the drag.
				IECore::LineSegment3f m_worldLine;
				float m_dragBeginPosition;

		};

	private :

		void enter();
		void leave();

		bool buttonPress( const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBeginInternal( const DragDropEvent &event );
		bool dragEnter( const DragDropEvent &event );

		bool m_hovering;
		float m_rasterScale;

};

IE_CORE_DECLAREPTR( Handle )

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<Handle> > HandleIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<Handle> > RecursiveHandleIterator;

} // namespace GafferUI

#endif // GAFFERUI_HANDLE_H
