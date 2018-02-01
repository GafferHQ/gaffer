//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"
#include "Gaffer/GraphComponent.h"

#include "GafferUI/AuxiliaryConnectionsGadget.h"
#include "GafferUI/AuxiliaryConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"


using namespace GafferUI;
using namespace Imath;

AuxiliaryConnectionsGadget::AuxiliaryConnectionsGadget()
	: Gadget()
{
}

AuxiliaryConnectionsGadget::~AuxiliaryConnectionsGadget()
{
}

Box3f AuxiliaryConnectionsGadget::bound() const
{
	// \todo
	return Box3f();
}

void AuxiliaryConnectionsGadget::markDirty( const Gaffer::Plug *dstPlug )
{
	// We just mark the whole node as dirty. We could potentially be a bit
	// smarter about it at some point, but this seems sufficient for now.

	const GraphGadget *gg = graphGadget();

	if( !dstPlug->node() )
	{
		return;
	}

	const NodeGadget *nodeGadget = gg->nodeGadget( dstPlug->node() );
	if( !nodeGadget )
	{
		return;
	}

	m_nodeGadgetsToUpdate.emplace( nodeGadget );
}

void AuxiliaryConnectionsGadget::markDirty( ConstNodeGadgetPtr nodeGadget )
{
	m_nodeGadgetsToUpdate.insert( nodeGadget );
}

void AuxiliaryConnectionsGadget::doRenderLayer( Layer layer, const Style *style ) const
{
	switch ( layer )
	{

	case GraphLayer::Connections :

		// update auxiliary connections before rendering them
		updateAuxiliaryConnections();
		Gadget::doRenderLayer( layer, style );

	default :
		break;

	}
}

const GraphGadget *AuxiliaryConnectionsGadget::graphGadget() const
{
	return ancestor<GraphGadget>();
}

void AuxiliaryConnectionsGadget::addAuxiliaryConnection( const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug )
{
	const GraphGadget *gg = graphGadget();
	const NodeGadget *srcNodeGadget = gg->nodeGadget( srcPlug->node() );
	const NodeGadget *dstNodeGadget = gg->nodeGadget( dstPlug->node() );

	if( !srcNodeGadget || !dstNodeGadget )
	{
		// \todo Do we need to throw an exception here?
		//       I'm returning here so that we don't show connections to invisible
		//       animation curve nodes, for instance.
		return;
	}

	AuxiliaryConnectionGadget *newConnection = m_auxiliaryConnectionGadgets.insert( srcNodeGadget, dstNodeGadget, srcPlug, dstPlug );
	if( newConnection )
	{
		addChild( newConnection );
	}

	requestRender();
}

void AuxiliaryConnectionsGadget::removeAuxiliaryConnectionGadgets( const NodeGadget *nodeGadget )
{
	// remove all connections that involve plugs on this node
	for( Gaffer::RecursivePlugIterator it( nodeGadget->node() ); !it.done(); ++it )
	{
		if( (*it)->direction() == Gaffer::Plug::In )
		{
			removeAuxiliaryConnection( (*it).get() );
		}
		else
		{
			const Gaffer::Plug::OutputContainer &outputs = (*it).get()->outputs();
			for( Gaffer::Plug::OutputContainer::const_iterator it = outputs.begin(), eIt = outputs.end(); it != eIt; ++it )
			{
				removeAuxiliaryConnection( (*it) );
			}
		}
	}

	// make sure we don't accidentally recreate them before the gadget is destroyed
	m_nodeGadgetsToUpdate.erase( nodeGadget );
}

void AuxiliaryConnectionsGadget::removeAuxiliaryConnection( const Gaffer::Plug *dstPlug )
{
	AuxiliaryConnectionGadget *connection = m_auxiliaryConnectionGadgets.find( dstPlug );
	if( connection )
	{
		bool removedGadget =  m_auxiliaryConnectionGadgets.erase( dstPlug );
		if( removedGadget )
		{
			removeChild( connection );
		}
	}
}

AuxiliaryConnectionGadget *AuxiliaryConnectionsGadget::auxiliaryConnectionGadget( const Gaffer::Plug *dstPlug )
{
	// make sure we've answered to all requests about updating data
	updateAuxiliaryConnections();

	return findAuxiliaryConnectionGadget( dstPlug );
}

const AuxiliaryConnectionGadget *AuxiliaryConnectionsGadget::auxiliaryConnectionGadget( const Gaffer::Plug *dstPlug ) const
{
	// make sure we've answered to all requests about updating data
	updateAuxiliaryConnections();

	return findAuxiliaryConnectionGadget( dstPlug );
}

size_t AuxiliaryConnectionsGadget::auxiliaryConnectionGadgets( const Gaffer::Plug *plug, std::vector<AuxiliaryConnectionGadget *> &connections, const Gaffer::Set *excludedNodes )
{
	// make sure we've answered to all requests about updating data
	updateAuxiliaryConnections();

	if( plug->direction() == Gaffer::Plug::In )
	{
		const Gaffer::Plug *input = plug->getInput<Gaffer::Plug>();
		if( input )
		{
			if( !excludedNodes || !excludedNodes->contains( input->node() ) )
			{
				AuxiliaryConnectionGadget *connection = m_auxiliaryConnectionGadgets.find( plug );
				if( connection )
				{
					connections.push_back( connection );
				}
			}
		}
	}
	else
	{
		const Gaffer::Plug::OutputContainer &outputs = plug->outputs();
		for( Gaffer::Plug::OutputContainer::const_iterator it = outputs.begin(), eIt = outputs.end(); it != eIt; ++it )
		{
			if( excludedNodes && excludedNodes->contains( (*it)->node() ) )
			{
				continue;
			}
			AuxiliaryConnectionGadget *connection = m_auxiliaryConnectionGadgets.find( *it );
			if( connection )
			{
				connections.push_back( connection );
			}
		}
	}
	return connections.size();
}

size_t AuxiliaryConnectionsGadget::auxiliaryConnectionGadgets( const Gaffer::Plug *plug, std::vector<const AuxiliaryConnectionGadget *> &connections, const Gaffer::Set *excludedNodes ) const
{
	// preferring naughty casts over maintaining two identical implementations
	return const_cast<AuxiliaryConnectionsGadget *>( this )->auxiliaryConnectionGadgets( plug, reinterpret_cast<std::vector<AuxiliaryConnectionGadget *> &>( connections ), excludedNodes );
}

size_t AuxiliaryConnectionsGadget::auxiliaryConnectionGadgets( const Gaffer::Node *node, std::vector<AuxiliaryConnectionGadget *> &connections, const Gaffer::Set *excludedNodes )
{
	// make sure we've answered to all requests about updating data
	updateAuxiliaryConnections();

	for( Gaffer::RecursivePlugIterator it( node ); !it.done(); ++it )
	{
		this->auxiliaryConnectionGadgets( it->get(), connections, excludedNodes );
	}

	return connections.size();
}

size_t AuxiliaryConnectionsGadget::auxiliaryConnectionGadgets( const Gaffer::Node *node, std::vector<const AuxiliaryConnectionGadget *> &connections, const Gaffer::Set *excludedNodes ) const
{
	// preferring naughty casts over maintaining two identical implementations
	return const_cast<AuxiliaryConnectionsGadget *>( this )->auxiliaryConnectionGadgets( node, reinterpret_cast<std::vector<AuxiliaryConnectionGadget *> &>( connections ), excludedNodes );
}

AuxiliaryConnectionGadget *AuxiliaryConnectionsGadget::findAuxiliaryConnectionGadget( const Gaffer::Plug *dstPlug ) const
{
	const Gaffer::Plug *srcPlug = dstPlug->getInput();
	if( !srcPlug )
	{
		return nullptr;
	}

	const GraphGadget *gg = graphGadget();
	const NodeGadget *dstNodeGadget = gg->nodeGadget( dstPlug->node() );
	const NodeGadget *srcNodeGadget = gg->nodeGadget( srcPlug->node() );
	if( !( dstNodeGadget && srcNodeGadget ) )
	{
		return nullptr;
	}

	return m_auxiliaryConnectionGadgets.find( srcNodeGadget, dstNodeGadget );
}

void AuxiliaryConnectionsGadget::updateAuxiliaryConnections() const
{
	for( const auto &nodeGadget : m_nodeGadgetsToUpdate )
	{

		// remove existing auxiliary connections
		for( Gaffer::RecursivePlugIterator it( nodeGadget->node() ); !it.done(); ++it )
		{
			const_cast<AuxiliaryConnectionsGadget *>( this )->removeAuxiliaryConnection( (*it).get() );
		}

		// recreate necessary auxiliary connections
		for( Gaffer::RecursivePlugIterator it( nodeGadget->node() ); !it.done(); ++it )
		{
			const Gaffer::Plug *dstPlug = IECore::runTimeCast<Gaffer::Plug>( (*it).get() );
			const Gaffer::Plug *srcPlug = dstPlug->getInput();
			if( !srcPlug )
			{
				continue;
			}

			it.prune();

			if( srcPlug->node() == dstPlug->node() )
			{
				continue;
			}

			const GraphGadget *gg = graphGadget();
			const NodeGadget *srcNodeGadget = gg->nodeGadget( srcPlug->node() );

			if( nodeGadget->nodule( dstPlug ) && srcNodeGadget->nodule( srcPlug ) )
			{
				continue;
			}

			const_cast<AuxiliaryConnectionsGadget *>( this )->addAuxiliaryConnection( srcPlug, dstPlug );
		}
	}

	// all necessary updates have been performed, cleaning up
	m_nodeGadgetsToUpdate.clear();

}

AuxiliaryConnectionGadget *AuxiliaryConnectionsGadget::AuxiliaryConnectionGadgetContainer::find( const NodeGadget *srcGadget, const NodeGadget *dstGadget ) const
{
	auto it = m_nodesMap.find( NodesKey( srcGadget, dstGadget ) );
	if( it == m_nodesMap.end() )
	{
		return nullptr;
	}
	return (*it).second;
}

AuxiliaryConnectionGadget *AuxiliaryConnectionsGadget::AuxiliaryConnectionGadgetContainer::find( const Gaffer::Plug *dstPlug ) const
{
	auto keyIt = m_plugMap.find( dstPlug );
	if( keyIt == m_plugMap.end() )
	{
		return nullptr;
	}
	NodesKey key = (*keyIt).second;

	auto connectionIt = m_nodesMap.find( key );
	if( connectionIt == m_nodesMap.end() )
	{
		return nullptr;
	}

	return (*connectionIt).second;
}

AuxiliaryConnectionGadget *AuxiliaryConnectionsGadget::AuxiliaryConnectionGadgetContainer::insert( const NodeGadget *srcNodeGadget, const NodeGadget *dstNodeGadget, const Gaffer::Plug *srcPlug, const Gaffer::Plug *dstPlug )
{
	bool addedNew = false;
	NodesKey key( srcNodeGadget, dstNodeGadget );

	AuxiliaryConnectionGadget *auxiliaryConnectionGadget = find( srcNodeGadget, dstNodeGadget );
	if( !auxiliaryConnectionGadget )
	{
		auxiliaryConnectionGadget = new AuxiliaryConnectionGadget( srcNodeGadget, dstNodeGadget);
		m_nodesMap[key] = auxiliaryConnectionGadget;

		addedNew = true;
	}

	auxiliaryConnectionGadget->addConnection( srcPlug, dstPlug );

	m_plugMap[dstPlug] = key;
	if( addedNew )
	{
		return auxiliaryConnectionGadget;
	}
	else
	{
		return nullptr;
	}
}

bool AuxiliaryConnectionsGadget::AuxiliaryConnectionGadgetContainer::erase( const Gaffer::Plug *dstPlug )
{
	auto keyIt = m_plugMap.find( dstPlug );
	if( keyIt == m_plugMap.end() )
	{
		return false;
	}

	NodesKey key = (*keyIt).second;
	m_plugMap.erase( dstPlug );

	auto connectionIt = m_nodesMap.find( key );
	if( connectionIt == m_nodesMap.end() )
	{
		return false;
	}

	(*connectionIt).second->removeConnection( dstPlug );
	if( (*connectionIt).second->empty() )
	{
		m_nodesMap.erase( key );
		return true;
	}
	return false;
}
