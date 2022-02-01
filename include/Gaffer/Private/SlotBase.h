//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFER_SLOTBASE_H
#define GAFFER_SLOTBASE_H

#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "boost/intrusive_ptr.hpp"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/noncopyable.hpp"

#include <atomic>
#include <cassert>

namespace Gaffer::Signals::Private
{

// SlotBase forms the core of the Gaffer::Signals system, providing a data
// structure designed for the storage of the slots connected to a signal. It is
// designed to meet several requirements :
//
// - Constant time insertion and removal of slots.
// - Shared ownership, so Connection can be used to track slots independently of
//   the Signal, and connections can continue to exist beyond the lifetime of
//   the signal and vice-versa.
// - Robustness to interesting situations such as self-disconnecting slots and
//   slots that cause the signal itself to be deleted.
// - Minimal storage requirements among the various Signals components.
//
// To meet these requirements, SlotBase objects are reference counted and form a
// doubly linked list with a few specific features :
//
// - The next slot is referenced by `intrusive_ptr`. This allows Signal to
//   maintain the lifetime of the slots purely by holding a single pointer to
//   the first slot, and also allows Connection to share ownership via it's own
//   `intrusive_ptr`.
// - The `previous` field doesn't point to the previous _slot_, but instead to
//   its `SlotBase::next` field. This allows the first slot to point back
//   directly to `Signal::m_firstSlot`, meaning we can remove a slot from the
//   list without needing access to a Signal object.
// - Disconnected slots keep a valid `next` pointer, so that SlotCallIterator
//   can continue iteration even if a slot disconnects itself when called.
//
struct SlotBase : private boost::noncopyable
{

	using Ptr = boost::intrusive_ptr<SlotBase>;

	// Inserts slot after `previous`.
	SlotBase( Ptr &prev )
		:	previous( &prev ), next( prev ), m_referenceCount( 0 ), blocked( false ), calling( false )
	{
		*previous = this;
		if( next )
		{
			next->previous = &next;
		}
	}

	virtual ~SlotBase()
	{
		assert( m_referenceCount.load() == 0 );
	}

	// Removes slot from list. Virtual so that Signal::Slot
	// can also destroy its slot functor.
	virtual void disconnect()
	{
		if( !previous )
		{
			// Already disconnected
			return;
		}

		if( next )
		{
			next->previous = previous;
		}
		Ptr &previousRef = *previous;
		assert( previousRef == this );
		previous = nullptr;
		// This assignment last, since it could drop
		// our reference count to 0 and destroy us.
		previousRef = next;
		// Note : We have deliberately kept our pointer to `next`, so that we
		// don't invalidate the SlotCallIterator when a slot disconnects itself
		// from within a call. We're not reachable from the head of the list,
		// but the end of the list is still reachable from us.
	}

	// Non-null when connected to signal (reachable from `Signal::m_firstSlot`).
	Ptr *previous;
	Ptr next;

	// Reference count. We don't derive from IECore::RefCounted or
	// `boost::intrusive_ref_counter` for two reasons :
	//
	// - We don't need a 64 bit count, and using a smaller type stored _after_
	//   our pointer fields lets us minimise `sizeof( SlotBase )`.
	// - We don't want an atomic reference count, because signals are not
	//   intended to be threadsafe and a non-atomic count yields significantly
	//   improved performance, particularly in
	//   `SignalsTest.testCallPerformance()`.
	//
	// > Note : We currently _do_ use an atomic count so we can support legacy
	// > code which unthinkingly performed concurrent emission of a signal from
	// > multiple threads. See comments in MetadataTest.cpp and documentation
	// > for `Node::errorSignal()`.
	std::atomic_uint32_t m_referenceCount;
	bool blocked;
	// True when currently in `Slot::operator()`. Used to defer destruction
	// of self-disconnecting functions.
	bool calling;

};

inline void intrusive_ptr_add_ref( SlotBase *r )
{
	r->m_referenceCount.fetch_add( 1, std::memory_order_relaxed );
}

inline void intrusive_ptr_release( SlotBase *r )
{
	if( r->m_referenceCount.fetch_sub( 1, std::memory_order_acq_rel ) == 1 )
	{
		delete r;
	}
}

} // namespace Gaffer::Signals::Private

#endif // GAFFER_SLOTBASE_H
