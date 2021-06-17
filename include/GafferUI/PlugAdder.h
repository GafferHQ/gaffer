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

#include "GafferUI/ConnectionCreator.h"
#include "GafferUI/StandardNodeGadget.h"

namespace GafferUI
{

class GAFFERUI_API PlugAdder : public ConnectionCreator
{

	public :

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::PlugAdder, PlugAdderTypeId, ConnectionCreator );

		PlugAdder();
		~PlugAdder() override;

		Imath::Box3f bound() const override;

		bool canCreateConnection( const Gaffer::Plug *endpoint ) const override;
		void updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent ) override;

		/// When emitted, shows a menu containing the specified plugs, and returns
		/// the chosen plug. Implemented as a signal so the menu can be implemented
		/// externally in Python code.
		typedef boost::signal<Gaffer::Plug *( const std::string &title, const std::vector<Gaffer::Plug *> & )> PlugMenuSignal;
		static PlugMenuSignal &plugMenuSignal();

		/// A simpler menu that just shows a list of strings.  Should the previous form be deprecated?
		typedef boost::signal<std::string ( const std::string &title, const std::vector<std::string> & )> MenuSignal;
		static MenuSignal &menuSignal();

	protected :

		void doRenderLayer( Layer layer, const Style *style ) const override;
		unsigned layerMask() const override;

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

		bool m_dragging;
		Imath::V3f m_dragPosition;
		Imath::V3f m_dragTangent;

};

IE_CORE_DECLAREPTR( PlugAdder )

} // namespace GafferUI

#endif // GAFFERUI_PLUGADDER_H
