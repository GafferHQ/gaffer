//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_CONNECTIONGADGET_H
#define GAFFERUI_CONNECTIONGADGET_H

#include "GafferUI/Gadget.h"

#include "Gaffer/Plug.h"

namespace GafferUI
{
	IE_CORE_FORWARDDECLARE( Nodule )
}

namespace GafferUI
{

class ConnectionGadget : public Gadget
{

	public :

		ConnectionGadget( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule );
		virtual ~ConnectionGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::ConnectionGadget, ConnectionGadgetTypeId, Gadget );
		
		/// Accepts only GraphGadgets as parent.
		virtual bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const;		
		virtual Imath::Box3f bound() const;
		
		/// Returns the Nodule representing the source plug in the connection.
		/// Note that this may be 0 if the source plug belongs to a node which
		/// has been hidden.
		Nodule *srcNodule();
		const Nodule *srcNodule() const;
		/// Returns the Nodule representing the destination plug in the connection.
		Nodule *dstNodule();
		const Nodule *dstNodule() const;
		/// May be called to change the connection represented by this gadget.
		void setNodules( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule );

		/// A minimised connection is drawn only as a small stub
		/// entering the destination nodule - this can be useful in
		/// uncluttering a complex graph.
		void setMinimised( bool minimised );
		bool getMinimised() const;

		/// May be called by the recipient of a drag to set a more appropriate position
		/// and tangent for the connection as the drag progresses within the destination.
		/// Throws if this connection is not currently the source of a connection.
		void updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent );

		virtual std::string getToolTip( const IECore::LineSegment3f &line ) const;
		
	protected :

		void setPositionsFromNodules();
		
		void doRender( const Style *style ) const;

	private :
		
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
		
		NodulePtr m_srcNodule;
		NodulePtr m_dstNodule;
		
		bool m_minimised;
		
		Gaffer::Plug::Direction m_dragEnd;
		
		bool m_hovering;
		
};

IE_CORE_DECLAREPTR( ConnectionGadget );

} // namespace GafferUI

#endif // GAFFERUI_CONNECTIONGADGET_H
