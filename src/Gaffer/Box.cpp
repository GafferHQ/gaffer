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

#include "Gaffer/Box.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/PlugIterator.h"
#include "Gaffer/NumericPlug.h"

using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Box );

Box::Box( const std::string &name )
	:	Node( name )
{
}

Box::~Box()
{
}

BoxPtr Box::create( Node *parent, const Set *childNodes )
{
	BoxPtr result = new Box;
	parent->addChild( result );

	// it's pretty natural to call this function passing childNodes == ScriptNode::selection().
	// unfortunately nodes will be removed from the selection as we reparent
	// them, so we have to make a copy of childNodes so our iteration isn't befuddled by
	// the changing contents. we can use this opportunity to weed out anything in childNodes
	// which isn't a direct child of parent though.
	StandardSetPtr verifiedChildNodes = new StandardSet();
	for( NodeIterator nodeIt( parent ); nodeIt != nodeIt.end(); nodeIt++ )
	{
		if( childNodes->contains( nodeIt->get() ) )
		{
			verifiedChildNodes->add( *nodeIt );
		}
	}
	
	// when a node we're putting in the box has connections to
	// a node remaining outside, we need to reroute the connection
	// via an intermediate plug on the box. this mapping maps input
	// plugs (be they internal or external) to intermediate input plugs.
	typedef std::pair<const Plug *, Plug *> PlugPair;
	typedef std::map<const Plug *, Plug *> PlugMap;
	PlugMap plugMap;

	for( size_t i = 0, e = verifiedChildNodes->size(); i < e; i++ )
	{
		// reparent the child under the Box
		Node *childNode = static_cast<Node *>( verifiedChildNodes->member( i ) );
		result->addChild( childNode );
				
		// reroute any connections to external nodes
		for( PlugIterator plugIt( childNode ); plugIt != plugIt.end(); plugIt++ )
		{
			Plug *plug = plugIt->get();
			if( plug->direction() == Plug::In )
			{
				Plug *input = plug->getInput<Plug>();
				if( input && !verifiedChildNodes->contains( input->node() ) )
				{
					PlugMap::const_iterator mapIt = plugMap.find( input );
					if( mapIt == plugMap.end() )
					{
						PlugPtr intermediateInput = plug->createCounterpart( "in", Plug::In );
						result->addChild( intermediateInput );
						intermediateInput->setInput( input );
						mapIt = plugMap.insert( PlugPair( input, intermediateInput.get() ) ).first;
					}
					plug->setInput( mapIt->second );
				}
			}
			else
			{
				// take a copy of the outputs, because we might be modifying the
				// original as we iterate.
				Plug::OutputContainer outputs = plug->outputs();
				typedef Plug::OutputContainer::const_iterator OutputIterator;
				for( OutputIterator oIt = outputs.begin(), eIt = outputs.end(); oIt != eIt; oIt++ )
				{
					Plug *output = *oIt;
					if( !verifiedChildNodes->contains( output->node() ) )
					{
						PlugMap::const_iterator mapIt = plugMap.find( plug );
						if( mapIt == plugMap.end() )
						{
							PlugPtr intermediateOutput = plug->createCounterpart( "out", Plug::Out );
							result->addChild( intermediateOutput );
							intermediateOutput->setInput( plug );
							mapIt = plugMap.insert( PlugPair( plug, intermediateOutput.get() ) ).first;
						}
						output->setInput( mapIt->second );
					}
				}
			}
		}
	}

	return result;
}
