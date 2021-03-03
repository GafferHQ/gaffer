//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGETEST_CONTEXTSANITISER_H
#define GAFFERIMAGETEST_CONTEXTSANITISER_H

#include "GafferImageTest/Export.h"

#include "Gaffer/Monitor.h"
#include "Gaffer/Plug.h"

#include "tbb/concurrent_unordered_set.h"

namespace GafferImageTest
{

/// A monitor which warns about common context handling mistakes.
class GAFFERIMAGETEST_API ContextSanitiser : public Gaffer::Monitor
{

	public :

		ContextSanitiser();

		IE_CORE_DECLAREMEMBERPTR( ContextSanitiser )

	protected :

		void processStarted( const Gaffer::Process *process ) override;
		void processFinished( const Gaffer::Process *process ) override;

	private :

		/// First is the upstream plug where the problem was detected. Second
		/// is the plug from the parent process responsible for calling upstream.
		using PlugPair = std::pair<Gaffer::ConstPlugPtr, Gaffer::ConstPlugPtr>;
		using Warning = std::pair<PlugPair, IECore::InternedString>;

		void warn( const Gaffer::Process &process, const IECore::InternedString &contextVariable );

		using WarningSet = tbb::concurrent_unordered_set<Warning>;
		WarningSet m_warningsEmitted;

};

IE_CORE_DECLAREPTR( ContextSanitiser )

} // namespace GafferImageTest

#endif // GAFFERIMAGETEST_CONTEXTSANITISER_H
