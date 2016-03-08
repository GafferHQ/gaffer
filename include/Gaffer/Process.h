//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_PROCESS_H
#define GAFFER_PROCESS_H

#include "tbb/enumerable_thread_specific.h"

#include "boost/noncopyable.hpp"

#include "IECore/InternedString.h"

namespace Gaffer
{

class Plug;
class Monitor;

/// Base class representing a node graph process being
/// performed on behalf of a plug. Processes are never
/// created directly by client code, but are generated
/// internally in response to calls such as
/// ValuePlug::getValue(). Typically processes can be
/// considered to be entirely an internal implementation
/// detail - they are exposed publicly only so they can
/// be used by the Monitor classes.
class Process : public boost::noncopyable
{

	public :

		/// The type of process being performed.
		const IECore::InternedString type() const { return m_type; }
		/// The plug for which the process is being
		/// performed.
		const Plug *plug() const { return m_plug; }

		/// Returns the parent process for this process - that
		/// is, the process that invoked this one.
		/// \todo Currently this does not track parent/child
		/// relationships correctly when a parent process spawns
		/// child processes on separate threads.
		const Process *parent() const { return m_parent; }

		/// Returns the Process currently being performed on
		/// this thread, or NULL if there is no such process.
		static const Process *current();

	protected :

		/// Protected constructor for use by derived classes only.
		Process( const IECore::InternedString &type, const Plug *plug, const Plug *downstream = NULL );
		~Process();

		/// Derived classes should catch exceptions thrown
		/// during processing, and call this method. It will
		/// report the error appropriately via Node::errorSignal()
		/// and rethrow the exception for propagation back to
		/// the original caller.
		/// \todo Consider ways of dealing with this automatically - could
		/// we use C++11's current_exception() in our destructor perhaps?
		void handleException();

	private :

		// Friendship allows monitors to register and deregister
		// themselves.
		friend class Monitor;
		static void registerMonitor( Monitor *monitor );
		static void deregisterMonitor( Monitor *monitor );
		static bool monitorRegistered( const Monitor *monitor );

		void emitError( const std::string &error ) const;

		struct ThreadData;

		IECore::InternedString m_type;
		const Plug *m_plug;
		const Plug *m_downstream;
		const Process *m_parent;
		ThreadData *m_threadData;

		static tbb::enumerable_thread_specific<ThreadData, tbb::cache_aligned_allocator<Process::ThreadData>, tbb::ets_key_per_instance> g_threadData;

};

} // namespace Gaffer

#endif // GAFFER_PROCESS_H
