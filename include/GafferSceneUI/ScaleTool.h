//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENEUI_SCALETOOL_H
#define GAFFERSCENEUI_SCALETOOL_H

#include "GafferUI/Style.h"

#include "GafferSceneUI/Export.h"
#include "GafferSceneUI/TransformTool.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )

class GAFFERSCENEUI_API ScaleTool : public TransformTool
{

	public :

		ScaleTool( SceneView *view, const std::string &name = defaultName<ScaleTool>() );
		~ScaleTool() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferSceneUI::ScaleTool, ScaleToolTypeId, TransformTool );

		/// Scales the current selection as if the handles
		/// had been dragged interactively. Exists mainly for
		/// use in the unit tests.
		void scale( const Imath::V3f &scale );

	protected :

		bool affectsHandles( const Gaffer::Plug *input ) const override;
		void updateHandles() override;

	private :

		// The guts of the scaling logic. This is factored out of the
		// drag handling so it can be shared with the `scale()` public
		// method.
		struct Scale
		{
			Imath::V3f originalScale;
			GafferUI::Style::Axes axes;
		};

		Scale createScale( GafferUI::Style::Axes axes );
		void applyScale( const Scale &scale, float s );

		// Drag handling.

		IECore::RunTimeTypedPtr dragBegin( GafferUI::Style::Axes axes );
		bool dragMove( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event );
		bool dragEnd();

		Scale m_drag;

		static ToolDescription<ScaleTool, SceneView> g_toolDescription;

};

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_SCALETOOL_H
