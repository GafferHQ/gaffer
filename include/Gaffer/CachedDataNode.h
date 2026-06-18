//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/ComputeNode.h"
#include "Gaffer/Spreadsheet.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include "IECore/MurmurHash.h"

#include "boost/algorithm/string/replace.hpp"
#include "boost/unordered_set.hpp"

#include "tbb/spin_rw_mutex.h"

#include <unordered_set>

namespace Gaffer
{

class GAFFER_API CachedDataNode : public ComputeNode
{

	public :

		explicit CachedDataNode(
			const std::string &name=defaultName<ComputeNode>(),
			const std::string &sourceDirectory = "", IECore::ConstCompoundDataPtr caches = nullptr
		);
		~CachedDataNode() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::CachedDataNode, CachedDataNodeTypeId, ComputeNode );

		BoolPlug *enabledPlug() override;
		const BoolPlug *enabledPlug() const override;

		StringPlug *selectorPlug();
		const StringPlug *selectorPlug() const;

		StringPlug *targetDirectoryPlug();
		const StringPlug *targetDirectoryPlug() const;

		CompoundObjectPlug *dataPlug();
		const CompoundObjectPlug *dataPlug() const;

		StringVectorDataPlug *keysPlug();
		const StringVectorDataPlug *keysPlug() const;

		void save( const std::filesystem::path &directory, boost::unordered_set<IECore::MurmurHash> &usedHashes, std::string &warning ) const;

		virtual void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

		// TODO - null to remove?
		void setEntry( const IECore::InternedString &key, IECore::ConstObjectPtr value );

		// TODO throwExceptions naming/spelling
		IECore::ConstObjectPtr getEntry( const IECore::InternedString &key, bool throwExceptions = true ) const;

		bool hasLiveEntries() const;
		// TODO - bad name
		std::map<IECore::InternedString, IECore::MurmurHash> entryHashes() const;

		static std::string cacheFileNameFromHash( const IECore::MurmurHash &h );
		static std::optional<IECore::MurmurHash> cacheFileNameToHash( const std::string &fileName );

		std::filesystem::path sourceDirectory() const;

		static std::filesystem::path recycleBinForDirectory( const std::filesystem::path &cacheDir );

	protected :
		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

	private :

		class SetEntryAction;

		struct CacheEntry
		{
			IECore::MurmurHash m_hash;
			// TODO - rename to m_liveValue?
			mutable IECore::ConstObjectPtr m_value;
		};

		void setEntryInternal( const IECore::InternedString &key, std::optional<CacheEntry> value );
		IECore::ConstObjectPtr getEntryIfLive( const IECore::InternedString &key ) const;

		IntPlug *refreshCountPlug();
		const IntPlug *refreshCountPlug() const;

		// Evaluate the cache - used by getEntry, and the output plugs
		ObjectPlug *evaluatePlug();
		const ObjectPlug *evaluatePlug() const;

		// TODO - figure out what I'm doing with this mutex ( it was set up in an earlier prototype, but I probably
		// do still need some mutexing to make this threadsafe )
		mutable tbb::spin_rw_mutex m_mutex;

		std::map<IECore::InternedString, CacheEntry> m_caches;
		mutable std::filesystem::path m_directory;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( CachedDataNode );

} // namespace Gaffer
