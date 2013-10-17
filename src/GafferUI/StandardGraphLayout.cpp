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
#include "Gaffer/DependencyNode.h"

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
	return connectNodeInternal( graph, node, potentialInputs, true /* insert if possible */ );
}

bool StandardGraphLayout::connectNodes( GraphGadget *graph, Gaffer::Set *nodes, Gaffer::Set *potentialInputs ) const
{
	// find the nodes without existing inputs, and when one of them
	// accepts connections from potentialInputs call it good.
	
	for( size_t i = 0, s = nodes->size(); i < s; ++i )
	{
		Node *node = IECore::runTimeCast<Node>( nodes->member( i ) );
		if( !node )
		{
			continue;
		}
		NodeGadget *nodeGadget = graph->nodeGadget( node );
		if( !nodeGadget )
		{
			continue;
		}
		
		bool hasInputs = false;
		for( RecursiveInputPlugIterator it( node ); it != it.end(); ++it )
		{
			if( (*it)->getInput<Plug>() && nodeGadget->nodule( it->get() ) )
			{
				hasInputs = true;
				break;
			}
		}
		if( hasInputs )
		{
			continue;
		}
		
		if( connectNodeInternal( graph, node, potentialInputs, nodes->size() == 1 /* only insert if there's only one node */ ) )
		{
			return true;
		}
	}
	
	return false;
}

void StandardGraphLayout::positionNode( GraphGadget *graph, Gaffer::Node *node, const Imath::V2f &fallbackPosition ) const
{
	Box2f hardConstraint;
	V2f softConstraint, position;
	if( nodeConstraints( graph, node, 0, hardConstraint, softConstraint ) )
	{
		if( hardConstraint.min.x < hardConstraint.max.x ) // hard constraint is achievable
		{
			position.x = clamp( softConstraint.x, hardConstraint.min.x, hardConstraint.max.x );
		}
		else
		{
			position.x = hardConstraint.center().x;
		}
		
		if( hardConstraint.min.y < hardConstraint.max.y ) // hard constraint is achievable
		{
			position.y = clamp( softConstraint.y, hardConstraint.min.y, hardConstraint.max.y );
		}
		else
		{
			position.y = hardConstraint.center().y;
		}
	}
	else
	{
		position = fallbackPosition;
	}
	
	graph->setNodePosition( node, position );
}

void StandardGraphLayout::positionNodes( GraphGadget *graph, Gaffer::Set *nodes, const Imath::V2f &fallbackPosition ) const
{
	// get the centre of the bunch of nodes we're positioning
	
	V2f centroid( 0 );
	size_t numNodes = 0;
	for( size_t i=0, s=nodes->size(); i<s; ++i )
	{
		Node *node = IECore::runTimeCast<Node>( nodes->member( i ) );
		if( !node )
		{
			continue;
		}
		centroid += graph->getNodePosition( node );
		numNodes++;
	}
	
	centroid /= numNodes;
	
	// figure out the hard and soft constraints per node, combining them
	// to produce constraints for the centroid.
	
	size_t numConstraints = 0;
	V2f softConstraint( 0 );
	Box2f hardConstraint = Box2f( V2f( V2f::baseTypeMin() ), V2f( V2f::baseTypeMax() ) );

	for( size_t i=0, s=nodes->size(); i<s; ++i )
	{
		Node *node = IECore::runTimeCast<Node>( nodes->member( i ) );
		if( !node )
		{
			continue;
		}
	
		V2f nodeSoftConstraint;
		Box2f nodeHardConstraint;
		if( nodeConstraints( graph, node, nodes, nodeHardConstraint, nodeSoftConstraint ) )
		{
			const V2f nodeOffset = graph->getNodePosition( node ) - centroid;
			
			nodeHardConstraint.min -= nodeOffset;
			nodeHardConstraint.max -= nodeOffset;
						
			hardConstraint.min.x = std::max( hardConstraint.min.x, nodeHardConstraint.min.x );
			hardConstraint.min.y = std::max( hardConstraint.min.y, nodeHardConstraint.min.y );
			hardConstraint.max.x = std::min( hardConstraint.max.x, nodeHardConstraint.max.x );
			hardConstraint.max.y = std::min( hardConstraint.max.y, nodeHardConstraint.max.y );
		
			softConstraint += nodeSoftConstraint - nodeOffset;
		
			numConstraints += 1;
		}
	
	}
		
	V2f newCentroid;
	if( numConstraints )
	{
		softConstraint /= numConstraints;
		
		if( hardConstraint.min.x < hardConstraint.max.x ) // hard constraint is achievable
		{
			newCentroid.x = clamp( softConstraint.x, hardConstraint.min.x, hardConstraint.max.x );
		}
		else
		{
			newCentroid.x = hardConstraint.center().x;
		}
		
		if( hardConstraint.min.y < hardConstraint.max.y ) // hard constraint is achievable
		{
			newCentroid.y = clamp( softConstraint.y, hardConstraint.min.y, hardConstraint.max.y );
		}
		else
		{
			newCentroid.y = hardConstraint.center().y;
		}
	}
	else
	{
		newCentroid = fallbackPosition;
	}
	
	// apply the offset between the old and new centroid to the nodes
	
	for( size_t i=0, s=nodes->size(); i<s; ++i )
	{
		Node *node = IECore::runTimeCast<Node>( nodes->member( i ) );
		if( !node )
		{
			continue;
		}
	
		const V2f nodeOffset = graph->getNodePosition( node ) - centroid;
		graph->setNodePosition( node, newCentroid + nodeOffset );
	}
	
}

bool StandardGraphLayout::connectNodeInternal( GraphGadget *graph, Gaffer::Node *node, Gaffer::Set *potentialInputs, bool insertIfPossible ) const
{
	// we only want to connect plugs which are visible in the ui - otherwise
	// things will get very confusing for the user.
	
	// get the gadget for the target node
	NodeGadget *nodeGadget = graph->nodeGadget( node );
	if( !nodeGadget )
	{
		return false;
	}
	
	// get all visible output plugs we could potentially connect in to our node
	vector<Plug *> outputPlugs;
	if( !this->outputPlugs( graph, potentialInputs, outputPlugs ) )
	{
		return false;
	}
	
	// iterate over the output plugs, connecting them in to the node if we can
	
	size_t numConnectionsMade = 0;
	Plug *firstConnectionSrc = 0, *firstConnectionDst = 0;
	vector<Plug *> inputPlugs;
	unconnectedInputPlugs( nodeGadget, inputPlugs );
	for( vector<Plug *>::const_iterator oIt = outputPlugs.begin(), oEIt = outputPlugs.end(); oIt != oEIt; oIt++ )
	{
		for( vector<Plug *>::const_iterator iIt = inputPlugs.begin(), iEIt = inputPlugs.end(); iIt != iEIt; iIt++ )
		{
			if( (*iIt)->acceptsInput( *oIt ) )
			{
				(*iIt)->setInput( *oIt );
				if( numConnectionsMade == 0 )
				{
					firstConnectionSrc = *oIt;
					firstConnectionDst = *iIt;
				}
				numConnectionsMade += 1;
				// some nodes dynamically add new inputs when we connect
				// existing inputs, so we recalculate the input plugs
				// to take account
				unconnectedInputPlugs( nodeGadget, inputPlugs );
				break;
			}
		}
	}

	// if only one connection was made, then try to insert the node into
	// the existing connections from the source.
			
	if( numConnectionsMade == 1 && insertIfPossible )
	{
		Plug *correspondingOutput = this->correspondingOutput( firstConnectionDst );
		if( correspondingOutput )
		{
			bool allCompatible = true;
			
			// This is a copy of (*it)->outputs() rather than a reference, as reconnection can modify (*it)->outputs()...
			Plug::OutputContainer outputs = firstConnectionSrc->outputs();
			for( Plug::OutputContainer::const_iterator it = outputs.begin(); it != outputs.end(); ++it )
			{
				// ignore outputs that aren't visible:
				NodeGadget *nodeGadget = graph->nodeGadget( (*it)->node() );
				if( !nodeGadget )
				{
					continue;
				}
				if( !nodeGadget->nodule( *it ) )
				{
					continue;
				}
				
				if( !(*it)->acceptsInput( correspondingOutput ) )
				{
					allCompatible = false;
					break;
				}
			}
			
			if( allCompatible )
			{
				for( Plug::OutputContainer::const_iterator it = outputs.begin(); it != outputs.end(); ++it )
				{
					// ignore outputs that aren't visible:
					NodeGadget *nodeGadget = graph->nodeGadget( (*it)->node() );
					if( !nodeGadget )
					{
						continue;
					}
					if( !nodeGadget->nodule( *it ) )
					{
						continue;
					}
					
					Plug *p = *it;
					if( p != firstConnectionDst )
					{
						p->setInput( correspondingOutput );
					}
				}
			}
		}
	}

	return numConnectionsMade;
}

size_t StandardGraphLayout::outputPlugs( NodeGadget *nodeGadget, std::vector<Gaffer::Plug *> &plugs ) const
{
	for( RecursiveOutputPlugIterator it( nodeGadget->node() ); it != it.end(); it++ )
	{
		if( nodeGadget->nodule( *it ) )
		{
			plugs.push_back( it->get() );
		}
	}
	
	return plugs.size();
}

size_t StandardGraphLayout::outputPlugs( GraphGadget *graph, Gaffer::Set *nodes, std::vector<Gaffer::Plug *> &plugs ) const
{
	for( size_t i = 0; i < nodes->size(); i++ )
	{
		const Node *node = IECore::runTimeCast<Node>( nodes->member( i ) );
		if( node )
		{
			NodeGadget *nodeGadget = graph->nodeGadget( node );
			if( nodeGadget )
			{
				outputPlugs( nodeGadget, plugs );
			}
		}
	}
	return plugs.size();
}

size_t StandardGraphLayout::unconnectedInputPlugs( NodeGadget *nodeGadget, std::vector<Plug *> &plugs ) const
{
	plugs.clear();
	for( RecursiveInputPlugIterator it( nodeGadget->node() ); it != it.end(); it++ )
	{
		if( (*it)->getInput<Plug>() == 0 and nodeGadget->nodule( *it ) )
		{
			plugs.push_back( it->get() );
		}
	}
	return plugs.size();
}

Gaffer::Plug *StandardGraphLayout::correspondingOutput( const Gaffer::Plug *input ) const
{
	/// \todo Consider adding this to DependencyNode as a correspondingOutput() method. If we do,
	/// then the method should be virtual and we should reimplement it more efficiently in derived
	/// classes wherever possible.
	const DependencyNode *dependencyNode = IECore::runTimeCast<const DependencyNode>( input->node() );
	if( !dependencyNode )
	{
		return 0;
	}
		
	for( RecursiveOutputPlugIterator it( dependencyNode ); it != it.end(); ++it )
	{
		if( dependencyNode->correspondingInput( *it ) == input )
		{
			return it->get();
		}
	}
	
	return 0;
}

bool StandardGraphLayout::nodeConstraints( GraphGadget *graph, Gaffer::Node *node, Gaffer::Set *excludedNodes, Imath::Box2f &hardConstraint, Imath::V2f &softConstraint ) const
{
	// find all the connections which aren't excluded
	
	std::vector<ConnectionGadget *> connections;
	if( !graph->connectionGadgets( node, connections, excludedNodes ) )
	{
		// there's nothing to go on - give up
		return false;
	}
	
	// figure out a position based on those connections
	
	softConstraint = V2f( 0 );
	hardConstraint = Box2f( V2f( V2f::baseTypeMin() ), V2f( V2f::baseTypeMax() ) );
	
	for( std::vector<ConnectionGadget *>::const_iterator it = connections.begin(), eIt = connections.end(); it != eIt; it++ )
	{
		// find the nodule at the other end of the connection
		const ConnectionGadget *connection = *it;
		const Nodule *nodule = 0;
		if( connection->srcNodule()->plug()->node() == node )
		{
			nodule = connection->dstNodule();
		}
		else
		{
			nodule = connection->srcNodule();
		}
	
		// use it to update the constraints
		
		V3f	nodulePos = nodule->transformedBound( 0 ).center();		
		softConstraint += V2f( nodulePos.x, nodulePos.y );
		
		const NodeGadget *nodeGadget = nodule->ancestor<NodeGadget>();
		V3f tangent = nodeGadget->noduleTangent( nodule );
		
		if( tangent.dot( V3f( 0, -1, 0 ) ) > 0.5f ) // down
		{
			hardConstraint.max.y = std::min( hardConstraint.max.y, nodulePos.y - 10.0f );
		}
		else if( tangent.dot( V3f( 0, 1, 0 ) ) > 0.5f ) // up
		{
			hardConstraint.min.y = std::max( hardConstraint.min.y, nodulePos.y + 10.0f );
		}
		
		if( tangent.dot( V3f( 1, 0, 0 ) ) > 0.5f ) // right
		{
			hardConstraint.min.x = std::max( hardConstraint.min.x, nodulePos.x + 10.0f );
		}
		else if( tangent.dot( V3f( -1, 0, 0 ) ) > 0.5f ) // left
		{
			hardConstraint.max.x = std::min( hardConstraint.max.x, nodulePos.x - 10.0f );
		}
	}

	softConstraint /= connections.size();
	
	return true;
}
