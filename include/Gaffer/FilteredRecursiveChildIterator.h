//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_FILTEREDRECURSIVECHILDITERATOR_H
#define GAFFER_FILTEREDRECURSIVECHILDITERATOR_H

#include "Gaffer/RecursiveChildIterator.h"

#include "boost/iterator/iterator_adaptor.hpp"

namespace Gaffer
{

template<typename Predicate, typename RecursionPredicate=TypePredicate<GraphComponent> >
class FilteredRecursiveChildIterator : public boost::iterator_adaptor<FilteredRecursiveChildIterator<Predicate, RecursionPredicate>, RecursiveChildIterator, const typename Predicate::ChildType::Ptr>
{

	public :

		using ChildType = typename Predicate::ChildType;
		using BaseIterator = boost::iterator_adaptor<FilteredRecursiveChildIterator<Predicate, RecursionPredicate>, RecursiveChildIterator, const typename Predicate::ChildType::Ptr>;

		FilteredRecursiveChildIterator()
			:	BaseIterator(),
				m_predicate( Predicate() ),
				m_recursionPredicate( RecursionPredicate() ),
				m_end( RecursiveChildIterator() )
		{
		}

		FilteredRecursiveChildIterator( const GraphComponent *parent )
			:	BaseIterator(
					RecursiveChildIterator( parent )
				),
				m_predicate( Predicate() ),
				m_recursionPredicate( RecursionPredicate() ),
				m_end( RecursiveChildIterator( parent, parent->children().end() ) )
		{
			satisfyPredicate();
		}

		FilteredRecursiveChildIterator( const GraphComponent *parent, const GraphComponent::ChildIterator &it )
			:	BaseIterator(
					RecursiveChildIterator( parent, it )
				),
				m_predicate( Predicate() ),
				m_recursionPredicate( RecursionPredicate() ),
				m_end( RecursiveChildIterator( parent, parent->children().end() ) )
		{
			satisfyPredicate();
		}

		/// Calling prune() causes the next increment to skip any recursion
		/// that it would normally perform.
		void prune()
		{
			const_cast<RecursiveChildIterator &>( BaseIterator::base() ).prune();
		}

		bool done() const
		{
			return BaseIterator::base().done();
		}

	private :

		friend class boost::iterator_core_access;

		typename BaseIterator::reference dereference() const
		{
			// cast should be safe as predicate has checked type, and the layout of
			// a GraphComponentPtr and any other intrusive pointer should be the same.
			return reinterpret_cast<typename BaseIterator::reference>( *BaseIterator::base() );
		}

		void increment()
		{
			if( !m_recursionPredicate( *BaseIterator::base() ) )
			{
				prune();
			}
			++( BaseIterator::base_reference() );
			satisfyPredicate();
		}

		void satisfyPredicate()
		{
			while( BaseIterator::base() != m_end && !m_predicate( *BaseIterator::base() ) )
			{
				if( !m_recursionPredicate( *BaseIterator::base() ) )
				{
					prune();
				}
				++( BaseIterator::base_reference() );
			}
		}

		Predicate m_predicate;
		RecursionPredicate m_recursionPredicate;
		RecursiveChildIterator m_end;

};

template<typename Predicate, typename RecursionPredicate=TypePredicate<GraphComponent>>
class FilteredRecursiveChildRange
{

	public :

		FilteredRecursiveChildRange( const GraphComponent &parent )
			:	m_parent( parent )
		{
		}

		using Iterator = FilteredRecursiveChildIterator<Predicate, RecursionPredicate>;

		Iterator begin() const
		{
			return Iterator( &m_parent, m_parent.children().begin() );
		}

		Iterator end() const
		{
			return Iterator( &m_parent, m_parent.children().end() );
		}

	private :

		const GraphComponent &m_parent;

};

} // namespace Gaffer

#endif // GAFFER_FILTEREDRECURSIVECHILDITERATOR_H
