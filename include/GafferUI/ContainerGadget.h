//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_CONTAINERGADGET_H
#define GAFFERUI_CONTAINERGADGET_H

#include "GafferUI/Gadget.h"

namespace GafferUI
{

class ContainerGadget : public Gadget
{

	public :

		ContainerGadget( const std::string &name=defaultName<ContainerGadget>() );
		virtual ~ContainerGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::ContainerGadget, ContainerGadgetTypeId, Gadget );

		/// ContainerGadgets accept any number of other Gadgets as children. Derived classes
		/// may further restrict this if they wish, but they must not accept non-Gadget children.
		virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;
		/// Returns the union of the transformed bounding boxes of all children.
		virtual Imath::Box3f bound() const;
		//@}
		
		/// The padding is a region added around the contents of the children.
		/// It is specified as the final bounding box when the child bounding
		/// box is ( ( 0, 0, 0 ), ( 0, 0, 0 ) ). That is, padding.min is added to bound.min
		/// and padding.max is added to bound.max. 
		void setPadding( const Imath::Box3f &padding );
		const Imath::Box3f &getPadding() const;
		
	protected :
	
		/// Implemented to render all the children.
		virtual void doRender( const Style *style ) const;
		
	private :
	
		void childAdded( GraphComponent *parent, GraphComponent *child );
		void childRemoved( GraphComponent *parent, GraphComponent *child );
		void childRenderRequest( Gadget *child );
		
		Imath::Box3f m_padding;
		
};

IE_CORE_DECLAREPTR( ContainerGadget );

} // namespace GafferUI

#endif // GAFFERUI_CONTAINERGADGET_H
