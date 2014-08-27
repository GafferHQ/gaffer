//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#ifndef GAFFERUI_VIEW3D_H
#define GAFFERUI_VIEW3D_H

#include "GafferUI/View.h"

namespace GafferUI
{

class View3D : public View
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::View3D, View3DTypeId, View );

		virtual ~View3D();

	protected :

		View3D( const std::string &name, Gaffer::PlugPtr input );

		/// The GL state to be used by derived classes when drawing. This
		/// is defined by the user via plugs on the view.
		const IECoreGL::State *baseState() const;
		/// A signal emitted when the base state has changed.
		typedef boost::signal<void ( View3D * )> BaseStateChangedSignal;
		BaseStateChangedSignal &baseStateChangedSignal();

	private :

		void plugSet( const Gaffer::Plug *plug );

		void updateBaseState();

		IECoreGL::StatePtr m_baseState;
		BaseStateChangedSignal m_baseStateChangedSignal;

};

} // namespace GafferUI

#endif // GAFFERUI_VIEW3D_H
