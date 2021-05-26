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

#ifndef GAFFERSCENE_RENDERCONTROLLER_H
#define GAFFERSCENE_RENDERCONTROLLER_H

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/Private/RendererAlgo.h"

#include "Gaffer/BackgroundTask.h"

#include "boost/signals.hpp"

#include <atomic>
#include <functional>

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

/// Utility class used to make interactive updates to a Renderer.
class GAFFERSCENE_API RenderController : public boost::signals::trackable
{

	public :

		RenderController( const ConstScenePlugPtr &scene, const Gaffer::ConstContextPtr &context, const IECoreScenePreview::RendererPtr &renderer );
		~RenderController();

		IECoreScenePreview::Renderer *renderer();

		void setScene( const ConstScenePlugPtr &scene );
		const ScenePlug *getScene() const;

		void setContext( const Gaffer::ConstContextPtr &context );
		const Gaffer::Context *getContext() const;

		void setExpandedPaths( const IECore::PathMatcher &expandedPaths );
		const IECore::PathMatcher &getExpandedPaths() const;

		void setMinimumExpansionDepth( size_t depth );
		size_t getMinimumExpansionDepth() const;

		typedef boost::signal<void (RenderController &)> UpdateRequiredSignal;
		UpdateRequiredSignal &updateRequiredSignal();

		bool updateRequired() const;

		typedef std::function<void ( Gaffer::BackgroundTask::Status progress )> ProgressCallback;

		void update( const ProgressCallback &callback = ProgressCallback() );
		std::shared_ptr<Gaffer::BackgroundTask> updateInBackground( const ProgressCallback &callback = ProgressCallback(), const IECore::PathMatcher &priorityPaths = IECore::PathMatcher()  );

		void updateMatchingPaths( const IECore::PathMatcher &pathsToUpdate, const ProgressCallback &callback = ProgressCallback() );

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
			AllGlobalComponents = GlobalsGlobalComponent | SetsGlobalComponent | RenderSetsGlobalComponent | CameraOptionsGlobalComponent | TransformBlurGlobalComponent | DeformationBlurGlobalComponent
		};

		struct MotionBlurOptions
		{
			bool transformBlur = false;
			bool deformationBlur = false;
			Imath::V2f shutter = Imath::V2f( 0 );
		};

		void plugDirtied( const Gaffer::Plug *plug );
		void contextChanged( const IECore::InternedString &name );
		void requestUpdate();
		void dirtyGlobals( unsigned components );
		void dirtySceneGraphs( unsigned components );

		void updateInternal( const ProgressCallback &callback = ProgressCallback(), const IECore::PathMatcher *pathsToUpdate = nullptr );
		void updateDefaultCamera();
		void cancelBackgroundTask();

		class SceneGraph;
		class SceneGraphUpdateTask;

		ConstScenePlugPtr m_scene;
		Gaffer::ConstContextPtr m_context;
		IECoreScenePreview::RendererPtr m_renderer;

		IECore::PathMatcher m_expandedPaths;
		size_t m_minimumExpansionDepth;

		boost::signals::scoped_connection m_plugDirtiedConnection;
		boost::signals::scoped_connection m_contextChangedConnection;

		UpdateRequiredSignal m_updateRequiredSignal;
		bool m_updateRequired;
		bool m_updateRequested;
		std::atomic<uint64_t> m_failedAttributeEdits;

		std::vector<std::unique_ptr<SceneGraph> > m_sceneGraphs;
		unsigned m_dirtyGlobalComponents;
		unsigned m_changedGlobalComponents;
		IECore::ConstCompoundObjectPtr m_globals;
		MotionBlurOptions m_motionBlurOptions;
		Private::RendererAlgo::RenderSets m_renderSets;
		std::unique_ptr<Private::RendererAlgo::LightLinks> m_lightLinks;
		IECoreScenePreview::Renderer::ObjectInterfacePtr m_defaultCamera;
		IECoreScenePreview::Renderer::AttributesInterfacePtr m_boundAttributes;

		std::shared_ptr<Gaffer::BackgroundTask> m_backgroundTask;

};

} // namespace GafferScene

#endif // GAFFERSCENE_RENDERCONTROLLER_H
