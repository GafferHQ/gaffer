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
#include "boost/noncopyable.hpp"

#include "tbb/spin_rw_mutex.h"

#include <filesystem>

namespace GafferScene
{

// Maps between scene locations and integer ids.
class GAFFERSCENE_API RenderManifest : boost::noncopyable
{

	public :

		RenderManifest();

		// Return the id for the path if it is found in the manifest, otherwise insert
		// it and return the freshly created id.
		uint32_t acquireID( const ScenePlug::ScenePath &path );

		// Return the id for the path if it is found in the manifest, otherwise return 0.
		uint32_t idForPath( const ScenePlug::ScenePath &path ) const;

		// Return the path for the id, if it is found in the manifest.
		std::optional<ScenePlug::ScenePath> pathForID( uint32_t id ) const;

		// The same functionality as above, except operating on multiple items at once.
		// More efficient than calling the above functions in a loop.
		std::vector<uint32_t> acquireIDs( const IECore::PathMatcher &paths );
		std::vector<uint32_t> idsForPaths( const IECore::PathMatcher &paths ) const;
		IECore::PathMatcher pathsForIDs( const std::vector<uint32_t> &ids ) const;

		// Reset the manifest.
		void clear();

		// Return the number of id/path pairs in the manifest.
		size_t size() const;

		// Find a RenderManifest stored in image metadata, according to either a
		// Gaffer convention ( gaffer:renderManifestFilePath pointing to a sidecar exr file
		// containing an exr manifest ), or a Cryptomatte convention ( a cryptomatte
		// metadata entry matching `cryptomatteLayerName`, with JSON text stored
		// directly in the image metadata, or in a sidecar JSON file ).
		//
		// If called repeatedly, will attempt to avoid reloading the manifest if relevant
		// metadata has not changed.
		//
		// In order to get this behaviour, you must not release the shared pointer to the previous manifest you
		// loaded until after calling this method again ( releasing it to soon would cause it to be evicted from
		// the cache, and unnecessarily reloaded ).
		static std::shared_ptr< const RenderManifest > loadFromImageMetadata( const IECore::CompoundData *metadata, const std::string &cryptomatteLayerName );

		// Write the current maninfest to a sidecar EXR file. This file will not contain any image data,
		// but uses the EXR id manifest format to store this manifest in the header.
		void writeEXRManifest( const std::filesystem::path &filePath ) const;

	private :

		using PathAndID = std::pair<ScenePlug::ScenePath, uint32_t>;
		using Map = boost::multi_index::multi_index_container<
			PathAndID,
			boost::multi_index::indexed_by<
				boost::multi_index::ordered_unique<
					boost::multi_index::member<PathAndID, ScenePlug::ScenePath, &PathAndID::first>
				>,
				boost::multi_index::ordered_unique<
					boost::multi_index::member<PathAndID, uint32_t, &PathAndID::second>
				>
			>
		>;

		void loadEXRManifest( const std::filesystem::path &filePath );
		void loadCryptomatteJSON( std::istream &in );

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
