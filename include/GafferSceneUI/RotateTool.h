//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENEUI_ROTATETOOL_H
#define GAFFERSCENEUI_ROTATETOOL_H

#include "GafferSceneUI/TransformTool.h"

#include "GafferUI/Style.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathEuler.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )

class GAFFERSCENEUI_API RotateTool : public TransformTool
{

	public :

		RotateTool( SceneView *view, const std::string &name = defaultName<RotateTool>() );
		~RotateTool() override;

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::RotateTool, RotateToolTypeId, TransformTool );

		Gaffer::IntPlug *orientationPlug();
		const Gaffer::IntPlug *orientationPlug() const;

		/// Rotates the current selection as if the handles
		/// had been dragged interactively. Exists mainly
		/// for use in the unit tests.
		void rotate( const Imath::Eulerf &degrees );

	protected :

		bool affectsHandles( const Gaffer::Plug *input ) const override;
		void updateHandles( float rasterScale ) override;

	private :

		// The guts of the rotation logic. This is factored out of the
		// drag handling so it can be shared with the `rotate()` public
		// method.
		struct Rotation
		{

			Rotation( const Selection &selection, Orientation orientation );

			bool canApply( const Imath::V3i &axisMask ) const;
			void apply( const Imath::Eulerf &rotation );

			private :

				Imath::V3f updatedRotateValue( const Gaffer::V3fPlug *rotatePlug, const Imath::Eulerf &rotation, Imath::V3f *currentValue = nullptr ) const;

				// For the validity of this reference, we rely
				// on `TransformTool::selection()` not changing
				// during drags.
				const Selection &m_selection;
				Imath::M44f m_gadgetToTransform;

				// Initialised lazily when we first
				// acquire the transform plug.
				mutable boost::optional<Imath::Eulerf> m_originalRotation; // Radians

		};

		// Handle Drag handling.

		IECore::RunTimeTypedPtr handleDragBegin();
		bool handleDragMove( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event );
		bool handleDragEnd();

		// Target mode handling

		bool keyPress( const GafferUI::KeyEvent &event );
		bool keyRelease( const GafferUI::KeyEvent &event );
		void sceneGadgetLeave( const GafferUI::ButtonEvent &event );
		void visibilityChanged( GafferUI::Gadget *gadget );
		void plugSet( Gaffer::Plug *plug );

		bool buttonPress( const GafferUI::ButtonEvent &event );

		void setTargetedMode( bool targeted );
		bool getTargetedMode() const { return m_targetedMode; }
		bool m_targetedMode;

		std::vector<Rotation> m_drag;

		static ToolDescription<RotateTool, SceneView> g_toolDescription;
		static size_t g_firstPlugIndex;

};

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_ROTATETOOL_H
