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

#ifndef GAFFERSCENEUI_CAMERATOOL_H
#define GAFFERSCENEUI_CAMERATOOL_H

#include "GafferSceneUI/TransformTool.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferUI/KeyEvent.h"

#include "Gaffer/StringPlug.h"

#include <unordered_map>

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( SceneView )

class GAFFERSCENEUI_API CameraTool : public GafferSceneUI::SelectionTool
{

	public :

		CameraTool( SceneView *view, const std::string &name = defaultName<CameraTool>() );
		~CameraTool() override;

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::CameraTool, CameraToolTypeId, GafferSceneUI::SelectionTool );

	private :

		const GafferScene::ScenePlug *scenePlug() const;
		const Gaffer::BoolPlug *lookThroughEnabledPlug() const;
		const Gaffer::StringPlug *lookThroughCameraPlug() const;

		void connectToViewContext();
		void contextChanged( const IECore::InternedString &name );

		boost::signals::scoped_connection m_contextChangedConnection;

		void plugDirtied( const Gaffer::Plug *plug );
		GafferScene::ScenePlug::ScenePath cameraPath() const;
		const TransformTool::Selection &cameraSelection();
		void preRenderBegin();
		void preRenderEnd();

		TransformTool::Selection m_cameraSelection;
		bool m_cameraSelectionDirty;

		IECore::RunTimeTypedPtr viewportDragBegin( const GafferUI::DragDropEvent &event );
		bool viewportWheel( const GafferUI::ButtonEvent &event );
		bool viewportKeyPress( const GafferUI::KeyEvent &event );
		bool viewportButtonPress( const GafferUI::ButtonEvent &event );

		size_t m_dragId;
		std::string m_undoGroup;

		void viewportCameraChanged();

		boost::signals::connection m_viewportCameraChangedConnection;

		void setCameraCenterOfInterest( const GafferScene::ScenePlug::ScenePath &camera, float centerOfInterest );
		float getCameraCenterOfInterest( const GafferScene::ScenePlug::ScenePath &camera ) const;

		typedef std::unordered_map<std::string, float> CameraCentersOfInterest;
		CameraCentersOfInterest m_cameraCentersOfInterest;

		static ToolDescription<CameraTool, SceneView> g_toolDescription;
		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( CameraTool )

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_CAMERATOOL_H
