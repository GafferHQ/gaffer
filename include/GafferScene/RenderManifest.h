//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Export.h"

#include "GafferScene/ScenePlug.h"

#include "boost/multi_index/member.hpp"
#include "boost/multi_index/ordered_index.hpp"
#include "boost/multi_index_container.hpp"

#include "tbb/spin_rw_mutex.h"

#include <filesystem>

// Maps between scene locations and integer ids.

namespace GafferScene
{

class GAFFERSCENE_API RenderManifest
{

	public :
		RenderManifest();

		uint32_t acquireID( const ScenePlug::ScenePath &path );

		uint32_t idForPath( const ScenePlug::ScenePath &path ) const;
		std::optional<ScenePlug::ScenePath> pathForId( uint32_t id ) const;

		std::vector<uint32_t> acquireIDs( const IECore::PathMatcher &paths );

		std::vector<uint32_t> idsForPaths( const IECore::PathMatcher &paths ) const;
		IECore::PathMatcher pathsForIDs( const std::vector<uint32_t> &ids ) const;

		void clear();
		size_t size() const;

		void readEXRManifest( const std::filesystem::path &filePath );
		void writeEXRManifest( const std::filesystem::path &filePath ) const;

	private :

		using PathAndId = std::pair<ScenePlug::ScenePath, uint32_t>;
		using Map = boost::multi_index::multi_index_container<
			PathAndId,
			boost::multi_index::indexed_by<
				boost::multi_index::ordered_unique<
					boost::multi_index::member<PathAndId, ScenePlug::ScenePath, &PathAndId::first>
				>,
				boost::multi_index::ordered_unique<
					boost::multi_index::member<PathAndId, uint32_t, &PathAndId::second>
				>
			>
		>;

		// Note: a very rough test indicates that when rendering many cheap locations, resulting in
		// high contention on this class, using a spin mutex to limit access here is much slower
		// than giving each thread its own accumulator and then combining them afterwards. The
		// measured overhead is about 0.4 seconds per million entries, vs 0.1 seconds per million
		// entries with per thread accumulators. There isn't really a simple way to expose per-thread
		// accumulators though ... the current thought is that it's worth the 0.3s of overhead to keep
		// the API simple.
		using Mutex = tbb::spin_rw_mutex;

		Map m_map;
		mutable Mutex m_mutex;

};

} // namespace GafferScene
