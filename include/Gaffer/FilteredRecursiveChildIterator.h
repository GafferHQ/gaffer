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

#include "boost/iterator/filter_iterator.hpp"

#include "Gaffer/RecursiveChildIterator.h"

namespace Gaffer
{

template<typename Predicate>
class FilteredRecursiveChildIterator : public boost::filter_iterator<Predicate, RecursiveChildIterator>
{

	public :

		typedef typename Predicate::ChildType ChildType;
		typedef boost::filter_iterator<Predicate, RecursiveChildIterator> BaseIterator;

		typedef const typename ChildType::Ptr &reference;
		typedef const typename ChildType::Ptr *pointer;

		FilteredRecursiveChildIterator()
			:	BaseIterator()
		{
		}

		FilteredRecursiveChildIterator( const GraphComponent *parent )
			:	BaseIterator(
					RecursiveChildIterator( parent ),
					RecursiveChildIterator( parent, parent->children().end() )
				)
		{
		}

		FilteredRecursiveChildIterator( const GraphComponent *parent, const GraphComponent::ChildIterator &it )
			:	BaseIterator(
					RecursiveChildIterator( parent, it ),
					RecursiveChildIterator( parent, parent->children().end() )
				)
		{
		}

		bool operator==( const RecursiveChildIterator &rhs ) const
		{
			return BaseIterator::base()==( rhs );
		}

		bool operator!=( const RecursiveChildIterator &rhs ) const
		{
			return BaseIterator::base()!=( rhs );
		}

		reference operator*() const
		{
			// cast should be safe as predicate has checked type, and the layout of
			// a GraphComponentPtr and any other intrusive pointer should be the same.
			return reinterpret_cast<reference>( BaseIterator::operator*() );
		}

		pointer operator->() const
		{
			return reinterpret_cast<pointer>( BaseIterator::operator->() );
		}

		FilteredRecursiveChildIterator &operator++()
		{
			BaseIterator::operator++();
			return *this;
		}

		FilteredRecursiveChildIterator operator++( int )
		{
			FilteredRecursiveChildIterator r( *this );
			BaseIterator::operator++();
			return r;
		}
		
		/// Calling prune() causes the next increment to skip any recursion
		/// that it would normally perform.
		void prune()
		{
			const_cast<RecursiveChildIterator &>( BaseIterator::base() ).prune();
		}
		
};

} // namespace Gaffer

#endif // GAFFER_FILTEREDRECURSIVECHILDITERATOR_H
