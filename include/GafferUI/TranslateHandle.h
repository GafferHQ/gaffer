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

#ifndef GAFFERUI_TRANSLATEHANDLE_H
#define GAFFERUI_TRANSLATEHANDLE_H

#include "GafferUI/Export.h"
#include "GafferUI/Handle.h"

namespace GafferUI
{

class GAFFERUI_API TranslateHandle : public Handle
{

	public :

		TranslateHandle( Style::Axes axes );
		~TranslateHandle() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::TranslateHandle, TranslateHandleTypeId, Handle );

		void setAxes( Style::Axes axes );
		Style::Axes getAxes() const;

		// Translation is measured in the local space of the handle.
		//
		// > Note :
		// > The use of a non-zero raster scale may make it appear
		// > that a handle has no scaling applied, but that scaling
		// > will still affect the results of `translation()`.
		float translation( const DragDropEvent &event ) const;

	protected :

		void renderHandle( const Style *style, Style::State state ) const override;
		void dragBegin( const DragDropEvent &event ) override;

	private :

		Style::Axes m_axes;
		LinearDrag m_drag;

};

IE_CORE_DECLAREPTR( TranslateHandle )

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<TranslateHandle> > TranslateHandleIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<TranslateHandle> > RecursiveTranslateHandleIterator;

} // namespace GafferUI

#endif // GAFFERUI_TRANSLATEHANDLE_H
