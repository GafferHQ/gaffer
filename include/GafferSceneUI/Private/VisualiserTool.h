//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferUI/ButtonEvent.h"
#include "GafferUI/DragDropEvent.h"
#include "GafferUI/KeyEvent.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

#include <variant>

namespace
{

class VisualiserGadget;

}  // namespace

namespace GafferSceneUI
{

class GAFFERSCENEUI_API VisualiserTool : public SelectionTool
{
	public :
		explicit VisualiserTool( SceneView *view, const std::string &name = defaultName<VisualiserTool>() );
		~VisualiserTool() override;

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::VisualiserTool, VisualiserToolTypeId, SelectionTool );

		enum class Mode
		{
			Auto,
			ColorAutoRange,
			Color,
			VertexLabel,

			First = Auto,
			Last = VertexLabel
		};

		Gaffer::StringPlug *dataNamePlug();
		const Gaffer::StringPlug *dataNamePlug() const;

		Gaffer::FloatPlug *opacityPlug();
		const Gaffer::FloatPlug *opacityPlug() const;

		Gaffer::IntPlug *modePlug();
		const Gaffer::IntPlug *modePlug() const;

		Gaffer::V3fPlug *valueMinPlug();
		const Gaffer::V3fPlug *valueMinPlug() const;

		Gaffer::V3fPlug *valueMaxPlug();
		const Gaffer::V3fPlug *valueMaxPlug() const;

		Gaffer::FloatPlug *sizePlug();
		const Gaffer::FloatPlug *sizePlug() const;

		Gaffer::FloatPlug *vectorScalePlug();
		const Gaffer::FloatPlug *vectorScalePlug() const;

		Gaffer::Color3fPlug *vectorColorPlug();
		const Gaffer::Color3fPlug *vectorColorPlug() const;

	private:

		friend VisualiserGadget;

		/// Class encapsulating a selected scene location
		struct Selection
		{
			Selection(
				const GafferScene::ScenePlug &scene,
				const GafferScene::ScenePlug &uniformPScene,
				const GafferScene::ScenePlug::ScenePath &path,
				const Gaffer::Context &context
			);

			const GafferScene::ScenePlug &scene() const;
			const GafferScene::ScenePlug &uniformPScene() const;
			const GafferScene::ScenePlug::ScenePath &path() const;
			const Gaffer::Context &context() const;

			private:

				GafferScene::ConstScenePlugPtr m_scene;
				GafferScene::ConstScenePlugPtr m_uniformPScene;
				GafferScene::ScenePlug::ScenePath m_path;
				Gaffer::ConstContextPtr m_context;
		};

		const std::vector<Selection> &selection() const;

		using CursorPosition = std::optional<Imath::V2f>;
		CursorPosition cursorPos() const;

		using CursorValue = std::variant<std::monostate, int, float, Imath::V2f, Imath::V3f, Imath::Color3f>;
		const CursorValue cursorValue() const;

		GafferScene::ScenePlug *internalScenePlug();
		const GafferScene::ScenePlug *internalScenePlug() const;

		GafferScene::ScenePlug *internalSceneUniformPPlug();
		const GafferScene::ScenePlug *internalSceneUniformPPlug() const;

		void connectOnActive();
		void disconnectOnInactive();
		bool mouseMove( const GafferUI::ButtonEvent &event );
		void enter( const GafferUI::ButtonEvent &event );
		void leave( const GafferUI::ButtonEvent &event );
		bool keyPress( const GafferUI::KeyEvent &event );
		bool buttonPress( const GafferUI::ButtonEvent &event );
		bool buttonRelease( const GafferUI::ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( const GafferUI::DragDropEvent &event );
		bool dragEnd( const GafferUI::DragDropEvent &event );
		void plugDirtied( const Gaffer::Plug *plug );
		void plugSet( const Gaffer::Plug *plug );
		void updateSelection() const;
		void preRender();
		void updateCursorPos( const GafferUI::ButtonEvent &event );
		void updateCursorValue();
		SceneGadget *sceneGadget();
		const SceneGadget *sceneGadget() const;

		void contextChanged();
		void selectedPathsChanged();

		void makeGadgetFirst();

		Gaffer::Signals::ScopedConnection m_preRenderConnection;
		Gaffer::Signals::ScopedConnection m_buttonPressConnection;
		Gaffer::Signals::ScopedConnection m_dragBeginConnection;

		GafferUI::GadgetPtr m_gadget;
		mutable std::vector<Selection> m_selection;
		CursorPosition m_cursorPos;
		CursorValue m_cursorValue;
		bool m_gadgetDirty;
		mutable bool m_selectionDirty;
		bool m_priorityPathsDirty;
		CursorValue m_valueAtButtonPress;
		bool m_initiatedDrag;

		static ToolDescription<VisualiserTool, SceneView> m_toolDescription;
		static size_t g_firstPlugIndex;
};

} // namespace GafferSceneUI
