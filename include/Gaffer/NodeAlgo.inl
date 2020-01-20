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

#ifndef GAFFER_NODEALGO_INL
#define GAFFER_NODEALGO_INL

#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"

#include "boost/unordered_set.hpp"

#include <deque>

namespace Gaffer
{

namespace NodeAlgo
{

// Internal implementation
// =======================

namespace Private
{

using NodeSet = boost::unordered_set<NodePtr>;

template<typename Visitor>
void visitBreadthFirst( Node *node, Visitor &visitor, Plug::Direction plugDirection )
{
	Private::NodeSet visited;
	std::deque<NodePtr> toVisit;
	toVisit.push_back( node );

	while( !toVisit.empty() )
	{
		NodePtr n;
		n = toVisit.front(); toVisit.pop_front();
		if( !visited.insert( n ).second )
		{
			continue;
		}

		if( n != node )
		{
			if( !visitor( n.get() ) )
			{
				continue;
			}
		}

		if( plugDirection != Plug::Out )
		{
			for( auto plug : Plug::RecursiveInputRange( *n ) )
			{
				if( auto input = plug->getInput() )
				{
					if( auto n = input->node() )
					{
						toVisit.push_back( n );
					}
				}
			}
		}

		if( plugDirection != Plug::In )
		{
			for( auto plug : Plug::RecursiveOutputRange( *n ) )
			{
				for( auto output : plug->outputs() )
				{
					if( auto n = output->node() )
					{
						toVisit.push_back( n );
					}
				}
			}
		}
	}
}

template<typename Visitor>
void visitDepthFirst( Node *node, Visitor &visitor, Plug::Direction plugDirection, NodeSet &visited, size_t depth = 0 )
{
	if( !visited.insert( node ).second )
	{
		return;
	}

	if( depth != 0 )
	{
		if( !visitor( node ) )
		{
			return;
		}
	}

	if( plugDirection != Plug::Out )
	{
		for( auto plug : Plug::RecursiveInputRange( *node ) )
		{
			if( auto input = plug->getInput() )
			{
				if( auto n = input->node() )
				{
					visitDepthFirst( n, visitor, plugDirection, visited, depth + 1 );
				}
			}
		}
	}

	if( plugDirection != Plug::In )
	{
		for( auto plug : Plug::RecursiveOutputRange( *node ) )
		{
			for( auto output : plug->outputs() )
			{
				if( auto n = output->node() )
				{
					visitDepthFirst( n, visitor, plugDirection, visited, depth + 1 );
				}
			}
		}
	}
}

template<typename Predicate>
struct FindVisitor
{

	FindVisitor( Predicate &predicate )
		:	m_predicate( predicate )
	{
	}

	bool operator()( Node *node )
	{
		if( result )
		{
			return false;
		}

		if( m_predicate( const_cast<const Node *>( node ) ) )
		{
			result = node;
			return false;
		}
		else
		{
			return true;
		}
	}

	Node *result = nullptr;

	private :

		Predicate &m_predicate;

};

template<typename Predicate>
struct FindAllVisitor
{

	FindAllVisitor( Predicate &predicate )
		:	m_predicate( predicate )
	{
	}

	bool operator()( Node *node )
	{
		if( m_predicate( const_cast<const Node *>( node ) ) )
		{
			result.push_back( node );
		}
		return true;
	}

	std::vector<Node *> result;

	private :

		Predicate &m_predicate;

};

template<typename T>
struct FindByTypeVisitor
{

	bool operator()( Node *node )
	{
		if( auto n = IECore::runTimeCast<T>( node ) )
		{
			result.push_back( n );
		}
		return true;
	}

	std::vector<T *> result;

};

} // namespace Private

// Visit
// =====

template<typename Visitor>
void visitUpstream( Node *node, Visitor &&visitor, VisitOrder order )
{
	if( order == VisitOrder::BreadthFirst )
	{
		Private::visitBreadthFirst( node, visitor, Plug::In );
	}
	else
	{
		Private::NodeSet visited;
		Private::visitDepthFirst( node, visitor, Plug::In, visited );
	}
}

template<typename Visitor>
void visitDownstream( Node *node, Visitor &&visitor, VisitOrder order )
{
	if( order == VisitOrder::BreadthFirst )
	{
		Private::visitBreadthFirst( node, visitor, Plug::Out );
	}
	else
	{
		Private::NodeSet visited;
		Private::visitDepthFirst( node, visitor, Plug::Out, visited );
	}
}

template<typename Visitor>
void visitConnected( Node *node, Visitor &&visitor, VisitOrder order )
{
	if( order == VisitOrder::BreadthFirst )
	{
		Private::visitBreadthFirst( node, visitor, Plug::Invalid );
	}
	else
	{
		Private::NodeSet visited;
		Private::visitDepthFirst( node, visitor, Plug::Invalid, visited );
	}
}

// Find
// =====

template<typename Predicate>
Node *findUpstream( Node *node, Predicate &&predicate, VisitOrder order )
{
	Private::FindVisitor<Predicate> finder( predicate );
	visitUpstream( node, finder, order );
	return finder.result;
}

template<typename Predicate>
Node *findDownstream( Node *node, Predicate &&predicate, VisitOrder order )
{
	Private::FindVisitor<Predicate> finder( predicate );
	visitDownstream( node, finder, order );
	return finder.result;
}

template<typename Predicate>
Node *findConnected( Node *node, Predicate &&predicate, VisitOrder order )
{
	Private::FindVisitor<Predicate> finder( predicate );
	visitConnected( node, finder, order );
	return finder.result;
}

// Find All
// ========

template<typename Predicate>
std::vector<Node *> findAllUpstream( Node *node, Predicate &&predicate, VisitOrder order )
{
	Private::FindAllVisitor<Predicate> finder( predicate );
	visitUpstream( node, finder, order );
	return finder.result;
}

template<typename Predicate>
std::vector<Node *> findAllDownstream( Node *node, Predicate &&predicate, VisitOrder order )
{
	Private::FindAllVisitor<Predicate> finder( predicate );
	visitDownstream( node, finder, order );
	return finder.result;
}

template<typename Predicate>
std::vector<Node *> findAllConnected( Node *node, Predicate &&predicate, VisitOrder order )
{
	Private::FindAllVisitor<Predicate> finder( predicate );
	visitConnected( node, finder, order );
	return finder.result;
}

// Find By Type
// ============

template<typename T>
std::vector<T *> upstreamNodes( Node *node, VisitOrder order )
{
	Private::FindByTypeVisitor<T> finder;
	visitUpstream( node, finder, order );
	return finder.result;
}

template<typename T>
std::vector<T *> downstreamNodes( Node *node, VisitOrder order )
{
	Private::FindByTypeVisitor<T> finder;
	visitDownstream( node, finder, order );
	return finder.result;
}

template<typename T>
std::vector<T *> connectedNodes( Node *node, VisitOrder order )
{
	Private::FindByTypeVisitor<T> finder;
	visitConnected( node, finder, order );
	return finder.result;
}

} // namespace NodeAlgo

} // namespace Gaffer

#endif // GAFFER_NODEALGO_INL
