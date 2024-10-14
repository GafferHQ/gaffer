//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
#include "GafferSceneUI/SelectionTool.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/ScenePlug.h"

#include "GafferUI/Gadget.h"

#include "Gaffer/ScriptNode.h"

#include "IECore/InternedString.h"
#include "IECore/PathMatcher.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )

class GAFFERSCENEUI_API LightTool : public GafferSceneUI::SelectionTool
{

	public :

		LightTool( SceneView *view, const std::string &name = defaultName<LightTool>() );
		~LightTool() override;

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::LightTool, LightToolTypeId, SelectionTool );

	private :

		GafferScene::ScenePlug *scenePlug();
		const GafferScene::ScenePlug *scenePlug() const;

		void contextChanged();
		void selectedPathsChanged();
		void metadataChanged( IECore::InternedString key );
		void updateHandleInspections();
		void updateHandleTransforms( float rasterScale );
		void plugDirtied( const Gaffer::Plug *plug );
		void preRender();
		void dirtyHandleTransforms();

		IECore::RunTimeTypedPtr dragBegin( GafferUI::Gadget *gadget );
		bool dragMove( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event );
		bool dragEnd( GafferUI::Gadget *gadget );

		std::string undoMergeGroup() const;

		GafferUI::GadgetPtr m_handles;
		bool m_handleInspectionsDirty;
		bool m_handleTransformsDirty;

		bool m_priorityPathsDirty;

		bool m_dragging;

		Gaffer::Signals::ScopedConnection m_preRenderConnection;

		std::vector<Gaffer::Signals::ScopedConnection> m_inspectorsDirtiedConnection;

		int m_mergeGroupId;

		static ToolDescription<LightTool, SceneView> g_toolDescription;
		static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( LightTool )

}  // namespace GafferSceneUI
