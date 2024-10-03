//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2014, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
#include "GafferSceneUI/SceneGadget.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/PathFilter.h"
#include "GafferScene/ScenePlug.h"

#include "GafferUI/FPSGadget.h"
#include "GafferUI/View.h"

#include <functional>

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( SceneProcessor )

} // namespace GafferScene

namespace GafferSceneUI
{

/// \todo As we add more features to the View classes, they're feeling a
/// bit monolithic, and not in the modular "plug it together how you like"
/// spirit of the rest of Gaffer. Internally the various features are implemented
/// as their own little classes though, so perhaps it would make sense to expose
/// these in the public API as optional "bolt on" components that applications can
/// use as they see fit. If we do this, we need to consider how these relate to
/// Tools, which could also be seen as viewer components.
class GAFFERSCENEUI_API SceneView : public GafferUI::View
{

	public :

		explicit SceneView( Gaffer::ScriptNodePtr scriptNode );
		~SceneView() override;

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::SceneView, SceneViewTypeId, GafferUI::View );

		Gaffer::IntPlug *minimumExpansionDepthPlug();
		const Gaffer::IntPlug *minimumExpansionDepthPlug() const;

		Gaffer::ValuePlug *cameraPlug();
		const Gaffer::ValuePlug *cameraPlug() const;

		Gaffer::ValuePlug *gnomonPlug();
		const Gaffer::ValuePlug *gnomonPlug() const;

		void frame( const IECore::PathMatcher &filter, const Imath::V3f &direction = Imath::V3f( -0.64, -0.422, -0.64 ) );
		void expandSelection( size_t depth = 1 );
		void collapseSelection();

		/// If the view is locked to a particular camera,
		/// this returns the bound of the resolution gate
		/// in raster space - this can be useful when
		/// drawing additional overlays. If the view is not
		/// locked to a particular camera then returns an
		/// empty bound.
		const Imath::Box2f &resolutionGate() const;

		using ShadingModeCreator = std::function<GafferScene::SceneProcessorPtr ()>;

		static void registerShadingMode( const std::string &name, ShadingModeCreator );
		static void registeredShadingModes( std::vector<std::string> &names );

		using RendererSettingsCreator = std::function<GafferScene::SceneProcessorPtr ()>;
		static void registerRenderer( const std::string &name, const RendererSettingsCreator &settingsCreator );
		static std::vector<std::string> registeredRenderers();

	private :

		// The filter for a preprocessing node used to hide things.
		GafferScene::PathFilter *deleteObjectFilter();
		const GafferScene::PathFilter *deleteObjectFilter() const;

		Imath::Box3f framingBound() const;

		void contextChanged();
		void selectedPathsChanged();
		void visibleSetChanged();
		bool keyPress( GafferUI::GadgetPtr gadget, const GafferUI::KeyEvent &event );
		void plugSet( Gaffer::Plug *plug );

		SceneGadgetPtr m_sceneGadget;

		/// \todo Refactor all these bolt-on classes to follow the model of
		/// `View::DisplayTransform` and `SceneView::Grid` :
		///
		/// - Derive from `Node`, and add child plugs to provide settings.
		/// - Parent under the `View` and promote settings plugs to the view.
		class Renderer;
		std::unique_ptr<Renderer> m_renderer;
		class SelectionMask;
		std::unique_ptr<SelectionMask> m_selectionMask;
		class DrawingMode;
		std::unique_ptr<DrawingMode> m_drawingMode;
		class ShadingMode;
		std::unique_ptr<ShadingMode> m_shadingMode;
		class Camera;
		std::unique_ptr<Camera> m_camera;
		class Grid;
		class Gnomon;
		std::unique_ptr<Gnomon> m_gnomon;
		class FPS;
		std::unique_ptr<FPS> m_fps;

		static size_t g_firstPlugIndex;
		static ViewDescription<SceneView> g_viewDescription;

};

IE_CORE_DECLAREPTR( SceneView );

} // namespace GafferSceneUI
