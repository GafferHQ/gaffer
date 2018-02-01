//////////////////////////////////////////////////////////////////////////
//
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

#ifndef GAFFERUI_AUXILIARYCONNECTIONGADGET_H
#define GAFFERUI_AUXILIARYCONNECTIONGADGET_H

#include "GafferUI/Gadget.h"

namespace Gaffer
{
	IE_CORE_FORWARDDECLARE( Plug );
}

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( NodeGadget );
IE_CORE_FORWARDDECLARE( Style );

class AuxiliaryConnectionGadget : public Gadget
{

	public:

		AuxiliaryConnectionGadget( const NodeGadget *srcGadget, const NodeGadget *dstGadget );
		~AuxiliaryConnectionGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::AuxiliaryConnectionGadget, AuxiliaryConnectionGadgetTypeId, Gadget );

		Imath::Box3f bound() const override;

		void doRenderLayer( Layer layer, const Style *style ) const override;
		std::string getToolTip( const IECore::LineSegment3f &position ) const override;

		int removeConnection( const Gaffer::Plug *dstPlug );
		int removeConnection( const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug );
		void addConnection( const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug );
		bool hasConnection( const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug ) const;
		bool empty() const;

	private:

		ConstNodeGadgetPtr m_srcGadget;
		ConstNodeGadgetPtr m_dstGadget;

		mutable std::string m_toolTip;
		mutable bool m_toolTipValid;

		std::map<const Gaffer::Plug*, const Gaffer::Plug*> m_representedConnections;

};

IE_CORE_DECLAREPTR( AuxiliaryConnectionGadget );

} // namespace GafferUI

#endif // GAFFERUI_AUXILIARYCONNECTIONGADGET_H
