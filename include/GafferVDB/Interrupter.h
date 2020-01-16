//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Don Boogert. All rights reserved.
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
//      * Neither the name of Don Boogert nor the names of
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

#ifndef GAFFERVDB_INTERRUPTER_H
#define GAFFERVDB_INTERRUPTER_H

#include "IECore/Canceller.h"

namespace GafferVDB
{

class Interrupter {

	public:

		Interrupter(const IECore::Canceller *canceller)
		: m_canceller(canceller),
		  m_interrupted(false)
		{
		}

		void start(const char* name = nullptr)
		{
		}

		void end()
		{
		}

		bool wasInterrupted( int percent = -1 )
		{
			if ( m_interrupted )
			{
				return true;
			}

			// todo this a a problem installing a exception handler
			// per a call to this function.
			try
			{
				IECore::Canceller::check( m_canceller );
			}
			catch( const IECore::Cancelled& )
			{
				m_interrupted = true;
			}

			return m_interrupted;
		}
	private:
		const IECore::Canceller* m_canceller;
		bool m_interrupted;

};

} // namespace GafferVDB

#endif // GAFFERVDB_INTERRUPTER_H

