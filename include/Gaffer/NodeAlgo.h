//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFER_NODEALGO_H
#define GAFFER_NODEALGO_H

#include "Gaffer/Node.h"

namespace Gaffer
{

namespace NodeAlgo
{

/// Visiting connected nodes
/// ========================
///
/// These functions invoke a `visitor` functor for all nodes which are connected to a
/// particular node (either directly or via intermediate nodes). The visitor must be
/// callable as `bool visitor( Node *node )`. If the visitor returns false then visitation
/// is pruned at `node`.
///
/// We use the following terminology :
///
/// - "Upstream": Refers to nodes reachable via connections _in_ to the _input_ plugs
///   of each node.
/// - "Downstream" : Refers to nodes reachable via connections _from_ the _output_
///   plugs of each node.
/// - "Connections" : Refers to nodes reachable through any combination of input or
///   output connections. At each node, we first traverse through input connections
///   and then through output connections.

/// The order in which the graph is traversed.
enum class VisitOrder
{
	/// Visits all connections down the first branch
	/// before returning and following all connections down
	/// the next branch, and so on.
	DepthFirst,
	/// Visits all directly connected nodes before progressing
	/// to visit their own connections and so on. This prioritises
	/// nodes that are close to the starting node.
	BreadthFirst
};

template<typename Visitor>
void visitUpstream( Node *node, Visitor &&visitor, VisitOrder order = VisitOrder::BreadthFirst );

template<typename Visitor>
void visitDownstream( Node *node, Visitor &&visitor, VisitOrder order = VisitOrder::BreadthFirst );

template<typename Visitor>
void visitConnected( Node *node, Visitor &&visitor, VisitOrder order = VisitOrder::BreadthFirst );

/// Finding a connected node
/// ========================
///
/// These functions use the `visit()` methods to find the first node matching a
/// predicate. The predicate must be callable as `bool predicate( const Node *node )`.

template<typename Predicate>
Node *findUpstream( Node *node, Predicate &&predicate, VisitOrder order = VisitOrder::BreadthFirst );

template<typename Predicate>
Node *findDownstream( Node *node, Predicate &&predicate, VisitOrder order = VisitOrder::BreadthFirst );

template<typename Predicate>
Node *findConnected( Node *node, Predicate &&predicate, VisitOrder order = VisitOrder::BreadthFirst );

/// Finding all connected nodes
/// ===========================

/// These functions use the `visit()` methods to find the all nodes matching a
/// predicate. The predicate must be callable as `bool predicate( const Node *node )`.
///
/// > Note : These behave differently to the similar methods on `GafferUI::GraphGadget`.
/// > The latter only considers connections that are visible to the user and nodes that are
/// > visible in the UI. These methods consider all connections and nodes.

template<typename Predicate>
std::vector<Node *> findAllUpstream( Node *node, Predicate &&predicate, VisitOrder order = VisitOrder::BreadthFirst );

template<typename Predicate>
std::vector<Node *> findAllDownstream( Node *node, Predicate &&predicate, VisitOrder order = VisitOrder::BreadthFirst );

template<typename Predicate>
std::vector<Node *> findAllConnected( Node *node, Predicate &&predicate, VisitOrder order = VisitOrder::BreadthFirst );

/// Finding connected nodes by type
/// =================================
///
/// These functions return all upstream/downstream/connected nodes of a particular type.
/// Nodes are returned in the order in which they would be visited via the `visit()` methods,
/// as determined by the `order` argument. The default BreadthFirst returns nodes in order
/// of distance from the starting node.

template<typename T = Node>
std::vector<T *> upstreamNodes( Node *node, VisitOrder order = VisitOrder::BreadthFirst );

template<typename T = Node>
std::vector<T *> downstreamNodes( Node *node, VisitOrder order = VisitOrder::BreadthFirst );

template<typename T = Node>
std::vector<T *> connectedNodes( Node *node, VisitOrder order = VisitOrder::BreadthFirst );

} // namespace NodeAlgo

} // namespace Gaffer

#include "Gaffer/NodeAlgo.inl"

#endif // GAFFER_NODEALGO_H
