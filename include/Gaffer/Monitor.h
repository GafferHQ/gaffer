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

#ifndef GAFFER_MONITOR_H
#define GAFFER_MONITOR_H

#include "boost/noncopyable.hpp"

namespace Gaffer
{

class Process;

/// Base class for monitoring node graph processes.
class Monitor : boost::noncopyable
{

	public :

		Monitor();
		virtual ~Monitor();

		void setActive( bool active );
		bool getActive() const;

		class Scope : boost::noncopyable
		{

			public :

				/// Constructing the Scope makes the monitor active.
				/// If monitor is NULL, the Scope is a no-op.
				Scope( Monitor *monitor );
				/// Destruction of the Scope makes the monitor inactive.
				~Scope();

			private :

				Monitor *m_monitor;

		};

	protected :

		friend class Process;

		/// Implementations must be safe to call concurrently.
		virtual void processStarted( const Process *process ) = 0;
		/// Implementations must be safe to call concurrently.
		virtual void processFinished( const Process *process ) = 0;

};

} // namespace Gaffer

#endif // GAFFER_MONITOR_H
