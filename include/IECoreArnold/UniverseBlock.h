//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "IECoreArnold/Export.h"

#include "boost/noncopyable.hpp"

#include "ai_universe.h"

namespace IECoreArnold
{

/// Manages Arnold initialisation via `AiBegin()` and creation and
/// destruction of AtUniverse objects via `AiUniverse()` and
/// `AiUniverseDestroy()`.
class IECOREARNOLD_API UniverseBlock : public boost::noncopyable
{

	public :

		/// Ensures that the Arnold API is initialised and that all plugins and
		/// metadata files on the ARNOLD_PLUGIN_PATH have been loaded.
		/// Constructs with a uniquely owned universe if `writable == true`, and
		/// a potentially shared universe otherwise. The latter is useful for
		/// making queries via the `AiNodeEntry` API.
		UniverseBlock( bool writable );
		/// Releases the universe created by the constructor.
		~UniverseBlock();

		AtUniverse *universe() { return m_universe; }

	private :

		const bool m_writable;
		AtUniverse *m_universe;

};

} // namespace IECoreArnold
