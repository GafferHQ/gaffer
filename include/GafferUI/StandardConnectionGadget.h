//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_STANDARDCONNECTIONGADGET_H
#define GAFFERUI_STANDARDCONNECTIONGADGET_H

#include "GafferUI/ConnectionGadget.h"

namespace GafferUI
{

/// The standard implementation of the abstract ConnectionGadget base
/// class. Connections endpoints may be dragged + dropped, and the tooltip
/// displays the name of the source and destination plugs.
class StandardConnectionGadget : public ConnectionGadget
{

	public :

		StandardConnectionGadget( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule );
		virtual ~StandardConnectionGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::StandardConnectionGadget, StandardConnectionGadgetTypeId, ConnectionGadget );
		
		virtual Imath::Box3f bound() const;
		
		virtual void setNodules( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule );

		virtual void updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent );

		virtual std::string getToolTip( const IECore::LineSegment3f &line ) const;
		
	protected :
		
		void doRender( const Style *style ) const;

	private :

		static ConnectionGadgetTypeDescription<StandardConnectionGadget> g_connectionGadgetTypeDescription;
		
		void setPositionsFromNodules();

		void enter( GadgetPtr gadget, const ButtonEvent &event );
		void leave( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const DragDropEvent &event );	
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );	
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );
		
		bool nodeSelected( const Nodule *nodule ) const;
		
		Imath::V3f m_srcPos;
		Imath::V3f m_srcTangent;
		Imath::V3f m_dstPos;
		Imath::V3f m_dstTangent;
						
		Gaffer::Plug::Direction m_dragEnd;
		
		bool m_hovering;
		
};

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<StandardConnectionGadget> > StandardConnectionGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<StandardConnectionGadget> > RecursiveStandardConnectionGadgetIterator;

} // namespace GafferUI

#endif // GAFFERUI_STANDARDCONNECTIONGADGET_H
