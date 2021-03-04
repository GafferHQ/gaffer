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

#ifndef GAFFERSCENE_INTERACTIVERENDER_H
#define GAFFERSCENE_INTERACTIVERENDER_H

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/RenderController.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/TypedObjectPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferScene
{

class GAFFERSCENE_API InteractiveRender : public Gaffer::ComputeNode
{

	public :

		InteractiveRender( const std::string &name=defaultName<InteractiveRender>() );
		~InteractiveRender() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::InteractiveRender, GafferScene::InteractiveRenderTypeId, Gaffer::ComputeNode );

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

		Gaffer::ObjectPlug *messagesPlug();
		const Gaffer::ObjectPlug *messagesPlug() const;

		/// Specifies a context in which the InteractiveRender should operate.
		/// The default is null, meaning that the context of the ancestor
		/// ScriptNode will be used, or failing that, a default context.
		void setContext( Gaffer::ContextPtr context );
		Gaffer::Context *getContext();
		const Gaffer::Context *getContext() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		// Constructor for derived classes which wish to hardcode the renderer type. Perhaps
		// at some point we won't even have derived classes, but instead will always use the
		// base class? At the moment the main purpose of the derived classes is to force the
		// loading of the module which registers the required renderer type.
		InteractiveRender( const IECore::InternedString &rendererType, const std::string &name );

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

		bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const override;

	private :

		ScenePlug *adaptedInPlug();
		const ScenePlug *adaptedInPlug() const;

		Gaffer::IntPlug *messageUpdateCountPlug();
		const Gaffer::IntPlug *messageUpdateCountPlug() const;

		void messagesChanged();
		static void messagesChangedUI();

		void plugSet( const Gaffer::Plug *plug );

		void update();
		Gaffer::ConstContextPtr effectiveContext();
		void stop();

		IECoreScenePreview::RendererPtr m_renderer;
		std::unique_ptr<RenderController> m_controller;
		State m_state;

		Gaffer::ContextPtr m_context;

		IE_CORE_FORWARDDECLARE( RenderMessageHandler )
		RenderMessageHandlerPtr  m_messageHandler;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( InteractiveRender );

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<InteractiveRender> > InteractiveRenderIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<InteractiveRender> > RecursiveInteractiveRenderIterator;

} // namespace GafferScene

#endif // GAFFERSCENE_INTERACTIVERENDER_H
