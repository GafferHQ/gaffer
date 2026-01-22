//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#pragma once

#include "GafferSceneTest/Export.h"

#include "Gaffer/Monitor.h"
#include "Gaffer/TypedObjectPlug.h"

#include "tbb/concurrent_unordered_set.h"
#include "tbb/concurrent_unordered_map.h"

namespace GafferSceneTest
{

/// A monitor which warns if the scene globals depend on some other
/// aspect of the scene. Our rule is that the globals must be fast to
/// compute, so should not depend on the rest of the scene, because that
/// could be arbitrarily complex.
class GAFFERSCENETEST_API GlobalsSanitiser : public Gaffer::Monitor
{

	public :

		GlobalsSanitiser();

		IE_CORE_DECLAREMEMBERPTR( GlobalsSanitiser )

	protected :

		void processStarted( const Gaffer::Process *process ) override;
		void processFinished( const Gaffer::Process *process ) override;

	private :

		// Maps from a process to the closest `ScenePlug.globals` that depends on it.
		using DependentGlobalsMap = tbb::concurrent_unordered_map<const Gaffer::Process *, const Gaffer::CompoundObjectPlug *>;
		DependentGlobalsMap m_dependentGlobalsMap;

		// First is the upstream plug where the problem was detected. Second
		// is the downstream globals plug which depended on it.
		using Warning = std::pair<Gaffer::ConstPlugPtr, Gaffer::ConstCompoundObjectPlugPtr>;
		using WarningSet = tbb::concurrent_unordered_set<Warning>;
		// Used to avoid outputting duplicate warnings.
		WarningSet m_warningsEmitted;

		void warn( const Gaffer::Process &process, const Gaffer::CompoundObjectPlug *dependentGlobals );

};

IE_CORE_DECLAREPTR( GlobalsSanitiser )

} // namespace GafferSceneTest
