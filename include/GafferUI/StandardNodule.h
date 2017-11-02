//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_STANDARDNODULE_H
#define GAFFERUI_STANDARDNODULE_H

#include "Gaffer/StringAlgo.h"
#include "Gaffer/Plug.h"

#include "GafferUI/Nodule.h"

namespace Gaffer
{
	IE_CORE_FORWARDDECLARE( Plug )
}

namespace GafferUI
{

class StandardNodule : public Nodule
{

	public :

		StandardNodule( Gaffer::PlugPtr plug );
		~StandardNodule() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::StandardNodule, StandardNoduleTypeId, Nodule );

		bool canCreateConnection( const Gaffer::Plug *destinationPlug ) const override;
		void updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent ) override;
		void createConnection( Gaffer::Plug *destinationPlug ) override;

		Imath::Box3f bound() const override;

	protected :

		void doRenderLayer( Layer layer, const Style *style ) const override;
		void renderLabel( const Style *style ) const;

		void enter( GadgetPtr gadget, const ButtonEvent &event );
		void leave( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );

		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const ButtonEvent &event );
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragLeave( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );
		bool drop( GadgetPtr gadget, const DragDropEvent &event );

		void setCompatibleLabelsVisible( const DragDropEvent &event, bool visible );

	private :

		void plugMetadataChanged( IECore::TypeId nodeTypeId, const Gaffer::StringAlgo::MatchPattern &plugPath, IECore::InternedString key, const Gaffer::Plug *plug );

		bool updateUserColor();

		bool m_draggingConnection;
		Imath::V3f m_dragPosition;
		Imath::V3f m_dragTangent;
		boost::optional<Imath::Color3f> m_userColor;

		static NoduleTypeDescription<StandardNodule> g_noduleTypeDescription;

};

IE_CORE_DECLAREPTR( StandardNodule );

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<StandardNodule> > StandardNoduleIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<StandardNodule> > RecursiveStandardNoduleIterator;

} // namespace GafferUI

#endif // GAFFERUI_STANDARDNODULE_H
