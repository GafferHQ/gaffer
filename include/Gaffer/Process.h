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

#include "Gaffer/Export.h"
#include "Gaffer/ThreadState.h"

#include "IECore/InternedString.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context );
IE_CORE_FORWARDDECLARE( Plug );

/// Base class representing a node graph process being
/// performed on behalf of a plug. Processes are never
/// created directly by client code, but are generated
/// internally in response to calls such as
/// ValuePlug::getValue(). Typically processes can be
/// considered to be entirely an internal implementation
/// detail - they are exposed publicly only so they can
/// be used by the Monitor classes.
class GAFFER_API Process : private ThreadState::Scope
{

	public :

		/// The type of process being performed.
		const IECore::InternedString type() const { return m_type; }
		/// The plug which is the subject of the process being performed.
		const Plug *plug() const { return m_plug; }
		/// The plug which triggered the process. This may be the same as
		/// `plug()` or may be a downstream plug. In either case,
		/// `destinationPlug()->source() == plug()`.
		const Plug *destinationPlug() const { return m_destinationPlug; }
		/// The context in which the process is being
		/// performed.
		const Context *context() const { return m_threadState->m_context; }

		/// Returns the parent process for this process - that
		/// is, the process that invoked this one.
		const Process *parent() const { return m_parent; }

		/// Returns the Process currently being performed on
		/// this thread, or null if there is no such process.
		static const Process *current();

		/// Check if we must force the monitored process to run, rather than using employing caches that
		/// may allow skipping the execution ( obviously, this is much slower than using the caches )
		inline static bool forceMonitoring( const ThreadState &s, const Plug *plug, const IECore::InternedString &processType );

	protected :

		/// Protected constructor for use by derived classes only.
		Process( const IECore::InternedString &type, const Plug *plug, const Plug *destinationPlug = nullptr );
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

		static bool forceMonitoringInternal( const ThreadState &s, const Plug *plug, const IECore::InternedString &processType );

		void emitError( const std::string &error, const Plug *source = nullptr ) const;

		IECore::InternedString m_type;
		const Plug *m_plug;
		const Plug *m_destinationPlug;
		const Process *m_parent;

};

/// Used to wrap exceptions that occur during execution of a Process,
/// adding plug name and process type to the original message.
class GAFFER_API ProcessException : public std::runtime_error
{

	public :

		ProcessException( const ProcessException &rhs ) = default;

		const Plug *plug() const;
		const Context *context() const;
		IECore::InternedString processType() const;

		/// Rethrows the original exception that was wrapped by `wrapCurrentException()`.
		[[noreturn]] void rethrowUnwrapped() const;

		/// Throws a ProcessException wrapping the current exception and storing
		/// the specified process information.
		[[noreturn]] static void wrapCurrentException( const Process &process );
		[[noreturn]] static void wrapCurrentException( const ConstPlugPtr &plug, const Context *context, IECore::InternedString processType );

	private :

		ProcessException( const ConstPlugPtr &plug, const Context *context, IECore::InternedString processType, const std::exception_ptr &exception, const char *what );

		static std::string formatWhat( const Plug *plug, const char *what );

		ConstPlugPtr m_plug;
		ConstContextPtr m_context;
		const IECore::InternedString m_processType;
		std::exception_ptr m_exception;

};

} // namespace Gaffer

#include "Gaffer/Process.inl"

#endif // GAFFER_PROCESS_H
