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

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneNode.h"
#include "GafferScene/SceneProcessor.h"

#include "Gaffer/Context.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "Gaffer/Private/IECorePreview/MessagesData.h"

#include "IECoreScene/Transform.h"
#include "IECoreScene/VisibleRenderable.h"

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"

#include "tbb/mutex.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;



namespace
{

typedef set<PlugPtr> PlugSet;
typedef std::unique_ptr<PlugSet> PlugSetPtr;

struct PendingUpdates
{
	tbb::spin_mutex mutex;
	PlugSetPtr plugs;
};

PendingUpdates &pendingUpdates()
{
	static PendingUpdates *p = new PendingUpdates;
	return *p;
}

} // anon namespace

// A thread-safe message handler for render messaging
class InteractiveRender::RenderMessageHandler : public MessageHandler
{
	public :

		RenderMessageHandler()
			:	m_messages( new MessagesData )
		{
		}

		void handle( MessageHandler::Level level, const std::string &context, const std::string &message  ) override
		{
			{
				tbb::mutex::scoped_lock lock( m_mutex );
				m_messages->writable().add( IECorePreview::Message( level, context, message ) );
			}

			messagesChangedSignal();
		}

		IECore::DataPtr messages()
		{
			tbb::mutex::scoped_lock lock( m_mutex );
			return m_messages->copy();
		}

		void messagesHash( IECore::MurmurHash &h )
		{
			tbb::mutex::scoped_lock lock( m_mutex );
			m_messages->hash( h );
		}

		void clear()
		{
			{
				tbb::mutex::scoped_lock lock( m_mutex );
				m_messages->writable().clear();
			}

			messagesChangedSignal();
		}

		boost::signal<void ()> messagesChangedSignal;

	private :

		tbb::mutex m_mutex;
		MessagesDataPtr m_messages;
};


static InternedString g_rendererContextName( "scene:renderer" );

size_t InteractiveRender::g_firstPlugIndex = 0;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( InteractiveRender );

InteractiveRender::InteractiveRender( const std::string &name )
	:	InteractiveRender( /* rendererType = */ InternedString(), name )
{
}

InteractiveRender::InteractiveRender( const IECore::InternedString &rendererType, const std::string &name )
	:	ComputeNode( name ),
		m_state( Stopped ),
		m_messageHandler( new RenderMessageHandler() )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
	addChild( new StringPlug( rendererType.string().empty() ? "renderer" : "__renderer", Plug::In, rendererType.string() ) );
	addChild( new IntPlug( "state", Plug::In, Stopped, Stopped, Paused, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ObjectPlug( "messages", Plug::Out, new MessagesData(), Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "__adaptedIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	// Incremented when new messages are received, triggering a dirty signal for the output plug.
	addChild( new IntPlug( "__messageUpdateCount", Plug::In, 0, 0, Imath::limits<int>::max(), Plug::Default & ~Plug::Serialisable ) );

	SceneProcessorPtr adaptors = RendererAlgo::createAdaptors();
	setChild( "__adaptors", adaptors );
	adaptors->inPlug()->setInput( inPlug() );
	adaptedInPlug()->setInput( adaptors->outPlug() );

	outPlug()->setInput( inPlug() );

	plugDirtiedSignal().connect( boost::bind( &InteractiveRender::plugDirtied, this, ::_1 ) );

	m_messageHandler->messagesChangedSignal.connect( boost::bind( &InteractiveRender::messagesChanged, this ) );
}

InteractiveRender::~InteractiveRender()
{
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

ScenePlug *InteractiveRender::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 3 );
}

const ScenePlug *InteractiveRender::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 3 );
}

ObjectPlug *InteractiveRender::messagesPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

const ObjectPlug *InteractiveRender::messagesPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

ScenePlug *InteractiveRender::adaptedInPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 5 );
}

const ScenePlug *InteractiveRender::adaptedInPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 5 );
}

Gaffer::IntPlug *InteractiveRender::messageUpdateCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::IntPlug *InteractiveRender::messageUpdateCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 6 );
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

void InteractiveRender::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == rendererPlug() || plug == statePlug() )
	{
		try
		{
			update();
		}
		catch( const std::exception &e )
		{
			errorSignal()( plug, plug, e.what() );
		}
	}
}

void InteractiveRender::update()
{
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

		m_renderer = IECoreScenePreview::Renderer::create(
			rendererPlug()->getValue(),
			IECoreScenePreview::Renderer::Interactive,
			"",
			m_messageHandler.get()
		);

		m_controller.reset(
			new RenderController( adaptedInPlug(), effectiveContext(), m_renderer )
		);
		m_controller->setMinimumExpansionDepth( limits<size_t>::max() );
		m_controller->updateRequiredSignal().connect(
			boost::bind( &InteractiveRender::update, this )
		);
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

	m_controller->update();

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

void InteractiveRender::stop()
{
	m_controller.reset();
	m_renderer.reset();
	m_state = Stopped;
}

// Called on a background thread when data is received on the driver.
// We need to update `messagesPlug()`, but all graph edits must
// be performed on the UI thread, so we can't do it directly.
void InteractiveRender::messagesChanged()
{
	bool scheduleUpdate = false;
	{
		// To minimise overhead we perform updates in batches by storing
		// a set of plugs which are pending update. If we're the creator
		// of a new batch then we are responsible for scheduling a call
		// to `messagesChangedUI()` to process the batch. Otherwise we just
		// add to the current batch.
		PendingUpdates &pending = pendingUpdates();
		tbb::spin_mutex::scoped_lock lock( pending.mutex );
		if( !pending.plugs.get() )
		{
			scheduleUpdate = true;
			pending.plugs.reset( new PlugSet );
		}
		pending.plugs->insert( messagesPlug() );
	}
	if( scheduleUpdate )
	{
		ParallelAlgo::callOnUIThread( &InteractiveRender::messagesChangedUI );
	}
}

// Called on the UI thread after being scheduled by `messagesChanged()`.
void InteractiveRender::messagesChangedUI()
{
	// Get the batch of plugs to trigger updates for. We want to hold the mutex
	// for the shortest duration possible, because it causes contention between
	// the background rendering thread and the UI thread, and can significantly
	// affect performance.  We do this by "stealing" the current batch, so the
	// background thread will create a new batch and we are safe to iterate our
	// batch without holding the lock.
	PlugSetPtr batch;
	{
		PendingUpdates &pending = pendingUpdates();
		tbb::spin_mutex::scoped_lock lock( pending.mutex );
		batch.reset( pending.plugs.release() );
	}

	// Now update the messages plugs for the render nodes that have received new messages.
	{
		DirtyPropagationScope dirtyPropagationScope;
		for( set<PlugPtr>::const_iterator it = batch->begin(), eIt = batch->end(); it != eIt; ++it )
		{
			PlugPtr plug = *it;
			// Because `messagesChangedUI()` is deferred to the UI thread,
			// it's possible that the node has actually been deleted by
			// the time we're called, so we must check.
			if( InteractiveRender *node = runTimeCast<InteractiveRender>( plug->node() ) )
			{
				node->messageUpdateCountPlug()->setValue( node->messageUpdateCountPlug()->getValue() + 1 );
			}
		}
	}
}

void InteractiveRender::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == messageUpdateCountPlug() )
	{
		outputs.push_back( messagesPlug() );
	}
}

void InteractiveRender::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output == messagesPlug() )
	{
		m_messageHandler->messagesHash( h );
	}
}

void InteractiveRender::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == messagesPlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue( m_messageHandler->messages() );
		return;
	}

	ComputeNode::compute( output, context );
}

Gaffer::ValuePlug::CachePolicy InteractiveRender::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == messagesPlug() )
	{
		// just copying data out of our intermediate is actually quicker than if we cache the result.
		return ValuePlug::CachePolicy::Uncached;
	}

	return ComputeNode::computeCachePolicy( output );
}
