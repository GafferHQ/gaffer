//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_SPACERGADGET_H
#define GAFFERUI_SPACERGADGET_H

#include "GafferUI/Gadget.h"

namespace GafferUI
{

class GAFFERUI_API SpacerGadget : public Gadget
{

	public :

		SpacerGadget( const Imath::Box3f &size );
		~SpacerGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::SpacerGadget, SpacerGadgetTypeId, Gadget );

		Imath::Box3f bound() const override;

		const Imath::Box3f &getSize() const;
		void setSize( const Imath::Box3f &size );

		/// Rejects all children.
		bool acceptsChild( const GraphComponent *potentialChild ) const override;

	protected :

		void doRenderLayer( Layer layer, const Style *style ) const override;

	private :

		Imath::Box3f m_bound;

};

IE_CORE_DECLAREPTR( SpacerGadget )

} // namespace GafferUI

#endif // GAFFERUI_SPACERGADGET_H
