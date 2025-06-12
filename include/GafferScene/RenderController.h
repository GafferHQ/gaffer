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

#pragma once

#include "GafferScene/Export.h"
#include "GafferScene/VisibleSet.h"

#include "Gaffer/Signals.h"

#include "GafferScene/RenderManifest.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/Private/RendererAlgo.h"

#include "Gaffer/BackgroundTask.h"

#include <atomic>
#include <functional>

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

/// Utility class used to make interactive updates to a Renderer.
class GAFFERSCENE_API RenderController : public Gaffer::Signals::Trackable
{

	public :

		RenderController( const ConstScenePlugPtr &scene, const Gaffer::ConstContextPtr &context, const IECoreScenePreview::RendererPtr &renderer );
		~RenderController() override;

		// Renderer, scene and expansion
		// =============================

		IECoreScenePreview::Renderer *renderer();

		void setScene( const ConstScenePlugPtr &scene );
		const ScenePlug *getScene() const;

		void setContext( const Gaffer::ConstContextPtr &context );
		const Gaffer::Context *getContext() const;

		void setVisibleSet( const GafferScene::VisibleSet &visibleSet );
		const GafferScene::VisibleSet &getVisibleSet() const;

		void setMinimumExpansionDepth( size_t depth );
		size_t getMinimumExpansionDepth() const;

		// Update
		// ======

		using UpdateRequiredSignal = Gaffer::Signals::Signal<void ( RenderController & )>;
		UpdateRequiredSignal &updateRequiredSignal();

		bool updateRequired() const;

		using ProgressCallback = std::function<void (Gaffer::BackgroundTask::Status)>;

		void update( const ProgressCallback &callback = ProgressCallback() );
		std::shared_ptr<Gaffer::BackgroundTask> updateInBackground( const ProgressCallback &callback = ProgressCallback(), const IECore::PathMatcher &priorityPaths = IECore::PathMatcher()  );

		void updateMatchingPaths( const IECore::PathMatcher &pathsToUpdate, const ProgressCallback &callback = ProgressCallback() );

		// Manifest
		// ========
		//
		// Allows IDs acquired from a standard `id` AOV to be mapped
		// back to the scene paths they came from.
		std::shared_ptr<RenderManifest> renderManifest();
		std::shared_ptr<const RenderManifest> renderManifest() const;

		// Controls if a manifest is needed even without any id Outputs.
		// ( Needed by SceneView which creates Outputs itself without the controller knowing )
		void setManifestRequired( bool manifestRequired );
		bool getManifestRequired();


	private :

		enum GlobalComponents
		{
			NoGlobalComponent = 0,
			GlobalsGlobalComponent = 1,
			SetsGlobalComponent = 2,
			RenderSetsGlobalComponent = 4,
			CameraOptionsGlobalComponent = 8,
			TransformBlurGlobalComponent = 16,
			DeformationBlurGlobalComponent = 32,
			CameraShutterGlobalComponent = 64,
			IncludedPurposesGlobalComponent = 128,
			IDGlobalComponent = 256,
			CapsuleAffectingGlobalComponents = TransformBlurGlobalComponent | DeformationBlurGlobalComponent | IncludedPurposesGlobalComponent,
			AllGlobalComponents = GlobalsGlobalComponent | SetsGlobalComponent | RenderSetsGlobalComponent | CameraOptionsGlobalComponent | TransformBlurGlobalComponent | DeformationBlurGlobalComponent | IncludedPurposesGlobalComponent | IDGlobalComponent
		};

		void plugDirtied( const Gaffer::Plug *plug );
		void contextChanged( const IECore::InternedString &name );
		void requestUpdate();
		void dirtyGlobals( unsigned components );
		void dirtySceneGraphs( unsigned components );

		void updateInternal( const ProgressCallback &callback = ProgressCallback(), const IECore::PathMatcher *pathsToUpdate = nullptr, bool signalCompletion = true );
		void updateDefaultCamera();
		void cancelBackgroundTask();

		class SceneGraph;
		class SceneGraphUpdateTask;

		ConstScenePlugPtr m_scene;
		Gaffer::ConstContextPtr m_context;
		IECoreScenePreview::RendererPtr m_renderer;


		GafferScene::VisibleSet m_visibleSet;
		size_t m_minimumExpansionDepth;

		Gaffer::Signals::ScopedConnection m_plugDirtiedConnection;
		Gaffer::Signals::ScopedConnection m_contextChangedConnection;

		UpdateRequiredSignal m_updateRequiredSignal;
		bool m_updateRequired;
		bool m_updateRequested;
		std::atomic<uint64_t> m_failedAttributeEdits;

		std::vector<std::unique_ptr<SceneGraph> > m_sceneGraphs;
		unsigned m_dirtyGlobalComponents;
		unsigned m_changedGlobalComponents;
		Private::RendererAlgo::RenderOptions m_renderOptions;
		Private::RendererAlgo::RenderSets m_renderSets;
		std::unique_ptr<Private::RendererAlgo::LightLinks> m_lightLinks;
		IECoreScenePreview::Renderer::ObjectInterfacePtr m_defaultCamera;
		IECoreScenePreview::Renderer::AttributesInterfacePtr m_defaultAttributes;

		std::shared_ptr<Gaffer::BackgroundTask> m_backgroundTask;

		bool m_manifestRequired;
		std::shared_ptr<RenderManifest> m_renderManifest;

};

} // namespace GafferScene
