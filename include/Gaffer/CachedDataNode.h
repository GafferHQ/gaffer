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

#include "tbb/spin_rw_mutex.h"

// TODO use std::unordered_set once I figure out how to get MurmurHash to work with it
//#include <unordered_set>
#include "boost/unordered_set.hpp"

namespace Gaffer
{

// TODO - should I put this inside the CachedDataNode namespace?

class GAFFER_API CacheDirectoryManager
{
public:
	CacheDirectoryManager();
	~CacheDirectoryManager();

	void startSerialisation( const std::filesystem::path &currentScriptPath, bool takeOwnership );
	void finishSerialisation( const boost::unordered_set<IECore::MurmurHash> &usedCaches );

	std::filesystem::path getCacheDirectory();

	std::optional<std::filesystem::path> findCache( const std::string &fileName ) const;

private:

	std::filesystem::path acquireRecycleBin();

	std::filesystem::path m_currentScriptPath;
	bool m_takeOwnership;
	bool m_currentCacheDirWritten;

	std::set<std::filesystem::path> m_cacheDirectories;
	std::set<std::filesystem::path> m_ownedRecycleBins;
};


class GAFFER_API CachedDataNode : public ComputeNode
{

	public :

		explicit CachedDataNode(
			const std::string &name=defaultName<ComputeNode>(),
			const std::string &sourceDirectory = "", IECore::ConstCompoundDataPtr caches = nullptr
		);
		~CachedDataNode() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::CachedDataNode, CachedDataNodeTypeId, ComputeNode );

		StringPlug *selectorPlug();
		const StringPlug *selectorPlug() const;

		ObjectPlug *dataPlug();
		const ObjectPlug *dataPlug() const;

		StringVectorDataPlug *keysPlug();
		const StringVectorDataPlug *keysPlug() const;

		void save( CacheDirectoryManager &cacheDirectoryManager, boost::unordered_set<IECore::MurmurHash> &usedHashes, std::string &warning ) const;

		virtual void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

		// TODO - separate call to remove entries, or pass null here to remove?
		void setEntry( const IECore::InternedString &key, IECore::ConstObjectPtr value );

		IECore::ConstObjectPtr getEntry( const IECore::InternedString &key, bool throwExceptions = true ) const;

		bool hasLiveEntries() const;
		std::map<IECore::InternedString, IECore::MurmurHash> entryHashes() const;

		static std::string cacheFileNameFromHash( const IECore::MurmurHash &h );
		static std::optional<IECore::MurmurHash> cacheFileNameToHash( const std::string &fileName );

		std::filesystem::path sourceDirectory() const;

	protected :
		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

	private :

		class SetEntryAction;

		struct CacheEntry
		{
			IECore::MurmurHash m_hash;
			mutable IECore::ConstObjectPtr m_liveValue;
		};

		void setEntryInternal( const IECore::InternedString &key, std::optional<CacheEntry> value );
		IECore::ConstObjectPtr getEntryIfLive( const IECore::InternedString &key ) const;

		IntPlug *refreshCountPlug();
		const IntPlug *refreshCountPlug() const;

		// Evaluate the cache - used by getEntry, and the output plugs
		ObjectPlug *evaluatePlug();
		const ObjectPlug *evaluatePlug() const;

		// TODO - figure out what I'm doing with this mutex - it was needed by an earlier prototype, but
		// maybe is no longer necessary ... is it true that calls to setValue are expected to be serial,
		// and not happen while computes are running, and can the same be assumed for setEntry?
		//mutable tbb::spin_rw_mutex m_mutex;

		const std::filesystem::path m_sourceDirectory;
		std::map<IECore::InternedString, CacheEntry> m_caches;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( CachedDataNode );

} // namespace Gaffer
