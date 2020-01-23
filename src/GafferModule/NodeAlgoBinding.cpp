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

#include "boost/python.hpp"

#include "NodeAlgoBinding.h"

#include "Gaffer/NodeAlgo.h"

using namespace boost::python;
using namespace Gaffer;

namespace
{

struct PythonVisitor
{

	PythonVisitor( object visitor )
		:	m_visitor( visitor )
	{
	}

	bool operator()( Node *node ) const
	{
		object r = m_visitor( NodePtr( node ) );
		extract<bool> boolExtractor( r );
		if( r == object() || !boolExtractor.check() )
		{
			throw IECore::Exception(
				"Visitor must return a bool (True to continue, False to prune)"
			);
		}
		return boolExtractor;
	}

	private :

		object m_visitor;

};

void visitUpstreamWrapper( Node &node, object visitor, NodeAlgo::VisitOrder order )
{
	NodeAlgo::visitUpstream( &node, PythonVisitor( visitor ), order );
}

void visitDownstreamWrapper( Node &node, object visitor, NodeAlgo::VisitOrder order )
{
	NodeAlgo::visitDownstream( &node, PythonVisitor( visitor ), order );
}

void visitConnectedWrapper( Node &node, object visitor, NodeAlgo::VisitOrder order )
{
	NodeAlgo::visitConnected( &node, PythonVisitor( visitor ), order );
}

struct PythonPredicate
{

	PythonPredicate( object predicate )
		:	m_predicate( predicate )
	{
	}

	bool operator()( const Node *node ) const
	{
		object r = m_predicate( NodePtr( const_cast<Node *>( node ) ) );
		return extract<bool>( r );
	}

	private :

		object m_predicate;

};

NodePtr findUpstreamWrapper( Node &node, object predicate, NodeAlgo::VisitOrder order )
{
	return NodeAlgo::findUpstream( &node, PythonPredicate( predicate ), order );
}

NodePtr findDownstreamWrapper( Node &node, object predicate, NodeAlgo::VisitOrder order )
{
	return NodeAlgo::findDownstream( &node, PythonPredicate( predicate ), order );
}

NodePtr findConnectedWrapper( Node &node, object predicate, NodeAlgo::VisitOrder order )
{
	return NodeAlgo::findConnected( &node, PythonPredicate( predicate ), order );
}

list nodeList( const std::vector<Node *> v )
{
	list result;
	for( auto n : v )
	{
		result.append( NodePtr( n ) );
	}
	return result;
}

list findAllUpstreamWrapper( Node &node, object predicate, NodeAlgo::VisitOrder order )
{
	auto v = NodeAlgo::findAllUpstream( &node, PythonPredicate( predicate ), order );
	return nodeList( v );
}

list findAllDownstreamWrapper( Node &node, object predicate, NodeAlgo::VisitOrder order )
{
	auto v = NodeAlgo::findAllDownstream( &node, PythonPredicate( predicate ), order );
	return nodeList( v );
}

list findAllConnectedWrapper( Node &node, object predicate, NodeAlgo::VisitOrder order )
{
	auto v = NodeAlgo::findAllConnected( &node, PythonPredicate( predicate ), order );
	return nodeList( v );
}

// Rather than wrap `upstreamNodes<T>()` etc, we reimplement them to
// take a TypeId rather than template argument to specify the type.
struct FindByTypeVisitor
{
	FindByTypeVisitor( IECore::TypeId type )
		:	m_type( type )
	{
	}

	bool operator()( Node *node )
	{
		if( node->isInstanceOf( m_type ) )
		{
			result.append( NodePtr( node ) );
		}
		return true;
	}

	list result;

	private :

		const IECore::TypeId m_type;
};

list upstreamNodes( Node &node, IECore::TypeId type, NodeAlgo::VisitOrder order )
{
	FindByTypeVisitor finder( type );
	NodeAlgo::visitUpstream( &node, finder, order );
	return finder.result;
}

list downstreamNodes( Node &node, IECore::TypeId type, NodeAlgo::VisitOrder order )
{
	FindByTypeVisitor finder( type );
	NodeAlgo::visitDownstream( &node, finder, order );
	return finder.result;
}

list connectedNodes( Node &node, IECore::TypeId type, NodeAlgo::VisitOrder order )
{
	FindByTypeVisitor finder( type );
	NodeAlgo::visitConnected( &node, finder, order );
	return finder.result;
}

} // namespace

void GafferModule::bindNodeAlgo()
{

	// Binding into _NodeAlgo so contents can be merged with Gaffer/NodeAlgo.py.
	object module( borrowed( PyImport_AddModule( "Gaffer._NodeAlgo" ) ) );
	scope().attr( "_NodeAlgo" ) = module;
	scope moduleScope( module );

	enum_<NodeAlgo::VisitOrder>( "VisitOrder" )
		.value( "DepthFirst", NodeAlgo::VisitOrder::DepthFirst )
		.value( "BreadthFirst", NodeAlgo::VisitOrder::BreadthFirst )
	;

	def( "visitUpstream", &visitUpstreamWrapper, ( arg( "node" ), arg( "visitor" ), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );
	def( "visitDownstream", &visitDownstreamWrapper, ( arg( "node" ), arg( "visitor" ), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );
	def( "visitConnected", &visitConnectedWrapper, ( arg( "node" ), arg( "visitor" ), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );

	def( "findUpstream", &findUpstreamWrapper, ( arg( "node" ), arg( "predicate" ), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );
	def( "findDownstream", &findDownstreamWrapper, ( arg( "node" ), arg( "predicate" ), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );
	def( "findConnected", &findConnectedWrapper, ( arg( "node" ), arg( "predicate" ), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );

	def( "findAllUpstream", &findAllUpstreamWrapper, ( arg( "node" ), arg( "predicate" ), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );
	def( "findAllDownstream", &findAllDownstreamWrapper, ( arg( "node" ), arg( "predicate" ), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );
	def( "findAllConnected", &findAllConnectedWrapper, ( arg( "node" ), arg( "predicate" ), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );

	def( "upstreamNodes", &upstreamNodes, ( arg( "node" ), arg( "type" ) = Node::staticTypeId(), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );
	def( "downstreamNodes", &downstreamNodes, ( arg( "node" ), arg( "type" ) = Node::staticTypeId(), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );
	def( "connectedNodes", &connectedNodes, ( arg( "node" ), arg( "type" ) = Node::staticTypeId(), arg( "order" ) = NodeAlgo::VisitOrder::BreadthFirst ) );

}
