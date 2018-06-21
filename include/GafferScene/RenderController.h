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
#include "GafferScene/RendererAlgo.h"

#include "boost/signals.hpp"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

/// Utility class used to make interactive updates to a Renderer.
class GAFFERSCENE_API RenderController : public boost::signals::trackable
{

	public :

		RenderController( const ConstScenePlugPtr &scene, const Gaffer::ConstContextPtr &context, IECoreScenePreview::RendererPtr &renderer );
		~RenderController();

		IECoreScenePreview::Renderer *renderer();

		void setScene( const ConstScenePlugPtr &scene );
		const ScenePlug *getScene() const;

		void setContext( const Gaffer::ConstContextPtr &context );
		const Gaffer::Context *getContext() const;

		typedef boost::signal<void (RenderController &)> UpdateRequiredSignal;
		UpdateRequiredSignal &updateRequiredSignal();

		bool updateRequired() const;

		void update();

	private :

		void plugDirtied( const Gaffer::Plug *plug );
		void contextChanged( const IECore::InternedString &name );
		void requestUpdate();

		void updateDefaultCamera();

		class SceneGraph;
		class SceneGraphUpdateTask;

		ConstScenePlugPtr m_scene;
		Gaffer::ConstContextPtr m_context;
		IECoreScenePreview::RendererPtr m_renderer;

		boost::signals::scoped_connection m_plugDirtiedConnection;
		boost::signals::scoped_connection m_contextChangedConnection;

		UpdateRequiredSignal m_updateRequiredSignal;
		bool m_updateRequired;

		std::vector<std::unique_ptr<SceneGraph> > m_sceneGraphs;
		unsigned m_dirtyComponents;
		IECore::ConstCompoundObjectPtr m_globals;
		RendererAlgo::RenderSets m_renderSets;
		IECoreScenePreview::Renderer::ObjectInterfacePtr m_defaultCamera;

};

} // namespace GafferScene

#endif // GAFFERSCENE_RENDERCONTROLLER_H
