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

#ifndef GAFFER_STANDARDSET_H
#define GAFFER_STANDARDSET_H

#include "Gaffer/Set.h"

#include "boost/multi_index_container.hpp"
#include "boost/multi_index/random_access_index.hpp"
#include "boost/multi_index/ordered_index.hpp"

namespace Gaffer
{

namespace Detail
{

struct MemberAcceptanceCombiner
{
	typedef bool result_type;
	
	template<typename InputIterator>
	bool operator()( InputIterator first, InputIterator last ) const
	{
		if( first==last )
		{
			return true;
		}
		while( first!=last )
		{
			if( !(*first) )
			{
				return false;
			}
			++first;
		}
		return true;
	}
};

} // namespace Detail

/// The StandardSet provides a Set implementation where membership is explicitly set using add() and remove()
/// methods. Membership may be restricted using the memberAcceptanceSignal().
class StandardSet : public Gaffer::Set
{

	public :

		StandardSet();
		virtual ~StandardSet();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::StandardSet, StandardSetTypeId, Gaffer::Set );
		
		typedef boost::signal<bool ( const StandardSet *, const Member * ), Detail::MemberAcceptanceCombiner> MemberAcceptanceSignal;
		/// This signal is emitted to determine whether or not a member is eligible
		/// to be in the StandardSet. Members are only added if all slots of the signal
		/// return true, or if no slots have been connected - otherwise an exception is thrown.
		/// You may call the signal yourself at any time to determine if a member is eligible.
		MemberAcceptanceSignal &memberAcceptanceSignal();
		/// A function suitable for use as a memberAcceptanceSignal slot. This rejects all
		/// members not derived from T.
		template<typename T>
		static bool typedMemberAcceptor( const StandardSet *set, const Member *potentialMember );

		/// @name Membership specification
		/// These methods are used to explicitly add and remove members.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Adds a member to the set. Returns true if the member
		/// was not already present and passes the acceptance tests,
		/// and false otherwise.
		bool add( MemberPtr member );
		/// Adds all the objects in the specified range into this set, returning
		/// the number of new members added.
		template<typename I>
		size_t add( I first, I last );
		/// Adds all the objects in the other set into this set, returning
		/// the number of new members added.
		size_t add( const Set *other );
		/// Removes a member from the set. Returns true if the member
		/// is removed and false if it wasn't there in the first place.
		bool remove( Member *member );
		/// Removes all the in the specified range from this set, returning the
		/// number of members removed.
		template<typename I>
		size_t remove( I first, I last );
		/// Removes all the objects in the other set from this set, returning
		/// the number of members removed.
		size_t remove( const Set *other );
		/// Removes all members from the set.
		void clear();
		//@}
		
		/// @name Implementation of the Set interface
		////////////////////////////////////////////////////////////////////
		//@{
		virtual bool contains( const Member *object ) const;
		virtual Member *member( size_t index );
		virtual const Member *member( size_t index ) const;
		virtual size_t size() const;
		//@}

	private :

		MemberAcceptanceSignal m_memberAcceptanceSignal;

		typedef boost::multi_index::multi_index_container<
			MemberPtr,
			boost::multi_index::indexed_by<
				boost::multi_index::ordered_unique<boost::multi_index::identity<MemberPtr> >,
				boost::multi_index::random_access<>
			>
		> MemberContainer;

		typedef const MemberContainer::nth_index<0>::type OrderedIndex;
		typedef const MemberContainer::nth_index<1>::type SequencedIndex;		
		
		MemberContainer m_members;
		
};

IE_CORE_DECLAREPTR( StandardSet );
	
} // namespace Gaffer

#include "Gaffer/StandardSet.inl"

#endif // GAFFER_STANDARDSET_H
