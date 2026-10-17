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

#include "boost/python.hpp"

#include "DataStoreBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ValuePlugBinding.h"

#include "Gaffer/DataStore.h"
#include "Gaffer/ScriptNode.h"

#include "boost/bind/placeholders.hpp"

#include "tbb/concurrent_hash_map.h"

#include "fmt/format.h"
#include "fmt/ranges.h"
#include "fmt/std.h"

using namespace boost::placeholders;
using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;


namespace
{

// Must match the definition in ScriptNode.cpp
const IECore::InternedString g_serialiserTargetFileContextName( "serialiser:targetFile" );

// For each Serialisation, store which DataStores have been serialised as part of that serialisation
using DataStoresMap = tbb::concurrent_hash_map< const Serialisation*, std::unique_ptr<std::set<const DataStore*> > >;
DataStoresMap g_serialisationDataStores;

} // namespace

namespace GafferModule
{

struct DataStorePostSerialisationSignalHandler
{
	DataStorePostSerialisationSignalHandler()
	{
		// Our handling of the postSerialisation signal is really part of the serialisation finishing.
		// It must always run ( so that the DataStoreSerialisationTracker instance gets cleaned up ),
		// and it could potentially fail ( if the user has done something naughty like deleting our
		// source data stores from disk ), in which case it will throw an exception, and this should
		// be treated the same as the serialisation being cancelled before we reach the postSerialisation
		// signal.
		// We don't yet have anything else using the postSerialisation signal, but if there is something
		// else, it should come after us, so we use a connectFront.
		GafferBindings::Serialisation::postSerialisationSignal().connectFront( &DataStorePostSerialisationSignalHandler::finishSerialisation );
	}

	static void finishSerialisation( const Serialisation *serialisation, bool success )
	{
		const std::string *targetPathString = Context::current()->getIfExists<std::string>( g_serialiserTargetFileContextName );
		if( !targetPathString )
		{
			return;
		}

		DataStoresMap::accessor mapEntry;
		g_serialisationDataStores.find( mapEntry, serialisation );

		std::unique_ptr< std::set<const DataStore*> > dataStoreForSerialisation;

		if( !mapEntry.empty() )
		{
			dataStoreForSerialisation = std::move( mapEntry->second );
			g_serialisationDataStores.erase( mapEntry );
		}

		if( success )
		{
			// A set of data store entry values, identified by their hashes, that have been saved
			// during this serialisation
			std::unordered_set< IECore::MurmurHash > usedDataHashes;

			if( dataStoreForSerialisation )
			{
				for( auto node : *dataStoreForSerialisation )
				{
					node->save( *targetPathString, serialisation->parent(), usedDataHashes );
				}
			}

			DataStore::finaliseDirectory( *targetPathString, serialisation->parent(), usedDataHashes );
		}
	}
};

class DataStoreSerialiser : public NodeSerialiser
{
	std::string postConstructor(
		const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation
	) const override
	{
		const DataStore *node = IECore::runTimeCast<const DataStore>( graphComponent );

		serialisation.addModule( "IECore" );

		// If we are saving to a file, as opposed to just doing a copy-and-paste, we rely on ScriptNode
		// setting this targetPath context variable
		const std::string *targetPathString = Context::current()->getIfExists<std::string>( g_serialiserTargetFileContextName );
		if( targetPathString )
		{
			std::filesystem::path targetPath = *targetPathString;

			DataStoresMap::accessor tracker;
			if( g_serialisationDataStores.emplace( tracker, &serialisation, nullptr ) )
			{
				tracker->second = std::make_unique< std::set<const DataStore*> >();
			}

			tracker->second->insert( node );
		}
		else
		{
			node->checkSaved();
		}

		std::vector<std::string> entryTokens;
		for( const auto &it : node->m_entries )
		{
			entryTokens.push_back( fmt::format( R"("{}" : IECore.MurmurHash("{}"))", it.first, it.second.m_hash.toString() ) );
		}
		std::string entriesRepr = fmt::format( "{{ {} }}", fmt::join( entryTokens, ", " ) );

		std::string mySerial;
		if( targetPathString )
		{
			mySerial = fmt::format(
				"{}._loadEntries( {} )\n", identifier, entriesRepr
			);
		}
		else
		{
			// If we're not saving out data stores with this serialisation, then we need to force a load
			// from the data store directory where the ScriptNode was last saved.
			const ScriptNode *scriptNode = graphComponent->ancestor<const ScriptNode>();
			if( !scriptNode )
			{
				throw IECore::Exception( "Cannot copy DataStore that is not part of a ScriptNode" );
			}

			mySerial = fmt::format(
				"{}._loadEntries( {}, {} )\n", identifier, entriesRepr,
				std::filesystem::path( scriptNode->fileNamePlug()->getValue() )
			);
		}

		return mySerial;
	}
};

struct DataStoreWrapperFunctionContainer
{
	static void loadEntriesWrapper(
		DataStore &dataStore, boost::python::dict pythonEntries, const std::string &loadFrom
	)
	{
		std::map< std::string, IECore::MurmurHash > entries;
		list items = list( pythonEntries.items() );
		for( int i = 0; i < len( items ); i++ )
		{
			boost::python::tuple entry = boost::python::extract<boost::python::tuple>( items[i] );
			std::string key = boost::python::extract<std::string>( entry[0] );
			IECore::MurmurHash hash = boost::python::extract<IECore::MurmurHash>( entry[1] );
			entries[ key ] = hash;
		}

		dataStore.loadEntries( entries, loadFrom );
	}
};

} // namespace GafferModule

namespace
{

GafferModule::DataStorePostSerialisationSignalHandler g_postSerialisationSignalHandler;

IECore::ObjectPtr getEntryWrapper( const DataStore &dataStore, const std::string &key, bool throwExceptions )
{
	IECore::ConstObjectPtr result = dataStore.getEntry( key, throwExceptions );
	if( result )
	{
		return result->copy();
	}
	else
	{
		return nullptr;
	}
}

} // namespace

void GafferModule::bindDataStore()
{

	scope s = DependencyNodeClass<DataStore>()
		.def( init<std::string>( ( arg( "name" )=GraphComponent::defaultName<DataStore>() ) ) )
		.def( "setEntry", &DataStore::setEntry )
		.def( "removeEntry", &DataStore::removeEntry )
		.def( "getEntry", &getEntryWrapper, ( arg_( "key" ), arg_( "throwExceptions" ) = true ) )
		.def( "isLive", &DataStore::isLive, ( arg_( "key" ) ) )
		.def( "_loadEntries", &DataStoreWrapperFunctionContainer::loadEntriesWrapper, ( arg( "entries" ), arg( "loadFrom") = "") )
	;

	Serialisation::registerSerialiser( Gaffer::DataStore::staticTypeId(), new DataStoreSerialiser );

}
