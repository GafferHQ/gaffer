//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_PLUGADDER_H
#define GAFFERUI_PLUGADDER_H

#include "GafferUI/Export.h"
#include "GafferUI/StandardNodeGadget.h"

namespace GafferUI
{

class GAFFERUI_API PlugAdder : public Gadget
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::PlugAdder, PlugAdderTypeId, Gadget );

		PlugAdder( StandardNodeGadget::Edge edge );
		virtual ~PlugAdder();

		virtual Imath::Box3f bound() const;

		void updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent );

		/// Returns `true` if a call to `addPlug( connectionEndPoint )` is possible.
		/// Should be implemented by derived classes.
		virtual bool acceptsPlug( const Gaffer::Plug *connectionEndPoint ) const = 0;
		/// Adds a plug compatible with `connectionEndPoint` and connects them together.
		/// Should be implemented by derived classes.
		virtual void addPlug( Gaffer::Plug *connectionEndPoint ) = 0;

		/// When emitted, shows a menu containing the specified plugs, and returns
		/// the chosen plug. Implemented as a signal so the menu can be implemented
		/// externally in Python code.
		typedef boost::signal<Gaffer::Plug *( const std::string &title, const std::vector<Gaffer::Plug *> & )> PlugMenuSignal;
		static PlugMenuSignal &plugMenuSignal();

	protected :

		virtual void doRender( const Style *style ) const;

		void applyEdgeMetadata( Gaffer::Plug *plug, bool opposite = false ) const;

	private :

		void enter( GadgetPtr gadget, const ButtonEvent &event );
		void leave( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const ButtonEvent &event );
		bool dragEnter( const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragLeave( const DragDropEvent &event );
		bool drop( const DragDropEvent &event );
		bool dragEnd( const DragDropEvent &event );

		StandardNodeGadget::Edge m_edge;

		bool m_dragging;
		Imath::V3f m_dragPosition;
		Imath::V3f m_dragTangent;

};

IE_CORE_DECLAREPTR( PlugAdder )

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<PlugAdder> > PlugAdderIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<PlugAdder> > RecursivePlugAdderIterator;

} // namespace GafferUI

#endif // GAFFERUI_PLUGADDER_H
