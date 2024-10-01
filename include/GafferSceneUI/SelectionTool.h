//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "GafferSceneUI/Export.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/ScenePlug.h"

#include "GafferUI/DragDropEvent.h"
#include "GafferUI/Tool.h"

#include "Gaffer/StringPlug.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )
IE_CORE_FORWARDDECLARE( SceneGadget )

class GAFFERSCENEUI_API SelectionTool : public GafferUI::Tool
{

	public :

		explicit SelectionTool( SceneView *view, const std::string &name = defaultName<SelectionTool>() );

		~SelectionTool() override;

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::SelectionTool, SelectionToolTypeId, GafferUI::Tool );

		Gaffer::StringPlug *selectModePlug();
		const Gaffer::StringPlug *selectModePlug() const;

		using SelectFunction = std::function<GafferScene::ScenePlug::ScenePath(
			const GafferScene::ScenePlug *,
			const GafferScene::ScenePlug::ScenePath &
		)>;
		// Registers a select mode identified by `name`. `function` must accept
		// the scene from which a selection will be made and the `ScenePath` the user
		// initially selected. It returns the `ScenePath` to use as the actual selection.
		static void registerSelectMode( const std::string &name, SelectFunction function );
		// Returns the names of registered modes, in the order they were registered.
		// The "/Standard" mode will always be first.
		static std::vector<std::string> registeredSelectModes();
		static void deregisterSelectMode( const std::string &mode );

	private :

		static ToolDescription<SelectionTool, SceneView> g_toolDescription;

		void plugSet( Gaffer::Plug *plug );

		SceneGadget *sceneGadget();

		class DragOverlay;
		DragOverlay *dragOverlay();

		bool buttonPress( const GafferUI::ButtonEvent &event );
		bool buttonRelease( const GafferUI::ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event );
		bool dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event );
		bool dragMove( const GafferUI::DragDropEvent &event );
		bool dragEnd( const GafferUI::DragDropEvent &event );

		bool m_acceptedButtonPress = false;
		bool m_initiatedDrag = false;

		static size_t g_firstPlugIndex;
};

} // namespace GafferSceneUI
