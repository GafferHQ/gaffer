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

#ifndef GAFFER_RECURSIVECHILDITERATOR_H
#define GAFFER_RECURSIVECHILDITERATOR_H

#include "Gaffer/GraphComponent.h"

#include "boost/container/small_vector.hpp"
#include "boost/iterator/iterator_facade.hpp"

namespace Gaffer
{

/// RecursiveChildIterator provides a depth-first traversal over all the children of
/// a GraphComponent. Use as follows :
///
/// for( RecursiveChildIterator it( parent ); !it.done(); ++it )
/// ...
class RecursiveChildIterator : public boost::iterator_facade<RecursiveChildIterator, const GraphComponentPtr, boost::forward_traversal_tag>
{

	public :

		RecursiveChildIterator()
			:	m_pruned( false )
		{
		}

		RecursiveChildIterator( const GraphComponent *parent )
			:	m_pruned( false )
		{
			m_stack.push_back(
				Level(
					parent->children(),
					parent->children().begin()
				)
			);
		}

		RecursiveChildIterator( const GraphComponent *parent, const GraphComponent::ChildIterator &it )
			:	m_pruned( false )
		{
			m_stack.push_back(
				Level(
					parent->children(),
					it
				)
			);
		}

		size_t depth() const
		{
			return m_stack.size() - 1;
		}

		/// Calling prune() causes the next increment to skip any recursion
		/// that it would normally perform.
		void prune()
		{
			m_pruned = true;
		}

		bool done() const
		{
			return m_stack.size() == 1 && m_stack[0].it == m_stack[0].end;
		}

	private :

		friend class boost::iterator_core_access;

		struct Level
		{
			Level( const GraphComponent::ChildContainer &container, GraphComponent::ChildIterator i )
				:	begin( container.begin() ), end( container.end() ), it( i )
			{
			}

			bool operator == ( const Level &other ) const
			{
				return begin == other.begin && end == other.end && it == other.it;
			}

			GraphComponent::ChildIterator begin;
			GraphComponent::ChildIterator end;
			GraphComponent::ChildIterator it;
		};

		using Levels = boost::container::small_vector<Level, 4>;
		Levels m_stack;
		bool m_pruned;

		void increment()
		{
			const GraphComponent *currentGraphComponent = stackTop().it->get();
			if( !m_pruned && currentGraphComponent->children().size() )
			{
				m_stack.push_back(
					Level(
						currentGraphComponent->children(),
						currentGraphComponent->children().begin()
					)
				);
			}
			else
			{
				++(stackTop().it);
				while( m_stack.size() > 1 && stackTop().it == stackTop().end )
				{
					m_stack.pop_back();
					++(stackTop().it);
				}
			}
			m_pruned = false;
		}

		bool equal( const RecursiveChildIterator &other ) const
		{
			return m_stack == other.m_stack;
		}

		const GraphComponentPtr &dereference() const
		{
			return *(stackTop().it);
		}

		Level &stackTop()
		{
			return *(m_stack.rbegin());
		}

		const Level &stackTop() const
		{
			return *(m_stack.rbegin());
		}

};

} // namespace Gaffer

#endif // GAFFER_RECURSIVECHILDITERATOR_H
