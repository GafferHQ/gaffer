//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014-2016, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENEUI_TRANSLATETOOL_H
#define GAFFERSCENEUI_TRANSLATETOOL_H

#include "Gaffer/NumericPlug.h"

#include "GafferSceneUI/Export.h"
#include "GafferSceneUI/TypeIds.h"
#include "GafferSceneUI/TransformTool.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )

class GAFFERSCENEUI_API TranslateTool : public TransformTool
{

	public :

		TranslateTool( SceneView *view, const std::string &name = defaultName<TranslateTool>() );
		virtual ~TranslateTool();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferSceneUI::TranslateTool, TranslateToolTypeId, TransformTool );

		Gaffer::IntPlug *orientationPlug();
		const Gaffer::IntPlug *orientationPlug() const;

		/// Translates by the world space offset in the directions
		/// specified by the current orientation,
		/// as if the user had dragged the handles interactively.
		/// This is primarily of use in the unit tests.
		void translate( const Imath::V3f &offset );

	protected :

		virtual bool affectsHandles( const Gaffer::Plug *input ) const;
		virtual void updateHandles();

	private :

		Imath::M44f handlesTransform() const;

		// The guts of the translation logic. This is factored out of the
		// drag handling so it can be shared with the `translate()` public
		// method.
		struct Translation
		{
			Imath::V3f origin;
			Imath::V3f direction;
		};

		Translation createTranslation( const Imath::V3f &directionInHandleSpace );
		void applyTranslation( const Translation &translation, float offset );

		// Drag handling.

		IECore::RunTimeTypedPtr dragBegin( int axis );
		bool dragMove( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event );
		bool dragEnd();

		Translation m_drag;

		static ToolDescription<TranslateTool, SceneView> g_toolDescription;
		static size_t g_firstPlugIndex;

};

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_TRANSLATETOOL_H
