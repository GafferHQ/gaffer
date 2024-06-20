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

#include "Gaffer/Context.h"
#include "Gaffer/ContextVariables.h"
#include "Gaffer/Loop.h"
#include "Gaffer/NameSwitch.h"
#include "Gaffer/Switch.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include <unordered_set>

using namespace Gaffer;
using namespace GafferUI;
using namespace IECore;
using namespace boost::placeholders;
using namespace std;

ContextTracker::ContextTracker( const Gaffer::NodePtr &node, const Gaffer::ContextPtr &context )
	:	m_node( node ), m_context( context )
{
	node->plugDirtiedSignal().connect( boost::bind( &ContextTracker::plugDirtied, this, ::_1 ) );
	context->changedSignal().connect( boost::bind( &ContextTracker::contextChanged, this, ::_2 ) );
	update();
}

ContextTracker::~ContextTracker()
{
	disconnectTrackedConnections();
}

const Gaffer::Node *ContextTracker::targetNode() const
{
	return m_node.get();
}

const Gaffer::Context *ContextTracker::targetContext() const
{
	return m_context.get();
}

bool ContextTracker::isTracked( const Gaffer::Plug *plug ) const
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

bool ContextTracker::isTracked( const Gaffer::Node *node ) const
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
	update();
}

void ContextTracker::contextChanged( IECore::InternedString variable )
{
	update();
}

void ContextTracker::update()
{
	m_nodeContexts.clear();
	m_plugContexts.clear();

	std::deque<std::pair<const Plug *, ConstContextPtr>> toVisit;

	for( Plug::RecursiveOutputIterator it( m_node.get() ); !it.done(); ++it )
	{
		toVisit.push_back( { it->get(), m_context } );
		it.prune();
	}

	std::unordered_set<MurmurHash> visited;

	while( !toVisit.empty() )
	{
		// Get next plug to visit, and early out if we've already visited it in
		// this context.

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

		const Node *node = plug->node();
		NodeData &nodeData = m_nodeContexts[node];
		if( !nodeData.context )
		{
			nodeData.context = context;
		}

		if( !node || plug->direction() == Plug::Out || !nodeData.allInputsActive || *context != *nodeData.context  )
		{
			m_plugContexts.insert( { plug, context } );
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

		Context::Scope scopedContext( context.get() );

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
				toVisit.push_back( { contextProcessor->inPlug(), inContext } );
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
					toVisit.push_back( { previousPlug, previousContext } );
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
