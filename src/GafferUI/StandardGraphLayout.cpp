//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/StandardGraphLayout.h"

#include "GafferUI/CompoundNodule.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/AuxiliaryNodeGadget.h"
#include "GafferUI/AuxiliaryConnectionsGadget.h"
#include "GafferUI/Nodule.h"

#include "Gaffer/BoxOut.h"
#include "Gaffer/ContextProcessor.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/Dot.h"
#include "Gaffer/EditScope.h"
#include "Gaffer/Loop.h"
#include "Gaffer/NameSwitch.h"
#include "Gaffer/Plug.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/Switch.h"

#include "IECore/BoundedKDTree.h"
#include "IECore/BoxAlgo.h"
#include "IECore/Export.h"
#include "IECore/MessageHandler.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathVec.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/graph/adjacency_list.hpp"

#include <cassert>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
//
// Layout Engine
//
// Internal code for performing node positioning and layout, targeted
// at the kinds of graphs produced using the StandardNodeGadget.
//
// Such graphs are strongly directional, but nodes may accept connections
// on all sides, and connections may therefore flow horizontally /and/
// vertically within the same graph. Additionally, each connection endpoint
// is located at a specific fixed location on the node, so the relative
// position of inputs to a node is important when attempting to reduce
// unnecessary crossings among connections.
//
// Unfortunately, the standard layered drawing algorithms (such as Sugiyama's)
// are not a good fit for our purposes because they lay out nodes in a single
// direction only. Standard force directed algorithms are not a good match
// for us either, as they produce organic looking graphs which provide no
// control over the direction of connections, or mechanisms for explicitly
// reducing crossings.
//
// We adopt a hybrid approach where we combine force directed layout with
// additional hard constraints that enforce the directionality of connections
// and ordering of inputs to minimise crossings. This approach is based on
// ideas described in the following paper :
//
// Scalable, Versatile and Simple Constrained Graph Layout
// Tim Dwyer
// Eurographics/ IEEE-VGTC Symposium on Visualization 2009
//
// The current implementation still has plenty of room for improvement -
// here are a few ideas worth exploring :
//
//    - Repulsive forces between nodes, proportional to the length
//      of the shortest path between them.
//
//    - Segmenting the graph into vertical and horizontal chunks
//      and grouping the nodes in the horizontal chunks after laying
//      them out separately. Or even better perhaps, preventing the
//      convex hulls of such chunks from overlapping using the method
//      described in the Dwyer paper.
//
//    - Alignment constraints between nodes with only a single
//      input/output.
//
//    - Investigating the balance between spring stiffness, number
//      of constraints iterations etc.
//
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Refactor into simple constraint in single axis,
/// remove LessThanOrEqualTo.
class Constraint
{

	public :

		enum Type
		{
			EqualTo,
			GreaterThanOrEqualTo,
			LessThanOrEqualTo
		};

		/// \todo Remove - it's only here so we can call m_constraints.resize()
		/// to remove the collision constraints.
		Constraint()
		{
		}

		// Enforces p - q ( ==, >=, <= ) d in direction v
		Constraint( V2f *p, V2f *q, Type type, float d, const V2f &v, float w = 0.5 )
			:	m_p( p ), m_q( q ), m_type( type ), m_d( d ), m_v( v ), m_w( w )
		{
		}

		void apply() const
		{
			const float p = m_v.dot( *m_p );
			const float q = m_v.dot( *m_q );
			const float separation = p - q;

			if(
				( m_type == EqualTo && separation == m_d ) ||
				( m_type == GreaterThanOrEqualTo && separation >= m_d ) ||
				( m_type == LessThanOrEqualTo && separation <= m_d )
			)
			{
				return;
			}

			const V2f r = m_v * (m_d - separation);
			*m_p += r * m_w;
			*m_q -= r * (1.0f - m_w);
		}

	private :

		V2f *m_p;
		V2f *m_q;
		Type m_type;
		float m_d;
		V2f m_v;
		float m_w;

};

class LayoutEngine
{

	public :

		LayoutEngine( GraphGadget *graphGadget, float edgeLengthScale, float nodeSeparationScale )
			:	m_graphGadget( graphGadget ),
				m_edgeLength( 4.0f * edgeLengthScale ),
				m_nodeSeparation( 2.0f * nodeSeparationScale ),
				m_springStiffness( 0.1 ),
				m_maxIterations( 10000 ),
				m_constraintsIterations( 10 )
		{

			// Convert the visible graph into our internal boost::graph format.
			// Start by putting all the visible nodes in the graph as vertices.
			// Build a map from node to vertex so we can use it to lookup nodes
			// when inserting edges.

			for( Node::Iterator it( graphGadget->getRoot() ); !it.done(); ++it )
			{
				Node *node = it->get();
				const NodeGadget *nodeGadget = graphGadget->nodeGadget( node );
				if( !nodeGadget )
				{
					continue;
				}

				Box3f bb = nodeGadget->bound();

				bool auxiliary = bool( runTimeCast<const AuxiliaryNodeGadget>( nodeGadget ) );

				VertexDescriptor v = add_vertex( m_graph );
				m_graph[v].node = node;
				m_graph[v].position = graphGadget->getNodePosition( node );
				m_graph[v].bound = Box2f( V2f( bb.min.x, bb.min.y ), V2f( bb.max.x, bb.max.y ) );
				m_graph[v].pinned = false;
				m_graph[v].collisionGroup = 0;
				m_graph[v].auxiliary = auxiliary;
				m_nodesToVertices[node] = v;
			}

			// Put all the visible connections in the graph as edges.

			for( NodesToVertices::const_iterator it = m_nodesToVertices.begin(), eIt = m_nodesToVertices.end(); it != eIt; ++it )
			{
				for( Plug::RecursiveInputIterator pIt( it->first ); !pIt.done(); ++pIt )
				{
					ConnectionGadget *connection = graphGadget->connectionGadget( pIt->get() );
					if( !connection || connection->getMinimised() )
					{
						continue;
					}

					const Nodule *srcNodule = connection->srcNodule();
					if( !srcNodule )
					{
						continue;
					}

					const Nodule *dstNodule = connection->dstNodule();

					NodesToVertices::const_iterator srcIt = m_nodesToVertices.find( srcNodule->plug()->node() );
					if( srcIt == m_nodesToVertices.end() )
					{
						continue;
					}

					const NodeGadget *srcNodeGadget = graphGadget->nodeGadget( srcNodule->plug()->node() );
					const NodeGadget *dstNodeGadget = graphGadget->nodeGadget( dstNodule->plug()->node() );
					const V3f srcNoduleOffset = srcNodule->transformedBound( srcNodeGadget ).center();
					const V3f dstNoduleOffset = dstNodule->transformedBound( dstNodeGadget ).center();
					const V3f srcNoduleTangent( srcNodeGadget->connectionTangent( srcNodule ) );
					const V3f dstNoduleTangent( dstNodeGadget->connectionTangent( dstNodule ) );

					EdgeDescriptor e = add_edge( srcIt->second, it->second, m_graph ).first;
					m_graph[e].sourceOffset = V2f( srcNoduleOffset.x, srcNoduleOffset.y );
					m_graph[e].targetOffset = V2f( dstNoduleOffset.x, dstNoduleOffset.y );
					m_graph[e].sourceTangent = direction( srcNoduleTangent );
					m_graph[e].targetTangent = direction( dstNoduleTangent );
					m_graph[e].idealDirection = direction( srcNoduleTangent - dstNoduleTangent );
				}
			}

		}

		void pinNode( Node *node )
		{
			NodesToVertices::const_iterator it = m_nodesToVertices.find( node );
			if( it == m_nodesToVertices.end() )
			{
				return;
			}

			m_graph[it->second].pinned = true;
		}

		void pinNodes( const Gaffer::Set *nodes, bool invert = false )
		{
			for( NodesToVertices::const_iterator it = m_nodesToVertices.begin(), eIt = m_nodesToVertices.end(); it != eIt; ++it )
			{
				if( nodes->contains( it->first ) != invert )
				{
					m_graph[it->second].pinned = true;
				}
			}
		}

		void pinNonAuxiliaryNodes( const Gaffer::Set *nodes )
		{
			for( NodesToVertices::const_iterator it = m_nodesToVertices.begin(), eIt = m_nodesToVertices.end(); it != eIt; ++it )
			{
				if( nodes && !nodes->contains( it->first ) )
				{
					continue;
				}

				if( !m_graph[it->second].auxiliary )
				{
					m_graph[it->second].pinned = true;
				}
			}
		}

		void groupNodes( const Gaffer::Set *nodes, const V2f &center )
		{
			// get vertex descriptors for the nodes we want to group.
			// while we're doing that, compute their bounding box.

			Box2f bound;
			vector<VertexDescriptor> childVertexDescriptors;
			for( size_t i = 0, s = nodes->size(); i < s; ++ i )
			{
				const Node *node = runTimeCast<const Node>( nodes->member( i ) );
				if( !node )
				{
					continue;
				}

				NodesToVertices::iterator it = m_nodesToVertices.find( node );
				if( it == m_nodesToVertices.end() )
				{
					continue;
				}

				childVertexDescriptors.push_back( it->second );

				const Vertex &child = m_graph[it->second];
				bound.extendBy( child.bound.min + child.position );
				bound.extendBy( child.bound.max + child.position );
			}

			// early out if nothing to group

			if( childVertexDescriptors.empty() )
			{
				return;
			}

			// make a new vertex to represent the group, and set its
			// position and bounding box to enclose the children.

			VertexDescriptor groupDescriptor = add_vertex( m_graph );
			Vertex &group = m_graph[groupDescriptor];
			group.node = nullptr;
			group.pinned = false;
			group.collisionGroup = 0;
			group.position = bound.center();
			group.bound = Box2f( bound.min - group.position, bound.max - group.position );

			// remove and add edges as needed. edges internal to
			// the group are removed, so that they won't clash with
			// the constraints we use to keep the children in position
			// relative to the group. edges connecting nodes inside the
			// group to nodes outside the group are replaced with edges
			// connecting the group itself to the external nodes.

			vector<EdgeDescriptor> edgesToRemove;
			EdgeIteratorRange e = edges( m_graph );
			for( EdgeIterator eIt = e.first; eIt != e.second; ++eIt )
			{
				const VertexDescriptor s = source( *eIt, m_graph );
				const VertexDescriptor t = target( *eIt, m_graph );
				const bool sInternal = nodes->contains( m_graph[s].node );
				const bool tInternal = nodes->contains( m_graph[t].node );
				if( !sInternal && !tInternal )
				{
					// edge is entirely outside group
					continue;
				}

				if( sInternal != tInternal )
				{
					// edge connects group to outside world, move
					// the edge to the group.

					VertexDescriptor newS = sInternal ? groupDescriptor : s;
					VertexDescriptor newT = tInternal ? groupDescriptor : t;

					EdgeDescriptor newEdgeDescriptor = add_edge( newS, newT, m_graph ).first;
					Edge &newEdge( m_graph[newEdgeDescriptor] );

					newEdge = m_graph[*eIt];
					m_graph[newEdgeDescriptor] = m_graph[*eIt];
					if( sInternal )
					{
						newEdge.sourceOffset = ( newEdge.sourceOffset + m_graph[s].position ) - group.position;
					}
					else
					{
						newEdge.targetOffset = ( newEdge.targetOffset + m_graph[t].position ) - group.position;
					}
				}

				edgesToRemove.push_back( *eIt );
			}

			for( vector<EdgeDescriptor>::iterator it = edgesToRemove.begin(), eIt = edgesToRemove.end(); it != eIt; ++it )
			{
				remove_edge( *it, m_graph );
			}

			// add constraints to keep the children in the right positions relative to the group.

			for( vector<VertexDescriptor>::const_iterator it = childVertexDescriptors.begin(), eIt = childVertexDescriptors.end(); it != eIt; ++it )
			{
				Vertex &child = m_graph[*it];
				for( int d = 0; d < 2; ++d )
				{
					addConstraint(
						child,
						group,
						Constraint::EqualTo,
						child.position[d] - group.position[d],
						d == 0 ? V2f( 1, 0 ) : V2f( 0, 1 ),
						1.0f
					);
				}
			}

			group.position = center;
		}

		/// Collision avoidance in solve() is only performed between nodes
		/// in the same group. A negative number may be assigned to disable
		/// all collisions involving a particular node.
		void assignCollisionGroup( const Gaffer::Node *node, int group )
		{
			NodesToVertices::const_iterator it = m_nodesToVertices.find( node );
			if( it == m_nodesToVertices.end() )
			{
				return;
			}

			m_graph[it->second].collisionGroup = group;
		}

		void assignCollisionGroup( const Gaffer::Set *nodes, int group )
		{
			for( size_t i = 0, e = nodes->size(); i != e; ++i )
			{
				if( const Gaffer::Node *node = runTimeCast<const Node>( nodes->member( i ) ) )
				{
					assignCollisionGroup( node, group );
				}
			}
		}

		void assignCollisionGroup( IECore::TypeId nodeType, int group )
		{
			VertexIteratorRange v = vertices( m_graph );
			for( VertexIterator it = v.first; it != v.second; ++it )
			{
				Vertex &v = m_graph[*it];
				if( v.node && v.node->isInstanceOf( nodeType ) )
				{
					v.collisionGroup = group;
				}
			}
		}

		void addConnectionDirectionConstraints()
		{

			EdgeIteratorRange e = edges( m_graph );
			for( EdgeIterator it = e.first; it != e.second; ++it )
			{
				Vertex &src = m_graph[source( *it, m_graph )];
				Vertex &dst = m_graph[target( *it, m_graph )];
				const Edge &edge = m_graph[*it];

				for( int d = 0; d < 2; ++d )
				{
					if( edge.idealDirection[d] == 0 )
					{
						continue;
					}

					const float separation =
						edge.sourceOffset[d] * edge.idealDirection[d] -
						edge.targetOffset[d] * edge.idealDirection[d] +
						m_edgeLength;

					addConstraint(
						dst,
						src,
						Constraint::GreaterThanOrEqualTo,
						separation,
						d == 0 ? V2f( edge.idealDirection[d], 0 ) : V2f( 0, edge.idealDirection[d] )					);

				}
			}

		}

		void addSiblingConstraints()
		{
			VertexIteratorRange v = vertices( m_graph );
			for( VertexIterator it = v.first; it != v.second; ++it )
			{
				addSiblingConstraints( *it, Direction( 0, -1 ) );
				addSiblingConstraints( *it, Direction( 1, 0 ) );
			}
		}

		void addAuxiliaryConnections()
		{
			AuxiliaryConnectionsGadget *auxiliaryConnectionsGadget = m_graphGadget->auxiliaryConnectionsGadget();

			// AuxiliaryConnections can represent more than a single connection
			// between two nodes. By storing the ones added, we can make sure that we
			// don't add any twice.
			std::set<std::pair<const Node*, const Node*> > existingAuxiliaryConnections;

			// In a second step we'll handle all auxiliary nodes that have incoming
			// auxiliary connections. Of these staged vertices, we'll add additional
			// springs to those that have more than one outgoing connection.
			std::vector<std::pair<const Plug*, const Plug*> > stagedAuxiliaryConnectionPlugs;

			for( NodesToVertices::const_iterator nodeIt = m_nodesToVertices.begin(), eIt = m_nodesToVertices.end(); nodeIt != eIt; ++nodeIt )
			{
				for( Plug::RecursiveInputIterator plugIt( nodeIt->first ); !plugIt.done(); ++plugIt )
				{
					const Plug *dstPlug = plugIt->get();
					const Plug *srcPlug = dstPlug->getInput();

					if( !srcPlug )
					{
						continue;
					}

					const Node *srcNode = srcPlug->node();
					NodesToVertices::const_iterator srcIt = m_nodesToVertices.find( srcNode );
					if( srcIt == m_nodesToVertices.end() )
					{
						continue;
					}

					const Node *dstNode = dstPlug->node();
					if( !auxiliaryConnectionsGadget->hasConnection( srcNode, dstNode ) )
					{
						// Potentially an auxiliary connection represented by a StandardConnectionGadget
						const ConnectionGadget *standardConnectionGadget = m_graphGadget->connectionGadget( dstPlug ) ;
						if( !standardConnectionGadget || standardConnectionGadget->srcNodule() )
						{
							continue;
						}
					}

					if( m_graph[nodeIt->second].auxiliary )
					{
						// Determining whether incoming edges (functioning as springs) need
						// to be added to this vertex depends on the number of outgoing
						// edges. We postpone this decision to later when we know about all
						// outgoing connections.
						stagedAuxiliaryConnectionPlugs.push_back( std::make_pair( srcPlug, dstPlug ) );
						continue;
					}

					const auto nodePair = std::make_pair( srcNode, dstNode );
					if( existingAuxiliaryConnections.find( nodePair ) != existingAuxiliaryConnections.end() )
					{
							continue;
					}
					existingAuxiliaryConnections.insert( nodePair );

					addAuxiliaryConnection( srcPlug, dstPlug );
				}
			}

			for( auto plugs : stagedAuxiliaryConnectionPlugs )
			{
				const Node *dstNode = plugs.second->node();

				if( out_degree( m_nodesToVertices.find( dstNode )->second, m_graph ) <= 1 )
				{
					// Auxiliary vertices with only one outgoing connection should be put
					// close to that connected node. No need for springs that would pull
					// the two nodes apart.
					continue;
				}

				auto nodePair = std::make_pair( plugs.first->node(), dstNode );
				if( existingAuxiliaryConnections.find( nodePair ) != existingAuxiliaryConnections.end() )
				{
					continue;
				}
				existingAuxiliaryConnections.insert( nodePair );

				addAuxiliaryConnection( plugs.first, plugs.second );
			}
		}

		void clearConstraints()
		{
			m_constraints.clear();
		}

		void solve( bool withCollisions )
		{
			VertexIteratorRange v = vertices( m_graph );

			size_t numConstraints = m_constraints.size();
			for( int i = 0; i < m_maxIterations; ++i )
			{
				for( VertexIterator it = v.first; it != v.second; ++it )
				{
					Vertex &vt = m_graph[*it];
					vt.previousPosition = vt.position;
				}

				applySprings();
				applyConstraints( m_constraintsIterations );

				if( withCollisions )
				{
					addCollisionConstraints();
					applyConstraints( m_constraintsIterations );
					m_constraints.resize( numConstraints );
				}

				float maxMovement = 0;
				for( VertexIterator it = v.first; it != v.second; ++it )
				{
					const Vertex &vt = m_graph[*it];
					maxMovement = max( maxMovement, fabs( vt.position.x - vt.previousPosition.x ) );
					maxMovement = max( maxMovement, fabs( vt.position.y - vt.previousPosition.y ) );
				}

				if( maxMovement < 0.0001 )
				{
					break;
				}
			}
		}

		void applyPositions()
		{
			VertexIteratorRange v = vertices( m_graph );
			for( VertexIterator it = v.first; it != v.second; ++it )
			{
				const Vertex &v = m_graph[*it];
				if( !v.pinned && v.node )
				{
					if( !isnan( v.position.x ) && !isnan( v.position.y ) && !isinf( v.position.x ) && !isinf( v.position.y ) )
					{
						m_graphGadget->setNodePosition( v.node, v.position );
					}
					else
					{
						IECore::msg( IECore::Msg::Warning, "LayoutEngine::applyPositions", "Layout algorithm failed to produce valid position for " + v.node->getName().string() );

					}
				}
			}
		}

	private :

		// The tangents of connection endpoints are specified by NodeGadgets
		// as arbitrary V3fs. We make the simplifying assumption that they
		// are 2 dimensional, and that they are either horizontal, vertical,
		// or on one of the two 45 degree diagonals. We represent such
		// directions as integer vectors, where the x and y coordinates may
		// only have values of -1, 0 or +1.
		typedef V2s Direction;

		Direction direction( const V3f &v )
		{
			V3f vn( v.x, v.y, 0.0f );
			vn.normalize();
			return Direction( int( round( vn.x ) ), int( round( vn.y ) ) );
		}

		// We convert the visible graph of nodes and connections into a boost
		// graph of vertices and edges, to give us a better representation
		// for querying and manipulation.

		struct Vertex
		{
			// The node this vertex represents.
			// May be nullptr for vertices introduced
			// by groupNodes().
			Node *node;
			// Node position within graph.
			V2f position;
			// Node bound in local space.
			Box2f bound;
			// True if node is not to be moved.
			bool pinned;
			// Provides finer control over collision avoidance.
			int collisionGroup;

			// State variables for use in solve().
			V2f previousPosition;
			V2f force;

			// True if node is represented by a (smaller) AuxiliaryNodeGadget
			bool auxiliary;
		};

		struct Edge
		{
			// Offsets of plugs relative to
			// parent node origin.
			V2f sourceOffset;
			V2f targetOffset;

			Direction sourceTangent;
			Direction targetTangent;
			Direction idealDirection;
		};

		typedef boost::adjacency_list<boost::listS, boost::listS, boost::bidirectionalS, Vertex, Edge> Graph;

		typedef Graph::vertex_descriptor VertexDescriptor;
		typedef Graph::edge_descriptor EdgeDescriptor;

		typedef Graph::vertex_iterator VertexIterator;
		typedef std::pair<VertexIterator, VertexIterator> VertexIteratorRange;

		typedef Graph::in_edge_iterator InEdgeIterator;
		typedef std::pair<InEdgeIterator, InEdgeIterator> InEdgeIteratorRange;

		typedef Graph::out_edge_iterator OutEdgeIterator;
		typedef std::pair<OutEdgeIterator, OutEdgeIterator> OutEdgeIteratorRange;

		typedef Graph::edge_iterator EdgeIterator;
		typedef std::pair<EdgeIterator, EdgeIterator> EdgeIteratorRange;

		typedef std::map<const Node *, VertexDescriptor> NodesToVertices;

		void addSiblingConstraints( VertexDescriptor vertex, const Direction &edgeDirection )
		{
			// find all the edges pointing in the specified direction.

			std::vector<EdgeDescriptor> edges;
			InEdgeIteratorRange e = in_edges( vertex, m_graph );
			for( InEdgeIterator it = e.first; it != e.second; ++it )
			{
				if( m_graph[*it].idealDirection == edgeDirection )
				{
					edges.push_back( *it );
				}
			}

			// sort edges perpendicular to edge direction

			const int dimension = edgeDirection.x ? 1 : 0;
			sort( edges.begin(), edges.end(), EdgeTargetOffsetLess( dimension, &m_graph ) );

			// make constraints among the siblings to keep them in order with
			// respect to their connection order.

			Vertex *prev = nullptr;
			for( std::vector<EdgeDescriptor>::const_iterator it = edges.begin(); it != edges.end(); ++it )
			{
				Vertex *curr = &(m_graph[source( *it, m_graph )]);
				if( prev )
				{
					const float separation = m_nodeSeparation + 0.5 * (
						fabs( prev->bound.size()[dimension] ) +
						fabs( curr->bound.size()[dimension] )
					);

					addConstraint(
						*curr,
						*prev,
						Constraint::GreaterThanOrEqualTo,
						separation,
						dimension == 0 ? V2f( 1, 0 ) : V2f( 0, 1 )
					);
				}
				prev = curr;
			}
		}

		// Adds a constraint between p and q, adjusting w based on their pinning status.
		void addConstraint( Vertex &p, Vertex &q, Constraint::Type type, float d, const V2f &v, float w = 0.5f )
		{
			if( p.pinned && q.pinned )
			{
				return;
			}

			if( p.pinned )
			{
				w = 0.0f;
			}
			else if( q.pinned )
			{
				w = 1.0f;
			}

			m_constraints.push_back(
				Constraint(
					&(p.position),
					&(q.position),
					type,
					d,
					v,
					w
				)
			);
		}

		void addCollisionConstraints()
		{
			// build a tree for making fast bound intersection queries

			vector<VertexDescriptor> vertexDescriptors;
			vector<Box2f> bounds;

			const V2f padding( m_nodeSeparation / 2.0f );

			VertexIteratorRange v = vertices( m_graph );
			for( VertexIterator it = v.first; it != v.second; ++it )
			{
				V2f nodePadding( padding );
				if( m_graph[*it].auxiliary )
				{
					nodePadding *= 0.5;
				}

				Box2f b = m_graph[*it].bound;
				b.min = b.min + m_graph[*it].position - nodePadding;
				b.max = b.max + m_graph[*it].position + nodePadding;
				bounds.push_back( b );
				vertexDescriptors.push_back( *it );
			}

			Box2fTree tree( bounds.begin(), bounds.end() );

			// find colliding bounds, and add constraints to separate them

			typedef vector<Box2f>::const_iterator BoundIterator;
			vector<BoundIterator> intersectingBounds;
			for( BoundIterator it = bounds.begin(), eIt = bounds.end(); it != eIt; ++it )
			{
				intersectingBounds.clear();
				tree.intersectingBounds( *it, intersectingBounds );
				for( vector<BoundIterator>::const_iterator bIt = intersectingBounds.begin(); bIt != intersectingBounds.end(); ++bIt )
				{
					size_t bound1Index = it - bounds.begin();
					size_t bound2Index = *bIt - bounds.begin();
					if( bound2Index <= bound1Index )
					{
						// we dealt with this collision already, when bound2Index was bound1Index
						continue;
					}

					Vertex &vertex1 = m_graph[vertexDescriptors[bound1Index]];
					Vertex &vertex2 = m_graph[vertexDescriptors[bound2Index]];

					if(
						vertex1.collisionGroup < 0 ||
						vertex2.collisionGroup < 0 ||
						vertex1.collisionGroup != vertex2.collisionGroup
					)
					{
						continue;
					}

					const Box2f &bound1 = *it;
					const Box2f &bound2 = **bIt;

					const int a = collisionSeparationAxis( vertexDescriptors[bound1Index], vertexDescriptors[bound2Index] );
					const V2f v = a == 0 ? V2f( 1, 0 ) : V2f( 0, 1 );

					float separation = 0.5 * ( bound1.size()[a] + bound2.size()[a] );
					Vertex *p = &vertex2;
					Vertex *q = &vertex1;
					if( vertex1.position[a] > vertex2.position[a] )
					{
						p = &vertex1;
						q = &vertex2;
					}

					addConstraint(
						*p,
						*q,
						Constraint::GreaterThanOrEqualTo,
						separation,
						v
					);
				}
			}
		}

		int collisionSeparationAxis( VertexDescriptor vertex1, VertexDescriptor vertex2 )
		{
			if( m_graph[vertex1].auxiliary && m_graph[vertex2].auxiliary )
			{
				return 1; // y-axis
			}

			bool foundHorizontalConnection = false;
			for( int i = 0; i < 2; ++i )
			{
				VertexDescriptor vertex = i == 0 ? vertex1 : vertex2;
				InEdgeIteratorRange inEdges = in_edges( vertex, m_graph );
				for( InEdgeIterator it = inEdges.first; it != inEdges.second; ++it )
				{
					if( m_graph[*it].targetTangent.y )
					{
						return 0;
					}
					else
					{
						foundHorizontalConnection = true;
					}
				}
				OutEdgeIteratorRange outEdges = out_edges( vertex, m_graph );
				for( OutEdgeIterator it = outEdges.first; it != outEdges.second; ++it )
				{
					if( m_graph[*it].sourceTangent.y )
					{
						return 0;
					}
					else
					{
						foundHorizontalConnection = true;
					}
				}
			}

			return foundHorizontalConnection ? 1 : 0;
		}

		void applyConstraints( size_t iterations )
		{
			for( size_t i = 0; i < iterations; ++i )
			{
				for( std::vector<Constraint>::const_iterator it = m_constraints.begin(), eIt = m_constraints.end(); it != eIt; ++it )
				{
					it->apply();
				}
			}
		}

		// Applies forces to the nodes by treating each connection as
		// a spring connecting the nodes at its ends. These aren't
		// traditional springs that apply a force down the length of
		// the spring though - those lead to messy graphs which tend
		// not to have nice horizontal and vertical directions
		// of flow, even with our directional constraints included.
		// Instead, our springs apply a force to bring the two nodes
		// into their ideal relative positions, which is defined as
		// being separated by the vector (srcTangent - dstTangent).
		// This is equivalent to applying a spring separately in the
		// x and y directions.
		void applySprings()
		{
			VertexIteratorRange v = vertices( m_graph );
			for( VertexIterator it = v.first; it != v.second; ++it )
			{
				m_graph[*it].force = V2f( 0.0f );
			}

			EdgeIteratorRange e = edges( m_graph );
			for( EdgeIterator it = e.first; it != e.second; ++it )
			{
				Vertex &src = m_graph[source( *it, m_graph )];
				Vertex &dst = m_graph[target( *it, m_graph )];
				if( src.pinned && dst.pinned )
				{
					continue;
				}

				Edge &edge = m_graph[*it];

				V2f srcPos = src.position + edge.sourceOffset;
				V2f dstPos = dst.position + edge.targetOffset;

				V2f offset = dstPos - srcPos;
				V2f desiredOffset = m_edgeLength * V2f( edge.idealDirection );

				float w = 0.5f;
				if( src.pinned )
				{
					w = 0.0f;
				}
				else if( dst.pinned )
				{
					w = 1.0f;
				}

				V2f v = desiredOffset - offset;
				src.force -= v * m_springStiffness * w;
				dst.force += v * m_springStiffness * ( 1.0f - w );
			}

			for( VertexIterator it = v.first; it != v.second; ++it )
			{
				m_graph[*it].position += m_graph[*it].force;
			}
		}

		struct EdgeTargetOffsetLess
		{
			EdgeTargetOffsetLess( int dimension, Graph *graph )
				:	m_dimension( dimension ), m_graph( graph )
			{
			}

			bool operator () ( EdgeDescriptor e1, EdgeDescriptor e2 ) const
			{
				const Edge &edge1 = (*m_graph)[e1];
				const Edge &edge2 = (*m_graph)[e2];
				return edge1.targetOffset[m_dimension] < edge2.targetOffset[m_dimension];
			}

			private :

				int m_dimension;
				Graph *m_graph;

		};

		void addAuxiliaryConnection( const Plug *srcPlug, const Plug *dstPlug )
		{
			const Node *srcNode = srcPlug->node();
			const Node *dstNode = dstPlug->node();

			NodesToVertices::const_iterator srcIt = m_nodesToVertices.find( srcNode );
			NodesToVertices::const_iterator dstIt = m_nodesToVertices.find( dstNode );

			const NodeGadget *srcNodeGadget = m_graphGadget->nodeGadget( srcNode );
			const NodeGadget *dstNodeGadget = m_graphGadget->nodeGadget( dstNode );
			const Nodule *srcNodule = srcNodeGadget->nodule( srcPlug );
			const Nodule *dstNodule = dstNodeGadget->nodule( dstPlug );

			// Determine if default should be laying out nodes side by side or stacked on top of each other.
			const V3f defaultDstTangent = m_graph[dstIt->second].auxiliary ? V3f( -1, 0, 0 ) : defaultTangent( dstNodeGadget );

			const V3f dstTangent = !dstNodule ? defaultDstTangent : dstNodeGadget->connectionTangent( dstNodule );
			V3f srcTangent = !srcNodule ? -1.0f * defaultDstTangent : srcNodeGadget->connectionTangent( srcNodule );

			// Ajust tangent if the auxiliary connection is represented by a
			// StandardConnectionGadget and has a dstNodule.
			// \todo: Inverse case needs handling once we draw those connections correctly.
			if( dstNodule && !srcNodule )
			{
				srcTangent = -1.0f * dstTangent;
			}

			Direction idealDirection = direction( srcTangent - dstTangent );

			V3f srcOffset, dstOffset;
			if( srcNodule )
			{
				srcOffset = srcNodule->transformedBound( srcNodeGadget ).center();
			}
			else
			{
				srcOffset = V3f( .5 * idealDirection.x, .5 * idealDirection.y, 0 ) * srcNodeGadget->bound().size();
			}

			if( dstNodule )
			{
				dstOffset = dstNodule->transformedBound( dstNodeGadget ).center();
			}
			else
			{
				dstOffset = V3f( -.5 * idealDirection.x, -.5 * idealDirection.y, 0 ) * dstNodeGadget->bound().size();
			}

			EdgeDescriptor e = add_edge( srcIt->second, dstIt->second, m_graph ).first;
			m_graph[e].sourceTangent = direction( srcTangent );
			m_graph[e].targetTangent = direction( dstTangent );
			m_graph[e].idealDirection = idealDirection;
			m_graph[e].sourceOffset = V2f( srcOffset.x, srcOffset.y );
			m_graph[e].targetOffset = V2f( dstOffset.x, dstOffset.y );
		}

		// Defaulting to putting auxiliary nodes to the left, unless there are nodules
		// on the left, but none on the top edge
		V3f defaultTangent( const NodeGadget *dstNodeGadget )
		{
			V3f up( 0, 1, 0 );
			V3f left( -1, 0, 0 );

			const StandardNodeGadget *standardNodeGadget = runTimeCast<const StandardNodeGadget>( dstNodeGadget );

			// For auxiliary edges we default to a horizontal tangent
			if( !standardNodeGadget )
			{
				return left;
			}

			bool leftEdgeBlocked = false;
			for( Nodule::RecursiveIterator it( dstNodeGadget ); !it.done(); ++it )
			{
				V3f noduleTangent = dstNodeGadget->connectionTangent( it->get() );

				if( noduleTangent == up )
				{
					// If the top edge is blocked by nodules, default to using the left edge for connections
					return left;
				}
				else if( noduleTangent == left && !leftEdgeBlocked )
				{
					leftEdgeBlocked = true;
				}
			}

			if( leftEdgeBlocked )
			{
				return up;
			}

			return left;
		}

		GraphGadget *m_graphGadget;
		Graph m_graph;
		NodesToVertices m_nodesToVertices;

		std::vector<Constraint> m_constraints;

		const float m_edgeLength;
		const float m_nodeSeparation;
		const float m_springStiffness;
		const int m_maxIterations;
		const int m_constraintsIterations;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// StandardGraphLayout implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( StandardGraphLayout )

StandardGraphLayout::StandardGraphLayout()
	:	m_connectionScale( 1.0f ), m_nodeSeparationScale( 1.0f )
{
}

StandardGraphLayout::~StandardGraphLayout()
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
		for( Plug::RecursiveInputIterator it( node ); !it.done(); ++it )
		{
			if( (*it)->getInput() && nodeGadget->nodule( it->get() ) )
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
	graph->setNodePosition( node, fallbackPosition );

	LayoutEngine layout( graph, m_connectionScale, m_nodeSeparationScale );

	StandardSetPtr s = new StandardSet();
	s->add( node );
	layout.pinNodes( s.get(), true /* invert */ );

	layout.assignCollisionGroup( (IECore::TypeId)Gaffer::BackdropTypeId, -1 ); // disable collisions with backdrops

	layout.addConnectionDirectionConstraints();

	layout.solve( true /* collision detection on */ );
	layout.applyPositions();
}

void StandardGraphLayout::positionNodes( GraphGadget *graph, Gaffer::Set *nodes, const Imath::V2f &fallbackPosition ) const
{
	LayoutEngine layout( graph, m_connectionScale, m_nodeSeparationScale );
	layout.pinNodes( nodes, true /* invert */ );
	layout.groupNodes( nodes, fallbackPosition );

	layout.addConnectionDirectionConstraints();

	layout.solve( false /* collision detection off */ );
	layout.applyPositions();
}

void StandardGraphLayout::layoutNodes( GraphGadget *graph, Gaffer::Set *nodes ) const
{
	LayoutEngine layout( graph, m_connectionScale, m_nodeSeparationScale );
	if( nodes )
	{
		layout.pinNodes( nodes, true /* invert */ );
	}

	// do a first round of layout without worrying about
	// collisions between nodes.

	layout.addConnectionDirectionConstraints();
	layout.addSiblingConstraints();
	layout.solve( false );

	// do a second round of layout, now resolving collisions.
	// we don't use the sibling constraints during this process
	// because multiple sets of sibling constraints can conflict
	// and produce unresolveable constraints that prevent the
	// collisions detection from working. a better alternative
	// might be to remove conflicting constraints before applying them.

	layout.clearConstraints();
	layout.addConnectionDirectionConstraints();
	layout.solve( true );

	layout.applyPositions();

	// do a third round of layout, now positioning nodes that are not represented
	// by StandardConnectionGadgets next to the affected node or in the middle of
	// multiple affected nodes (this is done for Expressions, for example).

	layout.pinNonAuxiliaryNodes( nodes );
	layout.clearConstraints();
	layout.addAuxiliaryConnections();
	layout.solve( true );

	layout.applyPositions();
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

	// If we're trying to connect a Dot, Switch, BoxOut, ContextProcessor
	// or Loop, then we may need to give it plugs first.
	/// \todo We should be able to do this by talking to PlugAdders instead of
	/// doing the work ourselves. In fact, because PlugAdders and Nodules are
	/// both derived from ConnectionCreator, we should only need to consider
	/// ConnectionCreators, and shouldn't need to know anything about what's
	/// happening behind the scenes. To make this work, I think we probably
	/// need to make a few tweaks, some of which would require a major version
	/// change :
	///
	/// - Add a `virtual bool ConnectionCreator::hasConnection()` method so
	///   that we can avoid modifying existing connections.
	/// - Have `ConnectionCreator::createConnection()` return the other endpoint
	///   of the connection.
	/// - Make the Dot node to use PlugAdders rather than its own mechanism
	///   (see PR #3059).
	if( Dot *dot = runTimeCast<Dot>( node ) )
	{
		if( !dot->inPlug() )
		{
			dot->setup( outputPlugs.front() );
		}
	}
	else if( NameSwitch *switchNode = runTimeCast<NameSwitch>( node ) )
	{
		if( !switchNode->inPlugs() )
		{
			switchNode->setup( outputPlugs.front() );
		}
	}
	else if( Switch *switchNode = runTimeCast<Switch>( node ) )
	{
		if( !switchNode->inPlugs() )
		{
			switchNode->setup( outputPlugs.front() );
		}
	}
	else if( BoxOut *boxOut = runTimeCast<BoxOut>( node ) )
	{
		if( !boxOut->plug() )
		{
			boxOut->setup( outputPlugs.front() );
		}
	}
	else if( ContextProcessor *contextProcessor = runTimeCast<ContextProcessor>( node ) )
	{
		if( !contextProcessor->inPlug() )
		{
			if( ValuePlug *valuePlug = runTimeCast<ValuePlug>( outputPlugs.front() ) )
			{
				contextProcessor->setup( valuePlug );
			}
		}
	}
	else if( Loop *loop = runTimeCast<Loop>( node ) )
	{
		if( !loop->inPlug() )
		{
			if( ValuePlug *valuePlug = runTimeCast<ValuePlug>( outputPlugs.front() ) )
			{
				loop->setup( valuePlug );
			}
		}
	}
	else if( auto editScope = runTimeCast<EditScope>( node ) )
	{
		if( !editScope->inPlug() )
		{
			editScope->setup( outputPlugs.front() );
		}
	}

	// iterate over the output plugs, connecting them in to the node if we can

	size_t numConnectionsMade = 0;
	Plug *firstConnectionSrc = nullptr, *firstConnectionDst = nullptr;
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
			// Find the destination plugs at the end of the existing
			// connections we want to insert into.
			vector<Plug *> insertionDsts;
			const Plug::OutputContainer &outputs = firstConnectionSrc->outputs();
			for( Plug::OutputContainer::const_iterator it = outputs.begin(); it != outputs.end(); ++it )
			{
				// ignore outputs that aren't visible:
				NodeGadget *nodeGadget = graph->nodeGadget( (*it)->node() );
				if( !nodeGadget || !nodeGadget->nodule( *it ) )
				{
					continue;
				}
				// Ignore the output which we made when connecting the node above
				if( *it == firstConnectionDst )
				{
					continue;
				}
				if( (*it)->acceptsInput( correspondingOutput ) )
				{
					// Insertion accepted - store for reconnection
					insertionDsts.push_back( *it );
				}
				else
				{
					// Insertion rejected - clear insertionDsts to
					// abort insertion entirely.
					insertionDsts.clear();
					break;
				}
			}
			// Reconnect the destination plugs such that we've inserted our node
			for( vector<Plug *>::const_iterator it = insertionDsts.begin(), eIt = insertionDsts.end(); it != eIt; ++it )
			{
				(*it)->setInput( correspondingOutput );
			}
		}
	}

	return numConnectionsMade;
}

size_t StandardGraphLayout::outputPlugs( NodeGadget *nodeGadget, std::vector<Gaffer::Plug *> &plugs ) const
{
	for( Plug::RecursiveOutputIterator it( nodeGadget->node() ); !it.done(); it++ )
	{
		if( auto nodule = nodeGadget->nodule( it->get() ) )
		{
			if( !runTimeCast<CompoundNodule>( nodule ) )
			{
				plugs.push_back( it->get() );
			}
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
	for( Plug::RecursiveInputIterator it( nodeGadget->node() ); !it.done(); it++ )
	{
		if( (*it)->getInput() == nullptr and nodeGadget->nodule( it->get() ) )
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
		return nullptr;
	}

	for( Plug::RecursiveOutputIterator it( dependencyNode ); !it.done(); ++it )
	{
		if( dependencyNode->correspondingInput( it->get() ) == input )
		{
			return it->get();
		}
	}

	return nullptr;
}

void StandardGraphLayout::setConnectionScale( float scale )
{
	m_connectionScale = scale;
}

float StandardGraphLayout::getConnectionScale() const
{
	return m_connectionScale;
}

void StandardGraphLayout::setNodeSeparationScale( float scale )
{
	m_nodeSeparationScale = scale;
}

float StandardGraphLayout::getNodeSeparationScale() const
{
	return m_nodeSeparationScale;
}
