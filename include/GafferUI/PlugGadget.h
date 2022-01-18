//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERUI_PLUGGADGET_H
#define GAFFERUI_PLUGGADGET_H

#include "GafferUI/ContainerGadget.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )
IE_CORE_FORWARDDECLARE( Context )

} // namespace Gaffer

namespace GafferUI
{

/// \todo Maybe rename GafferUI.PlugValueWidget to PlugWidget and
/// GafferUI.PlugWidget to GafferUI.LabelledPlugWidget, to better match
/// this class (and shorten some rather long names).
/// Add read-only support in the same way as PlugValueWidget does it.
class GAFFERUI_API PlugGadget : public ContainerGadget
{

	public :

		PlugGadget( Gaffer::PlugPtr plug );
		~PlugGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::PlugGadget, PlugGadgetTypeId, Gadget );

		void setPlug( Gaffer::PlugPtr plug );
		template<typename T=Gaffer::Plug>
		T *getPlug();

		void setContext( Gaffer::ContextPtr context );
		Gaffer::Context *getContext();

	protected :

		/// Must be implemented by derived classes - will be called whenever
		/// the ui needs to be updated to reflect a change in the plug.
		virtual void updateFromPlug();

	private :

		void plugDirtied( Gaffer::Plug *plug );
		void plugInputChanged( Gaffer::Plug *plug );
		void contextChanged( const Gaffer::Context *context, const IECore::InternedString &name );
		void updateContextConnection();

		Gaffer::Signals::ScopedConnection m_plugDirtiedConnection;
		Gaffer::Signals::ScopedConnection m_plugInputChangedConnection;
		Gaffer::Signals::ScopedConnection m_contextChangedConnection;
		Gaffer::PlugPtr m_plug;
		Gaffer::ContextPtr m_context;

};

IE_CORE_DECLAREPTR( PlugGadget )

} // namespace GafferUI

#include "GafferUI/PlugGadget.inl"

#endif // GAFFERUI_PLUGGADGET_H
