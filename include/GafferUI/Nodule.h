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

#ifndef GAFFERUI_NODULE_H
#define GAFFERUI_NODULE_H

#include "GafferUI/Gadget.h"

namespace Gaffer
{
	IE_CORE_FORWARDDECLARE( Plug )
}

namespace GafferUI
{

class Nodule : public Gadget
{

	public :

		Nodule( Gaffer::PlugPtr plug );
		virtual ~Nodule();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Nodule, NoduleTypeId, Gadget );
		
		Gaffer::PlugPtr plug();
		Gaffer::ConstPlugPtr plug() const;

		virtual Imath::Box3f bound() const;

	protected :

		void doRender( IECore::RendererPtr renderer ) const;

		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const ButtonEvent &event );	
		bool dragUpdate( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );

		bool drop( GadgetPtr gadget, const DragDropEvent &event );
		
	private :

		bool m_dragging;
		Imath::V3f m_dragPosition;
		
		Gaffer::PlugPtr m_plug;
		
};

IE_CORE_DECLAREPTR( Nodule );

} // namespace GafferUI

#endif // GAFFERUI_NODULE_H
