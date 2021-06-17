//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_AUXILIARYNODEGADGET_H
#define GAFFERUI_AUXILIARYNODEGADGET_H

#include "GafferUI/NodeGadget.h"

namespace GafferUI
{

class GAFFERUI_API AuxiliaryNodeGadget : public NodeGadget
{

	public :

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::AuxiliaryNodeGadget, AuxiliaryNodeGadgetTypeId, NodeGadget );

		AuxiliaryNodeGadget( Gaffer::NodePtr node );
		~AuxiliaryNodeGadget() override;

		Imath::Box3f bound() const override;

	protected :

		void doRenderLayer( Layer layer, const Style *style ) const override;

	private :

		static NodeGadgetTypeDescription<AuxiliaryNodeGadget> g_nodeGadgetTypeDescription;

		void nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, const Gaffer::Node *node );
		bool updateLabel();
		bool updateUserColor();

		// \todo Consolidate the mechanism for reading userColor with the one in StandardConnectionGadget
		boost::optional<Imath::Color3f> m_userColor;
		std::string m_label;
		float m_radius;
};

IE_CORE_DECLAREPTR( AuxiliaryNodeGadget )

} // namespace GafferUI

#endif // GAFFERUI_AUXILIARYNODEGADGET_H
