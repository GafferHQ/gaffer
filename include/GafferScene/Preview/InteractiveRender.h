//////////////////////////////////////////////////////////////////////////
//
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

#ifndef GAFFERSCENE_PREVIEW_INTERACTIVERENDER_H
#define GAFFERSCENE_PREVIEW_INTERACTIVERENDER_H

#include "Gaffer/Node.h"

#include "GafferScene/ScenePlug.h"
#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

namespace Preview
{

class InteractiveRender : public Gaffer::Node
{

	public :

		InteractiveRender( const std::string &name=defaultName<InteractiveRender>() );
		virtual ~InteractiveRender();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::Preview::InteractiveRender, GafferScene::PreviewInteractiveRenderTypeId, Gaffer::Node );

		enum State
		{
			Stopped,
			Running,
			Paused
		};

		GafferScene::ScenePlug *inPlug();
		const GafferScene::ScenePlug *inPlug() const;

		Gaffer::StringPlug *rendererPlug();
		const Gaffer::StringPlug *rendererPlug() const;

		Gaffer::IntPlug *statePlug();
		const Gaffer::IntPlug *statePlug() const;

		GafferScene::ScenePlug *outPlug();
		const GafferScene::ScenePlug *outPlug() const;

		/// The Context in which the InteractiveRender should operate.
		Gaffer::Context *getContext();
		const Gaffer::Context *getContext() const;
		void setContext( Gaffer::ContextPtr context );

	protected :

		// Constructor for derived classes which wish to hardcode the renderer type. Perhaps
		// at some point we won't even have derived classes, but instead will always use the
		// base class? At the moment the main purpose of the derived classes is to force the
		// loading of the module which registers the required renderer type.
		InteractiveRender( const IECore::InternedString &rendererType, const std::string &name );

	private :

		void construct( const IECore::InternedString &rendererType = IECore::InternedString() );

		void plugDirtied( const Gaffer::Plug *plug );
		void parentChanged( Gaffer::GraphComponent *child, Gaffer::GraphComponent *oldParent );
		void contextChanged( const IECore::InternedString &name );

		void update();
		void stop();

		class SceneGraph;
		class SceneGraphUpdateTask;

		std::vector<boost::shared_ptr<SceneGraph> > m_sceneGraphs;
		IECoreScenePreview::RendererPtr m_renderer;
		State m_state;
		unsigned m_dirtyFlags;
		IECore::ConstCompoundObjectPtr m_globals;
		IECore::ConstCompoundObjectPtr m_globalAttributes;
		GafferScene::PathMatcher m_lightSet;
		GafferScene::PathMatcher m_cameraSet;

		Gaffer::ContextPtr m_context;
		boost::signals::scoped_connection m_contextChangedConnection;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( InteractiveRender );

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<InteractiveRender> > InteractiveRenderIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<InteractiveRender> > RecursiveInteractiveRenderIterator;

} // namespace Preview

} // namespace GafferScene

#endif // GAFFERSCENE_PREVIEW_INTERACTIVERENDER_H
