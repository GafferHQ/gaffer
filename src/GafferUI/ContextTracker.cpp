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

#include "GafferUI/ContextTracker.h"

#include "GafferUI/Gadget.h"

#include "Gaffer/BackgroundTask.h"
#include "Gaffer/Context.h"
#include "Gaffer/ContextVariables.h"
#include "Gaffer/Loop.h"
#include "Gaffer/NameSwitch.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Switch.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index/hashed_index.hpp"
#include "boost/multi_index_container.hpp"

#include <unordered_set>

using namespace Gaffer;
using namespace GafferUI;
using namespace IECore;
using namespace boost::placeholders;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

using SharedInstance = std::pair<const Node *, ContextTracker *>;
using SharedInstances = boost::multi_index::multi_index_container<
	SharedInstance,
	boost::multi_index::indexed_by<
		boost::multi_index::hashed_unique<
			boost::multi_index::member<SharedInstance, const Node *, &SharedInstance::first>
		>,
		boost::multi_index::hashed_non_unique<
			boost::multi_index::member<SharedInstance, ContextTracker *, &SharedInstance::second>
		>
	>
>;

SharedInstances &sharedInstances()
{
	static SharedInstances g_sharedInstances;
	return g_sharedInstances;
}

using SharedFocusInstance = std::pair<const ScriptNode *, ContextTracker *>;
using SharedFocusInstances = boost::multi_index::multi_index_container<
	SharedFocusInstance,
	boost::multi_index::indexed_by<
		boost::multi_index::hashed_unique<
			boost::multi_index::member<SharedFocusInstance, const ScriptNode *, &SharedFocusInstance::first>
		>,
		boost::multi_index::hashed_non_unique<
			boost::multi_index::member<SharedFocusInstance, ContextTracker *, &SharedFocusInstance::second>
		>
	>
>;

SharedFocusInstances &sharedFocusInstances()
{
	static SharedFocusInstances g_sharedInstances;
	return g_sharedInstances;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ContextTracker
//////////////////////////////////////////////////////////////////////////

ContextTracker::ContextTracker( const Gaffer::NodePtr &node, const Gaffer::ContextPtr &context )
	:	m_context( context )
{
	context->changedSignal().connect( boost::bind( &ContextTracker::contextChanged, this, ::_2 ) );
	updateNode( node );
}

ContextTracker::~ContextTracker()
{
	sharedInstances().get<1>().erase( this );
	sharedFocusInstances().get<1>().erase( this );
	disconnectTrackedConnections();
	m_updateTask.reset();
}

ContextTrackerPtr ContextTracker::acquire( const Gaffer::NodePtr &node )
{
	auto &instances = sharedInstances();
	auto it = instances.find( node.get() );
	if( it != instances.end() )
	{
		return it->second;
	}

	auto scriptNode = node ? node->scriptNode() : nullptr;
	Ptr instance = new ContextTracker( node, scriptNode ? scriptNode->context() : new Context() );
	instances.insert( { node.get(), instance.get() } );
	return instance;
}

ContextTrackerPtr ContextTracker::acquireForFocus( Gaffer::ScriptNode *script )
{
	if( !script )
	{
		return acquire( script );
	}

	auto &instances = sharedFocusInstances();
	auto it = instances.find( script );
	if( it != instances.end() )
	{
		if( it->second->m_context == script->context() )
		{
			return it->second;
		}
		else
		{
			// Contexts don't match. Only explanation is that the original
			// ScriptNode has been destroyed and a new one created with the same
			// address. Ditch the old instance and fall through to create a new
			// one.
			instances.erase( it );
		}
	}

	Ptr instance = new ContextTracker( script->getFocus(), script->context() );
	script->focusChangedSignal().connect( boost::bind( &ContextTracker::updateNode, instance.get(), ::_2 ) );
	instances.insert( { script, instance.get() } );
	return instance;
}

void ContextTracker::updateNode( const Gaffer::NodePtr &node )
{
	if( node == m_node )
	{
		return;
	}

	m_plugDirtiedConnection.disconnect();
	m_node = node;
	if( m_node )
	{
		m_plugDirtiedConnection = node->plugDirtiedSignal().connect( boost::bind( &ContextTracker::plugDirtied, this, ::_1 ) );
	}

	scheduleUpdate();
}

const Gaffer::Node *ContextTracker::targetNode() const
{
	return m_node.get();
}

const Gaffer::Context *ContextTracker::targetContext() const
{
	return m_context.get();
}

void ContextTracker::scheduleUpdate()
{
	// Cancel old update.
	m_updateTask.reset();

	if( !m_node )
	{
		// Don't need a BackgroundTask, so just do the update directly on the UI
		// thread.
		m_nodeContexts.clear();
		m_plugContexts.clear();
		m_idleConnection.disconnect();
		changedSignal()( *this );
		return;
	}

	if( !m_node->scriptNode() )
	{
		// ScriptNode is dying. Can't use a BackgroundTask and no need for
		// update anyway.
		m_idleConnection.disconnect();
		return;
	}

	if( m_idleConnection.connected() )
	{
		// Update already scheduled.
		return;
	}

	// Arrange to do the update on the next idle event. This allows us to avoid
	// redundant restarts when `plugDirtied()` or `contextChanged()` is called
	// multiple times in quick succession.

	m_idleConnection = Gadget::idleSignal().connect(
		[thisRef = Ptr( this )] () {
			thisRef->updateInBackground();
		}
	);
}

void ContextTracker::updateInBackground()
{
	m_idleConnection.disconnect();

	// Seed the list of plugs to visit with all the outputs of our node.
	// We must take a copy of the context for this, because it will be used
	// on the background thread and the original context may be modified on
	// the main thread.
	ConstContextPtr contextCopy = new Context( *m_context );
	std::deque<std::pair<const Plug *, ConstContextPtr>> toVisit;
	if( m_node )
	{
		for( Plug::RecursiveOutputIterator it( m_node.get() ); !it.done(); ++it )
		{
			toVisit.push_back( { it->get(), contextCopy } );
			it.prune();
		}
	}

	Context::Scope scopedContext( contextCopy.get() );
	m_updateTask = ParallelAlgo::callOnBackgroundThread(

		/* subject = */ toVisit.empty() ? nullptr : toVisit.back().first,

		// OK to capture `this` without incrementing reference count, because
		// ~UpstreamContext cancels background task and waits for it to
		// complete. Therefore `this` will always outlive the task.
		[toVisit, this] () mutable {

			PlugContexts plugContexts;
			NodeContexts nodeContexts;

			// Alias for `this` to work around MSVC bug that prevents capturing
			// `this` again in a nested lambda.
			ContextTracker *that = this;

			try
			{
				ContextTracker::visit( toVisit, nodeContexts, plugContexts, Context::current()->canceller() );
			}
			catch( const IECore::Cancelled & )
			{
				// Cancellation could be for several reasons :
				//
				// 1. A graph edit is being made.
				// 2. The context has changed or `updateNode()` has been called
				//    and we're scheduling a new update.
				// 3. Our reference count has dropped to 0 and we're being
				//    deleted, and are cancelling the task from our destructor.
				//
				// In the first two cases we need to schedule a new update, but
				// in the last case we mustn't do anything.
				if( refCount() )
				{
					ParallelAlgo::callOnUIThread(
						// Need to own a reference via `thisRef`, because otherwise we could be deleted
						// before `callOnUIThread()` gets to us.
						[thisRef = Ptr( that )] () {
							thisRef->m_updateTask.reset();
							thisRef->scheduleUpdate();
						}
					);
				}
				throw;
			}
			catch( const Gaffer::ProcessException &e )
			{
				IECore::msg( IECore::Msg::Error, "ContextTracker::updateInBackground", e.what() );
			}

			if( refCount() )
			{
				ParallelAlgo::callOnUIThread(
					// Need to own a reference via `thisRef`, because otherwise we could be deleted
					// before `callOnUIThread()` gets to us.
					[thisRef = Ptr( that ), plugContexts = std::move( plugContexts ), nodeContexts = std::move( nodeContexts )] () mutable {
						thisRef->m_nodeContexts.swap( nodeContexts );
						thisRef->m_plugContexts.swap( plugContexts );
						thisRef->m_updateTask.reset();
						thisRef->changedSignal()( *thisRef );
					}
				);
			}
		}

	);
}

bool ContextTracker::updatePending() const
{
	return m_idleConnection.connected() || m_updateTask;
}

ContextTracker::Signal &ContextTracker::changedSignal()
{
	return m_changedSignal;
}

bool ContextTracker::isActive( const Gaffer::Plug *plug ) const
{
	if( findPlugContext( plug ) )
	{
		return true;
	}

	if( plug->direction() != Plug::In )
	{
		return false;
	}

	auto it = m_nodeContexts.find( plug->node() );
	return it != m_nodeContexts.end() && it->second.allInputsActive;
}

bool ContextTracker::isActive( const Gaffer::Node *node ) const
{
	return m_nodeContexts.find( node ) != m_nodeContexts.end();
}

Gaffer::ConstContextPtr ContextTracker::context( const Gaffer::Plug *plug ) const
{
	if( const Context *c = findPlugContext( plug ) )
	{
		return c;
	}

	return context( plug->node() );
}

Gaffer::ConstContextPtr ContextTracker::context( const Gaffer::Node *node ) const
{
	auto it = m_nodeContexts.find( node );
	return it != m_nodeContexts.end() ? it->second.context : m_context;
}

void ContextTracker::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug->direction() == Plug::Out )
	{
		scheduleUpdate();
	}
}

void ContextTracker::contextChanged( IECore::InternedString variable )
{
	if( !boost::starts_with( variable.string(), "ui:" ) )
	{
		scheduleUpdate();
	}
}

void ContextTracker::visit( std::deque<std::pair<const Plug *, ConstContextPtr>> &toVisit, NodeContexts &nodeContexts, PlugContexts &plugContexts, const IECore::Canceller *canceller )
{
	std::unordered_set<MurmurHash> visited;

	while( !toVisit.empty() )
	{
		// Get next plug to visit, and early out if we've already visited it in
		// this context or if we have been cancelled.

		IECore::Canceller::check( canceller );

		auto [plug, context] = toVisit.front();
		toVisit.pop_front();

		MurmurHash visitHash = context->hash();
		visitHash.append( (uintptr_t)plug );
		if( !visited.insert( visitHash ).second )
		{
			continue;
		}

		// If this is the first time we have visited the node and/or plug, then
		// record the context.

		assert( !context->canceller() );

		const Node *node = plug->node();
		NodeData &nodeData = nodeContexts[node];
		if( !nodeData.context )
		{
			nodeData.context = context;
		}

		if( !node || plug->direction() == Plug::Out || !nodeData.allInputsActive || *context != *nodeData.context  )
		{
			plugContexts.insert( { plug, context } );
		}

		// Arrange to visit any inputs to this plug, including
		// inputs to its descendants.

		if( auto input = plug->getInput() )
		{
			toVisit.push_back( { input, context } );
		}
		else
		{
			for( Plug::RecursiveInputIterator it( plug ); !it.done(); ++it )
			{
				if( auto input = (*it)->getInput() )
				{
					toVisit.push_back( { input, context } );
					it.prune();
				}
			}
		}

		// If the plug isn't an output plug on a node, or it has an input
		// connection, then we're done here and can continue to the next one.

		if( plug->direction() != Plug::Out || !plug->node() )
		{
			continue;
		}

		// Scope the context we're visiting before evaluating any plug
		// values. We store contexts without a canceller (ready to return
		// from `ContextTracker::context()`), so must also scope the canceller
		// to allow any computes we trigger to be cancelled.
		Context::EditableScope scopedContext( context.get() );
		scopedContext.setCanceller( canceller );

		if( plug->getInput() )
		{
			// The plug value isn't computed, so we _should_ be done. But
			// there's a wrinkle : switches have an optimisation where they make
			// a pass-through connection to avoid the compute when the index is
			// constant. We still consider the `index` plug to be active in this
			// case, so need to manually add it to the traversal.
			if( auto switchNode = runTimeCast<const Switch>( node ) )
			{
				if( plug == switchNode->outPlug() || switchNode->outPlug()->isAncestorOf( plug ) )
				{
					toVisit.push_back( { switchNode->enabledPlug(), context } );
					if( switchNode->enabledPlug()->getValue() )
					{
						toVisit.push_back( { switchNode->indexPlug(), context } );
					}
				}
			}
			continue;
		}

		// Plug is an output whose value may be computed. We want to visit only
		// the input plugs that will be used by the compute, accounting for any
		// changes in context the compute will make. A few special cases for the
		// most common nodes are sufficient to provide the user with good
		// feedback about what parts of the graph are active.

		if( auto dependencyNode = runTimeCast<const DependencyNode>( node ) )
		{
			if( auto enabledPlug = dependencyNode->enabledPlug() )
			{
				if( !enabledPlug->getValue() )
				{
					// Node is disabled, so we only need to visit the
					// pass-through input, if any.
					if( auto inPlug = dependencyNode->correspondingInput( plug ) )
					{
						toVisit.push_back( { inPlug, context } );
						toVisit.push_back( { enabledPlug, context } );
					}
					continue;
				}
			}
		}

		if( auto nameSwitch = runTimeCast<const NameSwitch>( node ) )
		{
			if( plug == nameSwitch->getChild<Plug>( "__outIndex" ) )
			{
				toVisit.push_back( { nameSwitch->selectorPlug(), context } );
				const string selector = nameSwitch->selectorPlug()->getValue();
				if( const ArrayPlug *in = nameSwitch->inPlugs() )
				{
					for( int i = 1, e = in->children().size(); i < e; ++i )
					{
						auto p = in->getChild<NameValuePlug>( i );
						toVisit.push_back( { p->enabledPlug(), context } );
						if( !p->enabledPlug()->getValue() )
						{
							continue;
						}
						const string name = p->namePlug()->getValue();
						toVisit.push_back( { p->namePlug(), context } );
						if( !name.empty() && StringAlgo::matchMultiple( selector, name ) )
						{
							break;
						}
					}
				}
				continue;
			}
			// Fall through so other outputs are covered by the Switch
			// base class handling below.
		}

		if( auto switchNode = runTimeCast<const Switch>( node ) )
		{
			if( const Plug *activeIn = switchNode->activeInPlug( plug ) )
			{
				toVisit.push_back( { switchNode->enabledPlug(), context } );
				toVisit.push_back( { switchNode->indexPlug(), context } );
				toVisit.push_back( { activeIn, context } );
			}
			continue;
		}

		if( auto contextProcessor = runTimeCast<const ContextProcessor>( node ) )
		{
			if( plug == contextProcessor->outPlug() )
			{
				// Assume all input plugs are used to generate the context.
				nodeData.allInputsActive = true;
				// Visit main input in processed context.
				ConstContextPtr inContext = contextProcessor->inPlugContext();
				toVisit.push_back( { contextProcessor->inPlug(), new Context( *inContext, /* omitCanceller = */ true ) } );
			}
			continue;
		}

		if( auto loop = runTimeCast<const Loop>( node ) )
		{
			if( auto valuePlug = runTimeCast<const ValuePlug>( plug ) )
			{
				auto [previousPlug, previousContext] = loop->previousIteration( valuePlug );
				if( previousPlug )
				{
					toVisit.push_back( { loop->indexVariablePlug(), context } );
					if( plug == loop->outPlug() || loop->outPlug()->isAncestorOf( plug ) )
					{
						toVisit.push_back( { loop->iterationsPlug(), context } );
					}
					toVisit.push_back( { previousPlug, new Context( *previousContext, /* omitCanceller = */ true ) } );
				}
			}
			continue;
		}

		// Generic behaviour for all other nodes : assume the compute depends on
		// every input plug.

		for( const auto &inputPlug : Plug::InputRange( *node ) )
		{
			nodeData.allInputsActive = true;
			toVisit.push_back( { inputPlug.get(), context } );
		}
	}
}

const Gaffer::Context *ContextTracker::findPlugContext( const Gaffer::Plug *plug ) const
{
	while( plug )
	{
		auto it = m_plugContexts.find( plug );
		if( it != m_plugContexts.end() )
		{
			return it->second.get();
		}

		plug = plug->parent<Plug>();
	}

	return nullptr;
}
