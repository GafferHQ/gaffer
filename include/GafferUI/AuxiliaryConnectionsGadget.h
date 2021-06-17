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

#ifndef GAFFERUI_AUXILIARYCONNECTIONSGADGET_H
#define GAFFERUI_AUXILIARYCONNECTIONSGADGET_H

#include "GafferUI/Gadget.h"

#include "boost/multi_index/member.hpp"
#include "boost/multi_index/hashed_index.hpp"
#include "boost/multi_index_container.hpp"

#include <unordered_map>

namespace Gaffer
{

class Plug;
class Node;

} // namespace Gaffer

namespace GafferUI
{

class GraphGadget;
class NodeGadget;
class Nodule;

/// Renders the "auxiliary" connections within a node graph. These
/// are defined as connections into plugs which don't have a nodule
/// of their own (although their parent may have a nodule).
class GAFFERUI_API AuxiliaryConnectionsGadget : public Gadget
{

	public :

		~AuxiliaryConnectionsGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::AuxiliaryConnectionsGadget, AuxiliaryConnectionsGadgetTypeId, Gadget );

		/// Gadgets may either be NodeGadgets or Nodules.
		bool hasConnection( const Gadget *srcGadget, const Gadget *dstGadget ) const;
		bool hasConnection( const Gaffer::Node *srcNode, const Gaffer::Node *dstNode ) const;

		std::pair<Gadget *, Gadget *> connectionAt( const IECore::LineSegment3f &position );
		std::pair<const Gadget *, const Gadget *> connectionAt( const IECore::LineSegment3f &position ) const;

		bool acceptsParent( const GraphComponent *potentialParent ) const override;
		std::string getToolTip( const IECore::LineSegment3f &position ) const override;

	protected :

		// Constructor is protected because we only want
		// GraphGadget to be able to construct these, which
		// we allow by giving it friend access.
		AuxiliaryConnectionsGadget();

		friend class GraphGadget;

		void parentChanging( Gaffer::GraphComponent *newParent ) override;
		void doRenderLayer( Layer layer, const Style *style ) const override;
		unsigned layerMask() const override;

	private :

		GraphGadget *graphGadget();
		const GraphGadget *graphGadget() const;

		void graphGadgetChildAdded( GraphComponent *child );
		void graphGadgetChildRemoved( const GraphComponent *child );

		void plugInputChanged( const Gaffer::Plug *plug );
		void childRemoved( const Gaffer::GraphComponent *node, const Gaffer::GraphComponent *child );

		void noduleAdded( const NodeGadget *nodeGadget, const Nodule *nodule );
		void noduleRemoved( const NodeGadget *nodeGadget, const Nodule *nodule );

		void dirtyInputConnections( const NodeGadget *nodeGadget );
		void dirtyOutputConnections( const NodeGadget *nodeGadget );

		void updateConnections() const;

		struct AuxiliaryConnection;
		void renderConnection( const AuxiliaryConnection &connection, const Style *style ) const;

		struct Connections
		{
			boost::signals::scoped_connection plugInputChangedConnection;
			boost::signals::scoped_connection noduleAddedConnection;
			boost::signals::scoped_connection noduleRemovedConnection;
			boost::signals::scoped_connection childRemovedConnection;
			bool dirty = true;
		};

		boost::signals::scoped_connection m_graphGadgetChildAddedConnection;
		boost::signals::scoped_connection m_graphGadgetChildRemovedConnection;

		// Key is the NodeGadget at the destination end of the connections
		// tracked by `Connections.dirty`.
		typedef std::unordered_map<const NodeGadget *, Connections> NodeGadgetConnections;
		mutable NodeGadgetConnections m_nodeGadgetConnections;

		// An auxiliary connection that we will draw.
		struct AuxiliaryConnection
		{
			const NodeGadget *srcNodeGadget;
			const NodeGadget *dstNodeGadget;
			// Endpoints may be srcNodeGadget/dstNodeGadget, or Nodules
			// belonging to them.
			std::pair<const Gadget *, const Gadget *> endpoints;
		};

		// Container for all our auxiliary connections.
		using AuxiliaryConnections = boost::multi_index::multi_index_container<
			AuxiliaryConnection,
			boost::multi_index::indexed_by<
				// Primary key is the unique pair of endpoint
				// gadgets the connection represents.
				boost::multi_index::hashed_unique<
					boost::multi_index::member<AuxiliaryConnection, std::pair<const Gadget *, const Gadget *>, &AuxiliaryConnection::endpoints>
				>,
				// Access to the range of connections originating
				// at `srcNodeGadget`. This will include all source
				// endpoints which are either `srcNodeGadget` itself
				// or are a nodule belonging to it.
				boost::multi_index::hashed_non_unique<
					boost::multi_index::member<AuxiliaryConnection, const NodeGadget *, &AuxiliaryConnection::srcNodeGadget>
				>,
				// Access to the range of connections ending at
				// `dstNodeGadget`. This will include all destination
				// endpoints which are either `dstNodeGadget` itself or
				// are a nodule belonging to it.
				boost::multi_index::hashed_non_unique<
					boost::multi_index::member<AuxiliaryConnection, const NodeGadget *, &AuxiliaryConnection::dstNodeGadget>
				>
			>
		>;

		mutable AuxiliaryConnections m_auxiliaryConnections;
		mutable bool m_dirty;

		// Convenience accessors for the secondary indexes of `m_auxiliaryConnections`.

		using SrcNodeGadgetIndex = AuxiliaryConnections::nth_index<1>::type;
		using DstNodeGadgetIndex = AuxiliaryConnections::nth_index<2>::type;
		SrcNodeGadgetIndex &srcNodeGadgetIndex() const;
		DstNodeGadgetIndex &dstNodeGadgetIndex() const;

};

} // namespace GafferUI

#endif // GAFFERUI_AUXILIARYCONNECTIONSGADGET_H
