//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Box.h"

#include "Gaffer/BoxOut.h"
#include "Gaffer/Context.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StandardSet.h"

#include "boost/regex.hpp"

#include <unordered_set>

using namespace std;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

std::unordered_set<const Node *> boxOutPassThroughSources( const Node *parent )
{
	std::unordered_set<const Node *> result;
	for( const auto &boxOut : BoxOut::Range( *parent ) )
	{
		Plug *plug = boxOut->passThroughPlug();
		while( plug )
		{
			if( const Node *node = plug->node() )
			{
				if( node->parent() != parent )
				{
					break;
				}
				else
				{
					result.insert( node );
				}
			}
			plug = plug->getInput();
		}
	}
	return result;
}


} // namespace

//////////////////////////////////////////////////////////////////////////
// Box
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Box );

Box::Box( const std::string &name )
	:	SubGraph( name )
{
}

Box::~Box()
{
}

bool Box::canPromotePlug( const Plug *descendantPlug ) const
{
	const Node *descendantNode = descendantPlug->node();
	if( !descendantNode || descendantNode->parent<Node>() != this )
	{
		return false;
	}

	return PlugAlgo::canPromote( descendantPlug );
}

Plug *Box::promotePlug( Plug *descendantPlug )
{
	const Node *descendantNode = descendantPlug->node();
	if( !descendantNode || descendantNode->parent<Node>() != this )
	{
		throw IECore::Exception(
			boost::str(
				boost::format( "Cannot promote plug \"%s\" as its node is not a child of \"%s\"." ) % descendantPlug->fullName() % fullName()
			)
		);
	}

	return PlugAlgo::promote( descendantPlug );
}

bool Box::plugIsPromoted( const Plug *descendantPlug ) const
{
	return PlugAlgo::isPromoted( descendantPlug );
}

void Box::unpromotePlug( Plug *promotedDescendantPlug )
{
	return PlugAlgo::unpromote( promotedDescendantPlug );
}

void Box::exportForReference( const std::filesystem::path &fileName ) const
{
	const ScriptNode *script = scriptNode();
	if( !script )
	{
		throw IECore::Exception( "Box::exportForReference called without ScriptNode" );
	}

	// we only want to save out our child nodes and plugs that are visible in the UI, so we build a filter
	// to specify just the things to export.

	boost::regex invisiblePlug( "^__.*$" );
	StandardSetPtr toExport = new StandardSet;
	for( ChildIterator it = children().begin(), eIt = children().end(); it != eIt; ++it )
	{
		if( (*it)->isInstanceOf( Node::staticTypeId() ) )
		{
			toExport->add( *it );
		}
		else if( const Plug *plug = IECore::runTimeCast<Plug>( it->get() ) )
		{
			if(
				!boost::regex_match( plug->getName().c_str(), invisiblePlug )
				&& plug != userPlug()
			)
			{
				toExport->add( *it );
			}
		}
	}

	ContextPtr context = new Context;
	context->set( "valuePlugSerialiser:omitParentNodePlugValues", true );
	context->set( "serialiser:includeParentMetadata", true );
	Context::Scope scopedContext( context.get() );

	script->serialiseToFile( fileName, this, toExport.get() );
}

BoxPtr Box::create( Node *parent, const Set *childNodes )
{
	BoxPtr result = new Box;
	parent->addChild( result );

	// It's pretty natural to call this function passing childNodes == ScriptNode::selection().
	// unfortunately nodes will be removed from the selection as we reparent
	// them, so we have to make a copy of childNodes so our iteration isn't befuddled by
	// the changing contents. We can use this opportunity to weed out anything in childNodes
	// which isn't a direct child of parent though, and also to skip over BoxIO nodes and pass-throughs
	// which should remain where they are.
	std::unordered_set<const Node *> boxOutPassThroughSources = ::boxOutPassThroughSources( parent );
	StandardSetPtr verifiedChildNodes = new StandardSet();
	for( const auto &node : Node::Range( *parent ) )
	{
		if( !childNodes->contains( node.get() ) )
		{
			continue;
		}
		if( IECore::runTimeCast<BoxIO>( node.get() ) )
		{
			continue;
		}
		if( boxOutPassThroughSources.find( node.get() ) != boxOutPassThroughSources.end() )
		{
			continue;
		}
		verifiedChildNodes->add( node );
	}

	// When a node we're putting in the box has connections to
	// a node remaining outside, we need to reroute the connection
	// via a promoted plug. This mapping maps source plugs (be they
	// internal or external) to promoted plugs.
	using PlugPair = std::pair<const Plug *, Plug *>;
	using PlugMap = std::map<const Plug *, Plug *>;
	PlugMap plugMap;

	for( size_t i = 0, e = verifiedChildNodes->size(); i < e; i++ )
	{
		// Reparent the node inside the box
		Node *childNode = static_cast<Node *>( verifiedChildNodes->member( i ) );
		result->addChild( childNode );
		// Reroute any connections to external nodes
		for( Plug::RecursiveIterator plugIt( childNode ); !plugIt.done(); ++plugIt )
		{
			Plug *plug = plugIt->get();
			if( plug->direction() == Plug::In )
			{
				Plug *input = plug->getInput();
				if( input && input->node()->parent<Node>() == parent && !verifiedChildNodes->contains( input->node() ) )
				{
					PlugMap::const_iterator mapIt = plugMap.find( input );
					if( mapIt == plugMap.end() )
					{
						plug->setInput( nullptr ); // To allow promotion
						PlugPtr promoted = PlugAlgo::promote( plug );
						promoted->setInput( input );
						plugMap.insert( PlugPair( input, promoted.get() ) );
					}
					else
					{
						plug->setInput( mapIt->second );
					}
					plugIt.prune();
				}
			}
			else
			{
				// Take a copy of the outputs, because we might be modifying the
				// original as we iterate.
				Plug::OutputContainer outputs = plug->outputs();
				if( !outputs.empty() )
				{
					using OutputIterator = Plug::OutputContainer::const_iterator;
					for( OutputIterator oIt = outputs.begin(), eIt = outputs.end(); oIt != eIt; oIt++ )
					{
						Plug *output = *oIt;
						const Node *outputNode = output->node();
						if( outputNode->parent<Node>() == parent && !verifiedChildNodes->contains( outputNode ) )
						{
							PlugMap::const_iterator mapIt = plugMap.find( plug );
							if( mapIt == plugMap.end() )
							{
								PlugPtr promoted = PlugAlgo::promote( plug );
								mapIt = plugMap.insert( PlugPair( plug, promoted.get() ) ).first;
							}
							output->setInput( mapIt->second );
						}
					}
					plugIt.prune();
				}
			}
		}
	}

	return result;
}
