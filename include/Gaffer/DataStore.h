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

#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include "IECore/MurmurHash.h"

#include "tbb/spin_rw_mutex.h"

#include <unordered_set>

namespace GafferModule
{

// Forward declaration for friendship declared below.
// We don't include DataSToreBinding.h because we don't want
// python involved in any way when building the pure C++
// modules.
struct DataStoreWrapperFunctionContainer;
struct DataStoreSerialisationTracker;
class DataStoreSerialiser;

} // namespace GafferModule


namespace Gaffer
{

class GAFFER_API DataStore : public ComputeNode
{

	public :

		explicit DataStore( const std::string &name=defaultName<ComputeNode>() );
		~DataStore() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::DataStore, DataStoreTypeId, ComputeNode );

		StringPlug *selectorPlug();
		const StringPlug *selectorPlug() const;

		ObjectPlug *outPlug();
		const ObjectPlug *outPlug() const;

		StringVectorDataPlug *keysPlug();
		const StringVectorDataPlug *keysPlug() const;

		virtual void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

		// The data is stored as key/value pairs called entries. They can be set, removed, and gotten.
		void setEntry( const std::string &key, IECore::ConstObjectPtr value );
		void removeEntry( const std::string &key );
		IECore::ConstObjectPtr getEntry( const std::string &key, bool throwExceptions = true ) const;

		// Check whether the value for this key is being held in dedicated memory by this DataStore.
		// If false, it is stored on disk, and only held in memory by the standard ValuePlug cache,
		// where it can be freed if the memory is needed for other things.
		bool isLive( const std::string &key ) const;

	protected :
		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

		// Used during deserialisation to load all the entries which were previously set
		friend struct GafferModule::DataStoreWrapperFunctionContainer;
		void loadEntries( const std::map< std::string, IECore::MurmurHash > &entries, const std::string &loadFrom = "" );

	private :

		class SetEntryAction;

		// This is incremented by setEntry so that the hash cache will pick up the update.
		IntPlug *refreshCountPlug();
		const IntPlug *refreshCountPlug() const;

		// Evaluate the entry for a key in the context - used by getEntry, and the output plugs.
		ObjectPlug *evaluatePlug();
		const ObjectPlug *evaluatePlug() const;


		struct Entry
		{
			IECore::MurmurHash m_hash;
			mutable IECore::ConstObjectPtr m_liveValue;
		};

		std::unordered_map<std::string, Entry> m_entries;

		// The live values are cleared after being saved, which can be triggered from a background
		// thread, so we need a mutex to protect them.
		mutable tbb::spin_rw_mutex m_entriesLiveValueMutex;

		void setEntryInternal( const std::string &key, const std::optional<Entry> &value );

		// The directory manager handles the directory where we can find values for any entries that
		// aren't live.
		class DirectoryManager;
		mutable std::shared_ptr<DirectoryManager> m_sourceDirectory;

		static std::shared_ptr<DirectoryManager> acquireDirectoryManager( const std::filesystem::path &scriptPath );


		// DataStoreSerialiser needs access to m_entries and checkSaved()
		friend class GafferModule::DataStoreSerialiser;

		// If there isn't a data store directory associated with serialisation, then we need to make sure
		// everything is already saved.
		void checkSaved() const;

		// DataStoreSerialisationTracker needs access to these private functions
		friend struct GafferModule::DataStoreSerialisationTracker;

		// Implement the actual saving of all entries for this node, and update usedDataHashes
		void save( const std::filesystem::path &scriptPath, const GraphComponent *serialisationParent, std::unordered_set< IECore::MurmurHash > &usedDataHashes ) const;

		// When we finish writing a data store directory, we remove files for entries that are no longer used,
		// either deleting them, or placing them in a recycle bin if they could be needed by an undo in the future.
		static void finaliseDirectory(
			const std::filesystem::path &scriptPath, const GraphComponent *serialisationParent,
			const std::unordered_set< IECore::MurmurHash > &usedDataHashes
		);


		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( DataStore );

} // namespace Gaffer
