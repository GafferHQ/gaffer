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

#include "boost/container/flat_set.hpp"

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
/// are defined as connections into plugs which don't have a nodule.
class GAFFERUI_API AuxiliaryConnectionsGadget : public Gadget
{

	public :

		~AuxiliaryConnectionsGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::AuxiliaryConnectionsGadget, AuxiliaryConnectionsGadgetTypeId, Gadget );

		bool hasConnection( const NodeGadget *srcNodeGadget, const NodeGadget *dstNodeGadget ) const;
		bool hasConnection( const Gaffer::Node *srcNode, const Gaffer::Node *dstNode ) const;

		std::pair<NodeGadget *, NodeGadget *> connectionAt( const IECore::LineSegment3f &position );
		std::pair<const NodeGadget *, const NodeGadget *> connectionAt( const IECore::LineSegment3f &position ) const;

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

	private :

		GraphGadget *graphGadget();
		const GraphGadget *graphGadget() const;

		void graphGadgetChildAdded( GraphComponent *child );
		void graphGadgetChildRemoved( const GraphComponent *child );

		void plugInputChanged( const Gaffer::Plug *plug );
		void childRemoved( const Gaffer::GraphComponent *node, const Gaffer::GraphComponent *child );

		void noduleAdded( const NodeGadget *nodeGadget, const Nodule *nodule );
		void noduleRemoved( const NodeGadget *nodeGadget, const Nodule *nodule );

		void dirty( const NodeGadget *nodeGadget );

		void updateConnections() const;

		struct Connections
		{
			boost::signals::scoped_connection plugInputChangedConnection;
			boost::signals::scoped_connection noduleAddedConnection;
			boost::signals::scoped_connection noduleRemovedConnection;
			boost::signals::scoped_connection childRemovedConnection;
			// The set of all NodeGadgets at the source end of the connections.
			boost::container::flat_set<const NodeGadget *> sourceGadgets;
			bool dirty = true;
		};

		boost::signals::scoped_connection m_graphGadgetChildAddedConnection;
		boost::signals::scoped_connection m_graphGadgetChildRemovedConnection;

		// Key is the NodeGadget at the destination end of the connections.
		typedef std::unordered_map<const NodeGadget *, Connections> NodeGadgetConnections;
		mutable NodeGadgetConnections m_nodeGadgetConnections;
		mutable bool m_dirty;

};

} // namespace GafferUI

#endif // GAFFERUI_AUXILIARYCONNECTIONSGADGET_H
