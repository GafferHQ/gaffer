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

#include "GafferScene/InteractiveRender.h"

#include "GafferScene/OptionTweaks.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneNode.h"
#include "GafferScene/SceneProcessor.h"
#include "GafferScene/VisibleSetData.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "Gaffer/Private/IECorePreview/Messages.h"

#include "IECoreScene/VisibleRenderable.h"

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"

#include "tbb/mutex.h"

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

using HandlerSet = set<MessageHandlerPtr>;
using HandlerSetPtr = std::unique_ptr<HandlerSet>;

struct PendingUpdates
{
	tbb::spin_mutex mutex;
	HandlerSetPtr handlers;
};

PendingUpdates &pendingUpdates()
{
	static PendingUpdates *p = new PendingUpdates;
	return *p;
}

const InternedString g_rendererOptionName( "option:render:defaultRenderer" );
const InternedString g_renderCameraOptionName( "option:render:camera" );
const InternedString g_visibleSetName( "ui:scene:visibleSet" );
const VisibleSet g_defaultVisibleSet = VisibleSet();

unordered_set<string> &activeRenderIds()
{
	static unordered_set<string> g_activeRenderIds;
	return g_activeRenderIds;
}

} // namespace

// A thread-safe message handler for render messaging
class InteractiveRender::RenderMessageHandler : public MessageHandler
{
	public :

		RenderMessageHandler( InteractiveRender *node )
			:	m_node( node )
		{
		}

		void handle( MessageHandler::Level level, const std::string &context, const std::string &message  ) override
		{
			// Always forward to the default handler for visibility outside of the UI
			MessageHandler::getDefaultHandler()->handle( level, context, message );

			{
				tbb::mutex::scoped_lock lock( m_mutex );
				m_messages.add( IECorePreview::Message( level, context, message ) );
			}

			messagesChangedSignal();
		}

		IECorePreview::Messages messages()
		{
			tbb::mutex::scoped_lock lock( m_mutex );
			return m_messages;
		}

		void clear()
		{
			{
				tbb::mutex::scoped_lock lock( m_mutex );
				m_messages.clear();
			}

			messagesChangedSignal();
		}

		Signals::Signal<void ()> messagesChangedSignal;

		InteractiveRender *node() const
		{
			return m_node;
		}

		void nodeDestroyed()
		{
			m_node = nullptr;
		}

	private :

		tbb::mutex m_mutex;
		IECorePreview::Messages m_messages;
		InteractiveRender *m_node;
};

static InternedString g_rendererContextName( "scene:renderer" );

size_t InteractiveRender::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( InteractiveRender );

InteractiveRender::InteractiveRender( const std::string &name )
	:	ComputeNode( name ),
		m_state( Stopped ),
		m_messageHandler( new RenderMessageHandler( this ) )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
	addChild( new StringPlug( "renderer" ) );
	addChild( new IntPlug( "state", Plug::In, Stopped, Stopped, Paused, Plug::Default & ~Plug::Serialisable ) );
	addChild( new BoolPlug( "useVisibleSet" ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	addChild( new StringPlug( "resolvedRenderer", Plug::Out, "", Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "__adaptedIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	SceneProcessorPtr adaptors = SceneAlgo::createRenderAdaptors();
	setChild( "__adaptors", adaptors );
	adaptors->inPlug()->setInput( inPlug() );
	adaptors->getChild<StringPlug>( "client" )->setValue( "InteractiveRender" );
	adaptors->getChild<StringPlug>( "renderer" )->setInput( resolvedRendererPlug() );
	adaptedInPlug()->setInput( adaptors->outPlug() );

	OptionTweaksPtr optionTweaks = new OptionTweaks();
	setChild( "__optionTweaks", optionTweaks );
	optionTweaks->inPlug()->setInput( inPlug() );

	TweakPlugPtr tweakPlug = new TweakPlug( "render:defaultRenderer", new StringPlug(), TweakPlug::CreateIfMissing );
	tweakPlug->valuePlug()->setInput( rendererPlug() );
	optionTweaks->tweaksPlug()->addChild( tweakPlug );

	outPlug()->setInput( optionTweaks->outPlug() );

	plugDirtiedSignal().connect( boost::bind( &InteractiveRender::plugDirtied, this, ::_1 ) );

	m_messageHandler->messagesChangedSignal.connect( boost::bind( &InteractiveRender::messagesChanged, this ) );
}

InteractiveRender::~InteractiveRender()
{
	m_messageHandler->nodeDestroyed();
	stop();
}

ScenePlug *InteractiveRender::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *InteractiveRender::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *InteractiveRender::rendererPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *InteractiveRender::rendererPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *InteractiveRender::statePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *InteractiveRender::statePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *InteractiveRender::useVisibleSetPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *InteractiveRender::useVisibleSetPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

ScenePlug *InteractiveRender::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 4 );
}

const ScenePlug *InteractiveRender::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *InteractiveRender::resolvedRendererPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *InteractiveRender::resolvedRendererPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

ScenePlug *InteractiveRender::adaptedInPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 6 );
}

const ScenePlug *InteractiveRender::adaptedInPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 6 );
}

Gaffer::Context *InteractiveRender::getContext()
{
	return m_context.get();
}

const Gaffer::Context *InteractiveRender::getContext() const
{
	return m_context.get();
}

void InteractiveRender::setContext( Gaffer::ContextPtr context )
{
	if( m_context == context )
	{
		return;
	}
	m_context = context;
	if( m_controller )
	{
		m_controller->setContext( effectiveContext() );
	}
}

IECore::DataPtr InteractiveRender::command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters )
{
	if( !m_renderer )
	{
		return nullptr;
	}

	IntPlug *stateSourcePlug = statePlug()->source<IntPlug>();
	const State state = (InteractiveRender::State)stateSourcePlug->getValue();
	stateSourcePlug->setValue( Paused );
	DataPtr result = m_renderer->command( name, parameters );
	stateSourcePlug->setValue( state );
	return result;
}

void InteractiveRender::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == rendererPlug() || plug == statePlug() || plug == useVisibleSetPlug() )
	{
		try
		{
			update();
		}
		catch( const std::exception &e )
		{
			m_messageHandler->handle( IECore::MessageHandler::Error, "InteractiveRender", e.what() );
		}
	}
}

void InteractiveRender::update()
{
	ConstContextPtr context = effectiveContext();
	Context::Scope scope( context.get() );

	const State requiredState = (State)statePlug()->getValue();

	// Stop the current render if we've been asked to, or if
	// there is no real input scene.

	if( requiredState == Stopped || inPlug()->source()->direction() != Plug::Out )
	{
		stop();
		return;
	}

	// If we've got this far, we know we want to be running or paused.
	// Start a render if we don't have one.

	if( !m_renderer )
	{
		m_messageHandler->clear();

		/// \todo It'd be great if we could deal with live edits to the `render:defaultRenderer`
		/// option, to switch renderer on the fly. The best way of doing this is probably
		/// to move the renderer creation to the RenderController. That approach would also
		/// allow the RenderController to recreate the renderer when unsupported option edits
		/// are made - for instance, changing `cycles:device`.
		const std::string rendererType = resolvedRendererPlug()->getValue();
		if( rendererType.empty() )
		{
			m_messageHandler->handle(
				IECore::Msg::Error, "InteractiveRender", "`render:defaultRenderer` option not set"
			);
			return;
		}

		m_renderer = IECoreScenePreview::Renderer::create(
			rendererType,
			IECoreScenePreview::Renderer::Interactive,
			"",
			m_messageHandler.get()
		);
		activeRenderIds().insert( Private::RendererAlgo::renderID( m_renderer.get() ) );

		m_controller.reset(
			new RenderController( adaptedInPlug(), effectiveContext(), m_renderer )
		);
		m_updateRequiredConnection = m_controller->updateRequiredSignal().connect(
			boost::bind( &InteractiveRender::update, this )
		);
		m_scriptMetadataChangedConnection = Metadata::nodeValueChangedSignal( scriptNode() ).connect(
			boost::bind( &InteractiveRender::scriptMetadataChanged, this, ::_2 )
		);

		// We can now use a live render manifest from the controller, so get rid of the saved manifest
		m_lastRenderManifest.reset();
	}

	// We need to pause to make edits, even if we want to
	// be running in the end.
	m_renderer->pause();
	if( requiredState == Paused )
	{
		m_state = requiredState;
		return;
	}

	// We want to be running, so update the scene
	// and kick off a render.
	assert( requiredState == Running );

	{
		IECore::MessageHandler::Scope messageScope( m_messageHandler.get() );
		Signals::BlockedConnection blockedConnection( m_updateRequiredConnection );
		if( useVisibleSetPlug()->getValue() )
		{
			// We can't use GafferSceneUI::ScriptNodeAlgo::getVisibleSet() here, so instead
			// we query the metadata directly.
			const auto data = Metadata::value<VisibleSetData>( scriptNode(), g_visibleSetName );
			VisibleSet visibleSet = data ? data->readable() : VisibleSet();
			// As a user convenience, we always include the render camera in the Visible Set
			// to mimic the Visible Set behaviour expected from the Viewer.
			if( ConstStringDataPtr renderCamera = inPlug()->globals()->member<StringData>( g_renderCameraOptionName ) )
			{
				visibleSet.inclusions.addPath( renderCamera->readable() );
			}
			m_controller->setVisibleSet( visibleSet );
			m_controller->setMinimumExpansionDepth( 0 );
		}
		else
		{
			m_controller->setMinimumExpansionDepth( numeric_limits<size_t>::max() );
			m_controller->setVisibleSet( g_defaultVisibleSet );
		}
		m_controller->update();
	}

	m_state = requiredState;
	m_renderer->render();
}

Gaffer::ConstContextPtr InteractiveRender::effectiveContext()
{
	if( m_context )
	{
		return m_context.get();
	}
	else if( ScriptNode *n = ancestor<ScriptNode>() )
	{
		return n->context();
	}
	else
	{
		return new Context();
	}
}

bool InteractiveRender::renderIsActive( const std::string &renderId )
{
	return activeRenderIds().count( renderId );
}

void InteractiveRender::stop()
{
	// A Catalogue may need to access the render manifest as part of saving out the images from this
	// render when it stops. To allow for this, we hold onto the manifest when we release the
	// controller ( which is what triggers the render to stop and the catalogue to save the images to
	// disk ). In theory, we could try to track when the render has finished signalling all catalogues
	// and then release this, but it's much simpler to hold onto it until the next render starts.
	if( m_controller )
	{
		m_lastRenderManifest = m_controller->renderManifest();
	}

	activeRenderIds().erase( Private::RendererAlgo::renderID( m_renderer.get() ) );

	m_scriptMetadataChangedConnection.disconnect();
	m_controller.reset();
	m_renderer.reset();
	m_state = Stopped;

}

void InteractiveRender::scriptMetadataChanged( IECore::InternedString key )
{
	if( key == g_visibleSetName && useVisibleSetPlug()->getValue() )
	{
		update();
	}
}

// Called on whichever thread handled the message. `messagesChangedSignal()`
// must be emitted on the UI thread, so we can't do it directly.
void InteractiveRender::messagesChanged()
{
	bool scheduleUpdate = false;
	{
		// To minimise overhead we perform updates in batches by storing
		// a set of handlers which are pending update. If we're the creator
		// of a new batch then we are responsible for scheduling a call
		// to `messagesChangedUI()` to process the batch. Otherwise we just
		// add to the current batch.
		PendingUpdates &pending = pendingUpdates();
		tbb::spin_mutex::scoped_lock lock( pending.mutex );
		if( !pending.handlers.get() )
		{
			scheduleUpdate = true;
			pending.handlers.reset( new HandlerSet );
		}
		pending.handlers->insert( m_messageHandler );
	}
	if( scheduleUpdate )
	{
		ParallelAlgo::callOnUIThread( &InteractiveRender::messagesChangedUI );
	}
}

// Called on the UI thread after being scheduled by `messagesChanged()`.
void InteractiveRender::messagesChangedUI()
{
	// Get the batch of nodes to signal updates for. We want to hold the mutex
	// for the shortest duration possible, because it causes contention between
	// the background rendering thread and the UI thread, and can significantly
	// affect performance.  We do this by "stealing" the current batch, so the
	// background thread will create a new batch and we are safe to iterate our
	// batch without holding the lock.
	HandlerSetPtr batch;
	{
		PendingUpdates &pending = pendingUpdates();
		tbb::spin_mutex::scoped_lock lock( pending.mutex );
		batch.reset( pending.handlers.release() );
	}

	// Now signal the render nodes that have received new messages.
	for( const auto &handler : *batch )
	{
		// Because `messagesChangedUI()` is deferred to the UI thread,
		// it's possible that the node has actually been deleted by
		// the time we're called, so we must check.
		if( InteractiveRender *node = static_cast<RenderMessageHandler *>( handler.get() )->node() )
		{
			node->m_messagesChangedSignal( node );
		}
	}
}

IECorePreview::Messages InteractiveRender::messages() const
{
	return m_messageHandler->messages();
}

InteractiveRender::InteractiveRenderSignal &InteractiveRender::messagesChangedSignal()
{
	return m_messagesChangedSignal;
}

void InteractiveRender::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == rendererPlug() || input == inPlug()->globalsPlug() )
	{
		outputs.push_back( resolvedRendererPlug() );
	}
}

std::shared_ptr<const RenderManifest> InteractiveRender::renderManifest() const
{
	if( m_controller )
	{
		return m_controller->renderManifest();
	}

	return m_lastRenderManifest;
}

void InteractiveRender::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == resolvedRendererPlug() )
	{
		const std::string renderer = rendererPlug()->getValue();
		if( renderer.empty() )
		{
			h.append( inPlug()->globalsHash() );
		}
		else
		{
			h.append( renderer );
		}
	}
}

void InteractiveRender::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == resolvedRendererPlug() )
	{
		std::string renderer = rendererPlug()->getValue();
		if( renderer.empty() )
		{
			ConstCompoundObjectPtr globals = inPlug()->globals();
			if( auto rendererData = globals->member<const StringData>( g_rendererOptionName ) )
			{
				renderer = rendererData->readable();
			}
		}
		static_cast<StringPlug *>( output )->setValue( renderer );
	}

	ComputeNode::compute( output, context );
}
