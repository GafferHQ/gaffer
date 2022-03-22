//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_SET_H
#define GAFFER_SET_H

#include "Gaffer/Export.h"
#include "Gaffer/Node.h"

#include "IECore/RunTimeTyped.h"

#include "boost/iterator/iterator_facade.hpp"

namespace Gaffer
{

template<typename ContainerType, typename ValueType>
class SetIterator;

/// Set provides an abstract base class for an arbitrary collection
/// of IECore::RunTimeTyped objects.
class GAFFER_API Set : public IECore::RunTimeTyped, public Signals::Trackable
{

	public :

		Set();
		~Set() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Set, SetTypeId, IECore::RunTimeTyped );

		using Member = IECore::RunTimeTyped;
		using MemberPtr = Member::Ptr;
		using ConstMemberPtr = Member::ConstPtr;

		/// Returns the number of members of the set.
		virtual size_t size() const = 0;
		/// Returns the indexth member of the set.
		virtual Member *member( size_t index ) = 0;
		/// Returns the indexth member of the set.
		virtual const Member *member( size_t index ) const = 0;
		/// Returns true if the object is a member of the set.
		virtual bool contains( const Member *object ) const = 0;

		using MemberSignal = Signals::Signal<void ( Set *, Member * ), Signals::CatchingCombiner<void>>;

		/// A signal emitted when a new member is added to the Set. It is
		/// the responsibility of derived classes to emit this when appropriate.
		MemberSignal &memberAddedSignal();
		/// A signal emitted when a member is removed from the Set. It is
		/// the responsibility of derived classes to emit this when appropriate.
		MemberSignal &memberRemovedSignal();

		using Iterator = SetIterator<Set, Member>;
		using ConstIterator = SetIterator<Set const, Member const>;

		Iterator begin();
		ConstIterator begin() const;
		Iterator end();
		ConstIterator end() const;

	private :

		MemberSignal m_memberAddedSignal;
		MemberSignal m_memberRemovedSignal;

};

IE_CORE_DECLAREPTR( Set );

template<typename ContainerType, typename ValueType>
class SetIterator : public boost::iterator_facade<SetIterator<ContainerType, ValueType>, ValueType, boost::random_access_traversal_tag, ValueType&, int64_t>
{

	public :
		SetIterator( ContainerType* set )
			:	SetIterator( set, 0 )
		{
		}

		SetIterator( ContainerType* set, size_t index )
			:	m_set( set ), m_index( index )
		{
		}

	private :

		friend class boost::iterator_core_access;

		void increment()
		{
			++m_index;
		}

		void decrement()
		{
			--m_index;
		}

		void advance( int64_t n )
		{
			m_index += n;
		}

		int64_t distance_to( SetIterator const &other ) const
		{
			return int64_t( m_index ) - int64_t( other.m_index );
		}

		bool equal( SetIterator const &other ) const
		{
			return m_index == other.m_index;
		}

		ValueType& dereference() const
		{
			return *(m_set->member( m_index ));
		}

		ContainerType* const m_set;
		size_t m_index;
};

} // namespace Gaffer

#endif // GAFFER_SET_H
