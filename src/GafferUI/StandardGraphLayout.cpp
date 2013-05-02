//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "OpenEXR/ImathVec.h"

#include "Gaffer/Plug.h"
#include "Gaffer/PlugIterator.h"
#include "Gaffer/Node.h"

#include "GafferUI/StandardGraphLayout.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/NodeGadget.h"

using namespace std;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( StandardGraphLayout )

StandardGraphLayout::~StandardGraphLayout()
{
}

StandardGraphLayout::StandardGraphLayout()
{
}

bool StandardGraphLayout::connectNode( GraphGadget *graph, Node *node, Gaffer::Set *potentialInputs ) const
{
	// we only want to connect plugs which are visible in the ui - otherwise
	// things will get very confusing for the user.
	
	// get all visible output plugs we could potentially connect in to our node
	vector<Plug *> outputPlugs;
	for( size_t i = 0; i < potentialInputs->size(); i++ )
	{
		const Node *node = IECore::runTimeCast<Node>( potentialInputs->member( i ) );
		if( node )
		{
			NodeGadget *nodeGadget = graph->nodeGadget( node );
			if( nodeGadget )
			{
				for( OutputPlugIterator it( node ); it != it.end(); it++ )
				{
					if( nodeGadget->nodule( *it ) )
					{
						outputPlugs.push_back( it->get() );
					}
				}
			}
		}
	}
		
	if( !outputPlugs.size() )
	{
		return false;
	}
	
	// get the gadget for the target node
	NodeGadget *nodeGadget = graph->nodeGadget( node );
	if( !nodeGadget )
	{
		return false;
	}

	// iterate over the output plugs, connecting them in to the node if we can
	
	bool result = false;
	vector<Plug *> inputPlugs;
	unconnectedInputPlugs( nodeGadget, inputPlugs );
	for( vector<Plug *>::const_iterator oIt = outputPlugs.begin(), oEIt = outputPlugs.end(); oIt != oEIt; oIt++ )
	{
		for( vector<Plug *>::const_iterator iIt = inputPlugs.begin(), iEIt = inputPlugs.end(); iIt != iEIt; iIt++ )
		{
			if( (*iIt)->acceptsInput( *oIt ) )
			{
				(*iIt)->setInput( *oIt );
				result = true;
				// some nodes dynamically add new inputs when we connect
				// existing inputs, so we recalculate the input plugs
				// to take account
				unconnectedInputPlugs( nodeGadget, inputPlugs );
				break;
			}
		}
	}
	
	return result;

}

void StandardGraphLayout::positionNode( GraphGadget *graph, Gaffer::Node *node, const Imath::V2f &fallbackPosition ) const
{
	// try to figure out the node position based on its input connections
	std::vector<const ConnectionGadget *> connections;
	for( InputPlugIterator it( node ); it != it.end(); it++ )
	{
		const ConnectionGadget *connection = graph->connectionGadget( *it );
		if( connection )
		{
			connections.push_back( connection );
		}
	}
	
	if( !connections.size() )
	{
		graph->setNodePosition( node, fallbackPosition );
		return;
	}
	
	V3f	srcNoduleCentroid( 0 );
	V2f floorPos( V2f::baseTypeMin(), V2f::baseTypeMax() );
		
	for( std::vector<const ConnectionGadget *>::const_iterator it = connections.begin(), eIt = connections.end(); it != eIt; it++ )
	{
		const Nodule *srcNodule = (*it)->srcNodule();
		V3f	srcNodulePos = srcNodule->transformedBound( 0 ).center();
		srcNoduleCentroid += srcNodulePos;
		
		const NodeGadget *srcNodeGadget = srcNodule->ancestor<NodeGadget>();
		V3f srcTangent = srcNodeGadget->noduleTangent( srcNodule );
		
		if( srcTangent.dot( V3f( 0, -1, 0 ) ) > 0.5f )
		{
			floorPos.y = std::min( floorPos.y, srcNodulePos.y - 10.0f );
		}
		if( srcTangent.dot( V3f( 1, 0, 0 ) ) > 0.5f )
		{
			floorPos.x = std::max( floorPos.x, srcNodulePos.x + 10.0f );
		}
	}

	srcNoduleCentroid /= connections.size();
	V2f nodePosition(
		std::max( srcNoduleCentroid.x, floorPos.x ),
		std::min( srcNoduleCentroid.y, floorPos.y )
	);
			
	// apply the position
	
	graph->setNodePosition( node, V2f( nodePosition.x, nodePosition.y ) );	
}

void StandardGraphLayout::unconnectedInputPlugs( NodeGadget *nodeGadget, std::vector<Plug *> &plugs ) const
{
	plugs.clear();
	for( InputPlugIterator it( nodeGadget->node() ); it != it.end(); it++ )
	{
		if( (*it)->getInput<Plug>() == 0 and nodeGadget->nodule( *it ) )
		{
			plugs.push_back( it->get() );
		}
	}
}
