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

#include "Gaffer/DataStore.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/Process.h"
#include "Gaffer/ValuePlug.h"

#include "IECore/CompoundParameter.h"
#include "IECore/NullObject.h"
#include "IECore/FileIndexedIO.h"
#include "IECore/ObjectWriter.h"

#include "fmt/std.h"

#include "tbb/concurrent_hash_map.h"

#include <regex>

using namespace Gaffer;

namespace
{

// Must match the definition in ScriptNode.cpp
const IECore::InternedString g_executionSourceFileContextName( "execution:sourceFile" );

// Check if the current serialisation is a save/saveAs ( so the nodes should now point to their
// new location on disk ), as opposed to an export ( which shouldn't affect the current nodes )
bool serialiseIsSave( const std::filesystem::path *scriptPath, const GraphComponent* serialisationParent )
{
	const ScriptNode *scriptNode = IECore::runTimeCast<const ScriptNode>( serialisationParent );
	if( ( !scriptNode ) || ( !scriptPath ) )
	{
		return false;
	}

	return std::filesystem::path( scriptNode->fileNamePlug()->getValue() ) == *scriptPath;
}

static const IECore::InternedString g_dataStoreEvaluationKeyName( "__dataStoreEvaluationKey" );

std::string dataStoreFileNameFromHash( const IECore::MurmurHash &h )
{
	return h.toString() + ".cob";
}

std::optional<IECore::MurmurHash> dataStoreFileNameToHash( const std::string &fileName )
{
	static const std::regex g_dataStoreFileNameRegex( R"(([0-9a-f]{32})\.cob)" );

	std::smatch match;
	if( std::regex_match( fileName, match, g_dataStoreFileNameRegex ) )
	{
		return IECore::MurmurHash::fromString( match.str( 1 ) );
	}

	return {};
}

IECore::ConstObjectPtr loadDataFile( const std::filesystem::path &filePath )
{
	IECore::FileIndexedIOPtr file = new IECore::FileIndexedIO(
		filePath.generic_string(), IECore::IndexedIO::rootPath, IECore::IndexedIO::Read
	);

	return IECore::Object::load( file, "object" );
}

} // namespace


class DataStore::SetEntryAction : public Gaffer::Action
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::DataStore::SetEntryAction, DataStoreSetEntryActionTypeId, Gaffer::Action );

		SetEntryAction( DataStorePtr node, const std::string &key, IECore::ConstObjectPtr value )
			: m_node( node ), m_key( key ), m_doValue( value ? std::make_optional<Entry>( {value->hash(), value} ) : std::nullopt )
		{
			// The source directory isn't changed by a SetEntry - it's changed by serialisation, which
			// happens in between SetEntry's. But undo'ing or redo'ing a SetEntry is what could trigger
			// needing to use a previous or future sourceDirectory, and we can support that by recording
			// this directory which is valid before or after this operation.
			m_sourceDirectory = node->m_sourceDirectory;

			auto it = node->m_entries.find( key );
			if( it != node->m_entries.end() )
			{
				m_undoValue = it->second;
			}
		}

		~SetEntryAction()
		{
		}

	protected :

		GraphComponent *subject() const override
		{
			return m_node.get();
		}

		void doAction() override
		{
			Action::doAction();
			m_node->setEntryInternal( m_key, m_doValue );
			// Currently, no tests fail if this isn't set, because after a redo, the value is
			// live. But it is conceptually correct to set the source directory to the value
			// it had at this point in the sequence of actions, and this could become important
			// if we start cleaning the live values out of the undo queue at some point.
			m_node->m_sourceDirectory = m_sourceDirectory;
		}

		void undoAction() override
		{
			Action::undoAction();
			m_node->setEntryInternal( m_key, m_undoValue );
			m_node->m_sourceDirectory = m_sourceDirectory;
		}

		bool canMerge( const Action *other ) const override
		{
			if( !Action::canMerge( other ) )
			{
				return false;
			}
			const SetEntryAction *setEntryAction = IECore::runTimeCast<const SetEntryAction>( other );
			return setEntryAction &&
				setEntryAction->m_node == m_node &&
				setEntryAction->m_key == m_key &&
				setEntryAction->m_sourceDirectory == m_sourceDirectory;
		}

		void merge( const Action *other ) override
		{
			const SetEntryAction *setEntryAction = static_cast<const SetEntryAction *>( other );
			m_doValue = setEntryAction->m_doValue;
		}

	private :

		DataStorePtr m_node;
		std::string m_key;

		std::shared_ptr<DirectoryManager> m_sourceDirectory;

		// \todo In a long paint session on heavy geo, it's very plausible that a large amount of memory
		// could be consumed by holding live values in the undo queue. In theory, you could probably
		// even run out of memory and crash. Since we already need the .recycleBin folder for dealing
		// with unused files that haven't been loaded ( but could be needed by undo ), it would be possible
		// to use the .recycleBin folder for dealing with this memory accumulation: when we save, we could
		// write all live value in the undo queue into the recycle bin, and clear them out of the undo
		// queue. Kinda seems like a good idea, but maybe not necessary currently.
		std::optional<Entry> m_doValue;
		std::optional<Entry> m_undoValue;

};

IE_CORE_DEFINERUNTIMETYPED( DataStore::SetEntryAction );

// The DirectoryManager handles the data store directory and recycle bin directory associated with a given script
// path. Its lifespan lasts as long as anything might need to access something from these directories. When it
// is freed, the associated recycle bin can be deleted ( since those values are now inaccessible ).
class DataStore::DirectoryManager
{
public:
	DirectoryManager( const std::filesystem::path &scriptPath )
		: m_dataStoreDirectory( scriptPath.parent_path() / ( scriptPath.filename().string() + ".dataStore" ) ),
		m_recycleBinDirectory( m_dataStoreDirectory / ".recycleBin" ),
		m_recycleBinAcquired( false )
	{
	}

	~DirectoryManager()
	{
		if( m_recycleBinAcquired )
		{
			// This is a fairly scary looking system call, so this is probably a good place to write
			// down some justification why this seems like it should be safe:
			// In order to get here, the path must end in ".recycleBin", and m_recycleBinAcquired must have
			// been set by acquireRecycleBin, which ensures that it didn't previously exist.
			// That should ensure that we're not deleting directories we don't own.
			// In order to be placed in a recycle bin, a file must be found in a ".dataStore" directory
			// corresponding to a script file that is currently being overwritten, and must look like
			// a Gaffer data store ( ie. matches the regex "[0-9a-f]{32}.cob", enforced by
			// dataStoreFileNameToHash ).

			std::filesystem::remove_all( m_recycleBinDirectory );
		}
	}

	const std::filesystem::path &dataStoreDirectory()
	{
		return m_dataStoreDirectory;
	}

	const std::filesystem::path &acquireRecycleBin()
	{
		if( !m_recycleBinAcquired )
		{
			if( std::filesystem::exists( m_recycleBinDirectory ) )
			{
				// TODO - need a way to repair this?
				// TODO - put a tag file in the dir so we can identify owning process / handle differently if process still open?
				throw IECore::Exception( fmt::format( "Cannot acquire recycle bin - something else owns a recycle bin at {}", m_recycleBinDirectory ) );
			}

			std::filesystem::create_directories( m_recycleBinDirectory );
			m_recycleBinAcquired = true;
		}

		return m_recycleBinDirectory;
	}

	std::optional<std::filesystem::path> getRecycleBinIfExists()
	{
		if( m_recycleBinAcquired )
		{
			return m_recycleBinDirectory;
		}
		else
		{
			return {};
		}
	}

private:

	const std::filesystem::path m_dataStoreDirectory;
	const std::filesystem::path m_recycleBinDirectory;
	bool m_recycleBinAcquired;
};

std::shared_ptr<DataStore::DirectoryManager> DataStore::acquireDirectoryManager( const std::filesystem::path &scriptPath )
{
	// When using a path as a key, we don't want two different representations of the same path to compare
	// differently.
	const std::filesystem::path scriptPathCanonical = std::filesystem::weakly_canonical( scriptPath );

	// Directory managers are held in a global map of weak_ptrs, so that they can be shared, and freed
	// when the last thing stops using them

	struct FilesystemHashCompare
	{
		size_t hash( const std::filesystem::path& x ) const
		{
			return std::filesystem::hash_value( x );
		}
		bool equal( const std::filesystem::path& x, const std::filesystem::path& y ) const
		{
			return x==y;
		}
	};

	using ConcurrentMap = tbb::concurrent_hash_map< std::filesystem::path, std::weak_ptr<DataStore::DirectoryManager>, FilesystemHashCompare >;
	static ConcurrentMap directoryManagers;

	std::shared_ptr<DirectoryManager> result;

	ConcurrentMap::accessor access;
	if( !directoryManagers.insert( access, scriptPathCanonical ) )
	{
		result = access->second.lock();
	}

	if( !result )
	{
		result = std::make_shared<DirectoryManager>( scriptPathCanonical );
		access->second = result;
	}

	return result;
}

GAFFER_NODE_DEFINE_TYPE( DataStore );

size_t DataStore::g_firstPlugIndex = 0;

DataStore::DataStore( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "selector", Plug::In ) );
	addChild( new ObjectPlug( "out", Plug::Out, new IECore::NullObject() ) );
	addChild( new StringVectorDataPlug( "keys", Plug::Out ) );
	addChild( new IntPlug( "__refreshCount", Plug::In, 0, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ObjectPlug( "__evaluate", Plug::Out, new IECore::NullObject() ) );
}

DataStore::~DataStore()
{
}

StringPlug *DataStore::selectorPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 0 );
}

const StringPlug *DataStore::selectorPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 0 );
}

ObjectPlug *DataStore::outPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

const ObjectPlug *DataStore::outPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 1 );
}

StringVectorDataPlug *DataStore::keysPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

const StringVectorDataPlug *DataStore::keysPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

IntPlug *DataStore::refreshCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const IntPlug *DataStore::refreshCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

ObjectPlug *DataStore::evaluatePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

const ObjectPlug *DataStore::evaluatePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

void DataStore::setEntry( const std::string &key, IECore::ConstObjectPtr value )
{
	if( !value )
	{
		throw IECore::Exception( "Null value passed to setValue" );
	}

	// Ignore setEntry calls if it matches the existing value
	auto it = m_entries.find( key );
	if( it != m_entries.end() && it->second.m_hash == value->hash() )
	{
		return;
	}

	Action::enact( new SetEntryAction( this, key, value ) );
}

void DataStore::removeEntry( const std::string &key )
{
	// Ignore removeEntry calls if there is no entry
	auto it = m_entries.find( key );
	if( it == m_entries.end() )
	{
		return;
	}

	// We have a removeEntry method in order to present a clearer API,
	// but we internally represent a remove as a SetEntry with a null
	// value in order to avoid duplicating code for SetEntryAction.
	Action::enact( new SetEntryAction( this, key, nullptr ) );
}

void DataStore::setEntryInternal( const std::string &key, const std::optional<Entry> &value )
{
	if( value )
	{
		m_entries[key] = *value;
	}
	else
	{
		m_entries.erase( key );
	}

	refreshCountPlug()->setValue( refreshCountPlug()->getValue() + 1 );
}

IECore::ConstObjectPtr DataStore::getEntry( const std::string &key, bool throwExceptions ) const
{
	try
	{
		// We use an evaluation plug to provide the getEntry() functionality - this means we can
		// use Gaffer's default plug cache to ensure that we don't load a file twice if it is
		// queried both via getEntry and via an output plug.
		Context::EditableScope s( Context::current() );
		s.set( g_dataStoreEvaluationKeyName, &key );
		return evaluatePlug()->getValue();
	}
	catch( ProcessException &e )
	{
		if( throwExceptions )
		{
			e.rethrowUnwrapped();
		}
		else
		{
			return nullptr;
		}
	}
}

bool DataStore::isLive( const std::string &key ) const
{
	tbb::spin_rw_mutex::scoped_lock liveValueLock( m_entriesLiveValueMutex, /* write = */ false );
	auto it = m_entries.find( key );
	if( it == m_entries.end() )
	{
		return false;
	}

	return it->second.m_liveValue != nullptr;
}

void DataStore::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == refreshCountPlug() ||
		input == selectorPlug()
	)
	{
		outputs.push_back( evaluatePlug() );
	}

	if(
		input == refreshCountPlug()
	)
	{
		outputs.push_back( keysPlug() );
	}

	if(
		input == evaluatePlug()
	)
	{
		outputs.push_back( outPlug() );
	}
}

void DataStore::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	if( output == evaluatePlug() )
	{
		const std::string &key = context->get<std::string>( g_dataStoreEvaluationKeyName );

		auto it = m_entries.find( key );
		if( it == m_entries.end() )
		{
			throw IECore::Exception( "Unknown key: " + key );
		}

		h = it->second.m_hash;
		return;
	}
	else if( output == outPlug() )
	{
		Context::EditableScope s( context );
		std::string select = selectorPlug()->getValue();
		s.set( g_dataStoreEvaluationKeyName, &select );

		h = evaluatePlug()->hash();
		return;
	}
	else if( output == keysPlug() )
	{
		ComputeNode::hash( output, context, h );

		for( const auto &[key, entry] : m_entries )
		{
			h.append( key );
		}
		return;
	}


	ComputeNode::hash( output, context, h );
}

void DataStore::compute( ValuePlug *output, const Context *context ) const
{
	if( output == evaluatePlug() )
	{
		IECore::ConstObjectPtr result;
		const std::string &key = context->get<std::string>( g_dataStoreEvaluationKeyName );

		auto it = m_entries.find( key );
		if( it == m_entries.end() )
		{
			throw IECore::Exception( "Unknown key: " + key );
		}

		tbb::spin_rw_mutex::scoped_lock liveValueLock( m_entriesLiveValueMutex, /* write = */ false );
		if( it->second.m_liveValue )
		{
			result = it->second.m_liveValue;
		}
		else
		{
			auto entryIt = m_entries.find( key );
			if( entryIt != m_entries.end() )
			{
				std::string dataStoreFileName = dataStoreFileNameFromHash( entryIt->second.m_hash );

				std::optional<std::filesystem::path> sourcePath;
				if( m_sourceDirectory )
				{
					if( IECore::FileIndexedIO::canRead( ( m_sourceDirectory->dataStoreDirectory() / dataStoreFileName ).generic_string() ) )
					{
						sourcePath = m_sourceDirectory->dataStoreDirectory() / dataStoreFileName;
					}
					else if( const std::optional<std::filesystem::path> recycleBinDir = m_sourceDirectory ? m_sourceDirectory->getRecycleBinIfExists() : std::nullopt )
					{
						std::filesystem::path recycleBinPath = (*recycleBinDir) / dataStoreFileName;

						if( IECore::FileIndexedIO::canRead( recycleBinPath.generic_string() ) )
						{
							sourcePath = recycleBinPath;
						}
					}
				}

				if( !sourcePath )
				{
					throw IECore::Exception( fmt::format(
						"Could not locate data store file {} in {}.", dataStoreFileName, m_sourceDirectory->dataStoreDirectory()
					) );
				}

				result = loadDataFile( *sourcePath );
			}
		}

		if( !result )
		{
			throw IECore::Exception( "Unknown key: " + key );
		}

		static_cast<ObjectPlug *>( output )->setValue( result );
		return;

	}
	else if( output == outPlug() )
	{
		Context::EditableScope s( context );
		std::string select = selectorPlug()->getValue();
		s.set( g_dataStoreEvaluationKeyName, &select );

		static_cast<ObjectPlug *>( output )->setValue( evaluatePlug()->getValue() );
		return;
	}
	else if( output == keysPlug() )
	{
		std::vector<std::string> keys;

		for( const auto &[key, entry] : m_entries )
		{
			keys.push_back( key );
		}

		std::sort( keys.begin(), keys.end() );

		static_cast<StringVectorDataPlug *>( output )->setValue(
			new IECore::StringVectorData( std::move( keys ) )
		);
		return;
	}

	ComputeNode::compute( output, context );
}

void DataStore::loadEntries( const std::map< std::string, IECore::MurmurHash > &entries, const std::string &loadFrom )
{
	bool needsLoad;
	std::filesystem::path sourceScript;
	if( loadFrom.empty() )
	{
		// By default, the source directory for data stores corresponds to the source file we
		// are executing.
		// This will fail if source file context variable isn't set ( ie the serialisation
		// we're executing didn't come from a file ), but we should never hit that exception,
		// because loadFrom should always be set in those cases.
		needsLoad = false;
		sourceScript = Context::current()->get<std::string>( g_executionSourceFileContextName );
	}
	else
	{
		// When copy-and-pasting, we aren't executing a file on disk, so we need to know where to
		// find appropriate data stores. This is set via the "loadFrom" variable.
		sourceScript = loadFrom;

		const ScriptNode* scriptNode = ancestor<ScriptNode>();

		// When we're pasting a serialised value that references a different scripts data store
		// directory, we aren't taking ownership of that directory, so we can't guarantee that
		// the files will stay accessible. To prevent a scenario where everything initially
		// appears to have been pasted successful, but then breaks later when the source script
		// is modified, we force all the pasted values to load into memory.
		//
		// This isn't needed however, in the common case where we're pasting within the same script,
		// so we check if the source script matches the current filename.
		needsLoad = !( scriptNode && scriptNode->fileNamePlug()->getValue() == sourceScript );
	}

	m_sourceDirectory = acquireDirectoryManager( sourceScript );

	for( const auto &[key, hash] : entries )
	{
		if( !needsLoad )
		{
			m_entries[ key ] = { hash, nullptr };
		}
		else
		{
			try
			{
				m_entries[ key ] = { hash, loadDataFile( m_sourceDirectory->dataStoreDirectory() / dataStoreFileNameFromHash( hash ) ) };
			}
			catch( const IECore::Exception & )
			{
				throw IECore::Exception( "Cannot paste - source file uses data stores which are not accessible, or have been modified." );
			}
		}
	}
}

void DataStore::checkSaved() const
{
	// Copy and pasting a DataStore is only supported if it has already been saved to disk somewhere.
	// This function tests this.

	for( auto &[ key, entry ] : m_entries )
	{
		std::string fileName = dataStoreFileNameFromHash( entry.m_hash );

		if( !m_sourceDirectory || !std::filesystem::exists( m_sourceDirectory->dataStoreDirectory() / fileName ) )
		{
			// TODO - This exception appearing in the console doesn't feel like very clear feedback that
			// hitting Ctrl-C failed. Do we need better handling for exceptions? Or should we be using
			// a different mechanism here?
			throw IECore::Exception( fmt::format( "Cannot copy, DataStore \"{}\" is not saved yet.", fullName() ) );
		}
	}
}

void DataStore::save( const std::filesystem::path &scriptPath, const Gaffer::GraphComponent *serialisationParent, std::unordered_set< IECore::MurmurHash > &usedDataHashes ) const
{
	std::shared_ptr<DirectoryManager> targetDirectory = acquireDirectoryManager( scriptPath );

	std::string warning;

	tbb::spin_rw_mutex::scoped_lock liveValueLock( m_entriesLiveValueMutex, /* write = */ false );
	for( auto &[key, entry] : m_entries )
	{
		if( usedDataHashes.empty() )
		{
			// If this is the first time we've written something this serialisation, make sure the data store
			// directory exists
			std::filesystem::create_directories( targetDirectory->dataStoreDirectory() );
		}

		if( !usedDataHashes.insert( entry.m_hash ).second )
		{
			// This value was already saved during this serialization
			continue;
		}

		std::string fileName = dataStoreFileNameFromHash( entry.m_hash );


		std::filesystem::path destPath = targetDirectory->dataStoreDirectory() / fileName;
		if( std::filesystem::exists( destPath ) )
		{
			// This value was already saved during a previous serialization
			continue;
		}

		std::optional<std::filesystem::path> sourcePath;
		if( m_sourceDirectory )
		{
			std::filesystem::path sourceDirectoryPath = m_sourceDirectory->dataStoreDirectory() / fileName;
			if( m_sourceDirectory != targetDirectory && std::filesystem::exists( sourceDirectoryPath ) )
			{
				sourcePath = sourceDirectoryPath;
			}
			else if( m_sourceDirectory->getRecycleBinIfExists() )
			{
				std::filesystem::path recycleBinPath = (*m_sourceDirectory->getRecycleBinIfExists() ) / fileName;
				if( std::filesystem::exists( recycleBinPath ) )
				{
					sourcePath = recycleBinPath;
				}
			}
		}

		if( sourcePath )
		{
			// This value already exists on disk, but in a different directory.
			// Try to hardlink to it.
			std::error_code ec;
			std::filesystem::create_hard_link( *sourcePath, destPath, ec );
			if( ec )
			{
				if( !warning.size() )
				{
					warning = fmt::format( "During saving, could not create hardlink at {} pointing to {}, falling back to copying file.", destPath, *sourcePath );
				}

				// If that failed, just copy.
				std::filesystem::copy_file( *sourcePath, destPath );
			}
		}
		else
		{
			// This value does not yet exist on disk, and we need to write it.
			if( !entry.m_liveValue )
			{
				throw IECore::Exception( fmt::format( "Unable to save entry \"{}\" on \"{}\" - no live value, but cannot find on disk in directory {}.", key, fullName(), m_sourceDirectory->dataStoreDirectory() ) );
			}

			// I can't think why the writer would modify the source, I assume this old Cortex stuff just isn't
			// intended to be const correct.
			IECore::ObjectPtr liveValueCast = const_cast<IECore::Object*>( entry.m_liveValue.get() );

			IECore::WriterPtr writer = new IECore::ObjectWriter( liveValueCast, destPath.generic_string() );
			writer->write();
		}
	}

	if( serialiseIsSave( &scriptPath, serialisationParent ) )
	{
		// All entries now exist in target directory. Update so that we'll now read from disk
		// instead of needing to hold live values.

		m_sourceDirectory = targetDirectory;

		liveValueLock.upgrade_to_writer();
		for( auto &[key, entry] : m_entries )
		{
			entry.m_liveValue.reset();
		}
	}

	if( warning.size() )
	{
		IECore::msg( IECore::Msg::Warning, "Serialisation", warning );
	}

}

void DataStore::finaliseDirectory( const std::filesystem::path &scriptPath, const Gaffer::GraphComponent *serialisationParent, const std::unordered_set< IECore::MurmurHash > &usedDataHashes )
{
	std::shared_ptr<DirectoryManager> directoryManager = acquireDirectoryManager( scriptPath );
	const std::filesystem::path &dataStoreDirectory = directoryManager->dataStoreDirectory();

	bool isSave = serialiseIsSave( &scriptPath, serialisationParent );

	if( !std::filesystem::exists( dataStoreDirectory ) )
	{
		// No cleanup needed
		return;
	}

	try
	{
		for( auto const& directoryEntry : std::filesystem::directory_iterator( dataStoreDirectory ) )
		{
			auto entryHash = dataStoreFileNameToHash( directoryEntry.path().filename().generic_string() );
			if( entryHash )
			{
				if( !usedDataHashes.count( *entryHash ) )
				{
					if( !isSave )
					{
						// If this is an export rather than a save, then the open script won't rely on
						// the old unused data, so we can go ahead and just remove it.
						// ( Otherwise we need to put it in a recycle bin in case we need this data
						// again after an undo. )
						std::filesystem::remove( directoryEntry.path() );
						continue;
					}

					// It's a little bit non-obvious whether it's safe to move this file while we have a
					// directory iterator, but the docs say about changing directory contents: "it is unspecified
					// whether the change would be observed through the iterator." Since they don't say
					// anything about the iterator becoming invalid, I guess this is fine.
					const std::filesystem::path recycledPath( directoryManager->acquireRecycleBin() / directoryEntry.path().filename() );

					if( std::filesystem::exists( recycledPath ) )
					{
						// We've already stored this in the recycle bin, so it's safe to just delete it
						std::filesystem::remove( directoryEntry.path() );
					}
					else
					{
						std::filesystem::rename( directoryEntry.path(), recycledPath );
					}
				}
			}
			else
			{
				if( directoryEntry.path().filename() != ".recycleBin" )
				{
					IECore::msg(
						IECore::Msg::Warning, "Serialisation",
						fmt::format( "Unexpected file {} in data store directory {}.",
							directoryEntry.path().filename(), dataStoreDirectory
						)
					);
				}
			}
		}
	}
	catch( IECore::Exception &e )
	{
		IECore::msg(
			IECore::Msg::Warning, "Serialisation",
			std::string( "Unable to clean up unused data stores : " ) + e.what()
		);
	}
}
