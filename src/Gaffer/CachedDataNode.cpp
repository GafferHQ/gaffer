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

#include "Gaffer/CachedDataNode.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/ValuePlug.h"

#include "IECore/NullObject.h"
#include "IECore/FileIndexedIO.h"

#include "boost/bind/bind.hpp"

#include <regex>

using namespace Gaffer;

namespace {

static const IECore::InternedString g_cacheEvaluationKeyName( "__cacheEvaluationKey" );

} // namespace

class CachedDataNode::SetEntryAction : public Gaffer::Action
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::CachedDataNode::SetEntryAction, SetEntryActionTypeId, Gaffer::Action );

		SetEntryAction( CachedDataNodePtr node, const IECore::InternedString &key, IECore::ConstObjectPtr value )
			: m_node( node ), m_key( key ), m_doValue( { value->hash(), value } )
		{
			auto it = node->m_caches.find( key );
			if( it != node->m_caches.end() )
			{
				m_undoValue = it->second;
			}
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
		}

		void undoAction() override
		{
			Action::undoAction();
			m_node->setEntryInternal( m_key, m_undoValue );
		}

		bool canMerge( const Action *other ) const override
		{
			if( !Action::canMerge( other ) )
			{
				return false;
			}
			const SetEntryAction *setEntryAction = IECore::runTimeCast<const SetEntryAction>( other );
			return setEntryAction && setEntryAction->m_node == m_node && setEntryAction->m_key == m_key;
		}

		void merge( const Action *other ) override
		{
			const SetEntryAction *setEntryAction = static_cast<const SetEntryAction *>( other );
			m_doValue = setEntryAction->m_doValue;
		}

	private :

		CachedDataNodePtr m_node;
		IECore::InternedString m_key;
		CacheEntry m_doValue;
		CacheEntry m_undoValue;

};

IE_CORE_DEFINERUNTIMETYPED( CachedDataNode::SetEntryAction );


GAFFER_NODE_DEFINE_TYPE( CachedDataNode );

size_t CachedDataNode::g_firstPlugIndex = 0;

CachedDataNode::CachedDataNode(
		const std::string &name,
		const std::string &sourceDirectory, IECore::ConstCompoundDataPtr caches
)
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new BoolPlug( "enabledPlug", Plug::In, true ) );
	addChild( new StringPlug( "selector", Plug::In ) );
	addChild( new StringPlug( "targetDirectory", Plug::In, "TODO${fileName}" ) );
	addChild( new CompoundObjectPlug( "data", Plug::Out ) );
	addChild( new StringVectorDataPlug( "keys", Plug::Out ) );
	addChild( new IntPlug( "refreshCount", Plug::In ) );
	addChild( new ObjectPlug( "evaluate", Plug::Out, new IECore::NullObject() ) );

	// TODO - force load if sourceDirectory doesn't match
	m_directory = sourceDirectory;
	if( caches )
	{
		for( const auto &it : caches->readable() )
		{
			IECore::StringData *stringVal = IECore::runTimeCast<IECore::StringData>( it.second.get() );
			if( !stringVal )
			{
				throw IECore::Exception( "BAD STRINGVAL TODO" );
			}
			m_caches[ it.first ] = { IECore::MurmurHash::fromString( stringVal->readable() ), nullptr };

			//std::cerr << "FILE MAP " << it.first << " : " << stringVal->readable() << "\n";
		}
	}
}

CachedDataNode::~CachedDataNode()
{
}

BoolPlug *CachedDataNode::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 0 );
}

const BoolPlug *CachedDataNode::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 0 );
}

StringPlug *CachedDataNode::selectorPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *CachedDataNode::selectorPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

StringPlug *CachedDataNode::targetDirectoryPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const StringPlug *CachedDataNode::targetDirectoryPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

CompoundObjectPlug *CachedDataNode::dataPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3 );
}

const CompoundObjectPlug *CachedDataNode::dataPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3 );
}

StringVectorDataPlug *CachedDataNode::keysPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
}

const StringVectorDataPlug *CachedDataNode::keysPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
}

IntPlug *CachedDataNode::refreshCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

const IntPlug *CachedDataNode::refreshCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

ObjectPlug *CachedDataNode::evaluatePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 6 );
}

const ObjectPlug *CachedDataNode::evaluatePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 6 );
}

void CachedDataNode::save( const std::filesystem::path &directory, boost::unordered_set<IECore::MurmurHash> &usedHashes, std::string &warning ) const
{
	// TODO - weird things happen if exceptions occur during serialization

	std::filesystem::create_directories( directory );

	for( auto &cache : m_caches )
	{
		if( !usedHashes.insert( cache.second.m_hash ).second )
		{
			// This value was already saved during this serialization
			continue;
		}

		std::string fileName = cacheFileNameFromHash( cache.second.m_hash );
		std::filesystem::path destPath = directory / fileName;
		if( std::filesystem::exists( destPath ) )
		{
			// This value was already saved during a previous serialization
			continue;
		}

		if( m_directory != directory )
		{
			std::filesystem::path sourcePath = m_directory / fileName;
			if( std::filesystem::exists( sourcePath ) )
			{
				// This value already exists on disk, but in a different directory.
				// Try to hardlink to it.
				std::error_code ec;
				std::filesystem::create_hard_link( sourcePath, destPath, ec );
				if( ec )
				{
					if( !warning.size() )
					{
						warning = fmt::format( "While saving \"{}\", could not create hardlink at \"{}\" pointing to \"{}\", falling back to copying file.", fullName(), destPath.string(), sourcePath.string() );
					}
					// If that fails, just copy.
					std::filesystem::copy_file( sourcePath, destPath );
				}
				continue;
			}
		}

		// This value does not yet exist on disk, and we need to write it.

		if( !cache.second.m_value )
		{
			throw IECore::Exception( fmt::format( "Unable to save entry \"{}\" on \"{}\" - no live value, but cannot find on disk.", cache.first, fullName() ) );
		}
		IECore::FileIndexedIOPtr file = new IECore::FileIndexedIO( destPath, IECore::IndexedIO::rootPath, IECore::IndexedIO::Exclusive | IECore::IndexedIO::Write);

		cache.second.m_value->save( file, "object" );

	}

	// Caches successfully written to target directory. Update so that we'll now read the disk caches
	// instead of needing to hold live values.
	m_directory = directory;
	for( auto &cache : m_caches )
	{
		cache.second.m_value.reset();
	}

}

std::string CachedDataNode::cacheFileNameFromHash( const IECore::MurmurHash &h )
{
	return h.toString() + ".io";
}

std::optional<IECore::MurmurHash> CachedDataNode::cacheFileNameToHash( const std::string &fileName )
{
	static const std::regex g_cacheFileNameRegex( R"(([0-9a-f]{32}).io)" );

	std::smatch match;
	if( std::regex_match( fileName, match, g_cacheFileNameRegex ) )
	{
		return IECore::MurmurHash::fromString( match.str( 1 ) );
	}

	return {};
}

std::filesystem::path CachedDataNode::sourceDirectory() const
{
	return m_directory;
}

std::filesystem::path CachedDataNode::recycleBinForDirectory( const std::filesystem::path &cacheDir )
{
	return cacheDir / ".recycleBin";
}

void CachedDataNode::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == refreshCountPlug()
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
		outputs.push_back( dataPlug() );
	}
}

void CachedDataNode::setEntry( const IECore::InternedString &key, IECore::ConstObjectPtr value )
{
	// TODO - reevaluate use of mutex
	//tbb::spin_rw_mutex::scoped_lock lock( m_mutex, /* write = */ true );

	// Ignore setEntry calls if it matches the existing value
	auto it = m_caches.find( key );
	if( it != m_caches.end() && it->second.m_hash == value->hash() )
	{
		return;
	}

	Action::enact( new SetEntryAction( this, key, value ) );
}

void CachedDataNode::setEntryInternal( const IECore::InternedString &key, std::optional<CacheEntry> value )
{
	if( value )
	{
		m_caches[key] = *value;
	}
	else
	{
		m_caches.erase( key );
	}
	refreshCountPlug()->setValue( refreshCountPlug()->getValue() + 1 );
}

IECore::ConstObjectPtr CachedDataNode::getEntry( const IECore::InternedString &key, bool throwExceptions ) const
{
	try
	{
		// We use an evaluation plug to provide the getEntry() functionality - this means we can
		// use Gaffer's default plug cache to ensure that we don't load a file twice if it is
		// queried both via getEntry and via an output plug.
		Context::EditableScope s( Context::current() );
		s.set( g_cacheEvaluationKeyName, &key );
		return evaluatePlug()->getValue();
	}
	catch( ... )
	{
		if( throwExceptions )
		{
			throw;
		}
		else
		{
			return nullptr;
		}
	}
}

bool CachedDataNode::hasLiveEntries() const
{
	for( auto &cache : m_caches )
	{
		if( cache.second.m_value )
		{
			return true;
		}
	}

	return false;
}

std::map<IECore::InternedString, IECore::MurmurHash> CachedDataNode::entryHashes() const
{
	std::map<IECore::InternedString, IECore::MurmurHash> result;
	for( auto &cache : m_caches )
	{
		result[cache.first] = cache.second.m_hash;
	}

	return result;
}

void CachedDataNode::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	if( output == evaluatePlug() )
	{
		ComputeNode::hash( output, context, h );

		const IECore::InternedString &key = context->get<IECore::InternedString>( g_cacheEvaluationKeyName );

		tbb::spin_rw_mutex::scoped_lock lock( m_mutex, /* write = */ false );
		auto it = m_caches.find( key );
		if( it == m_caches.end() )
		{
			throw IECore::Exception( "Unknown key: " + key.string() );
		}

		h = it->second.m_hash;
		return;
	}
	else if( output == dataPlug() )
	{
		Context::EditableScope s( context );
		IECore::InternedString select = selectorPlug()->getValue();
		s.set( g_cacheEvaluationKeyName, &select );

		// TODO
		h = IECore::MurmurHash();
		evaluatePlug()->hash( h );
	}
	else if( output == keysPlug() )
	{
		ComputeNode::hash( output, context, h );

		tbb::spin_rw_mutex::scoped_lock lock( m_mutex, /* write = */ false );
		for( const auto &i : m_caches )
		{
			h.append( i.first );
		}
	}


	ComputeNode::hash( output, context, h );
}

void CachedDataNode::compute( ValuePlug *output, const Context *context ) const
{
	if( output == evaluatePlug() )
	{
		IECore::ConstObjectPtr result;
		const IECore::InternedString &key = context->get<IECore::InternedString>( g_cacheEvaluationKeyName );

		tbb::spin_rw_mutex::scoped_lock lock( m_mutex, /* write = */ false );
		auto it = m_caches.find( key );
		if( it == m_caches.end() )
		{
			throw IECore::Exception( "Unknown key: " + key.string() );
		}

		if( it->second.m_value )
		{
			result = it->second.m_value;
		}
		else
		{
			auto cacheIt = m_caches.find( key );
			if( cacheIt != m_caches.end() )
			{
				std::string cacheFileName = cacheFileNameFromHash( cacheIt->second.m_hash );

				IECore::FileIndexedIOPtr file;
				if( IECore::FileIndexedIO::canRead( m_directory / cacheFileName ) )
				{
					file = new IECore::FileIndexedIO(
						m_directory / cacheFileName, IECore::IndexedIO::rootPath, IECore::IndexedIO::Read
					);
				}
				else if( IECore::FileIndexedIO::canRead( recycleBinForDirectory( m_directory / cacheFileName ) ) )
				{
					file = new IECore::FileIndexedIO(
						recycleBinForDirectory( m_directory / cacheFileName ), IECore::IndexedIO::rootPath, IECore::IndexedIO::Read
					);
				}
				else
				{
					throw IECore::Exception( "Could not locate cache file " + cacheFileName );
				}

				// TODO TODO TODO
				// look in recycle bin if necessary ( also when saving )

				result = IECore::Object::load( file, "object" );
			}
		}

		if( !result )
		{
			throw IECore::Exception( "Unknown key: " + key.string() );
		}

		static_cast<ObjectPlug *>( output )->setValue( result );
		return;

	}
	else if( output == dataPlug() )
	{
		Context::EditableScope s( context );
		IECore::InternedString select = selectorPlug()->getValue();
		s.set( g_cacheEvaluationKeyName, &select );

		IECore::ConstCompoundObjectPtr typedValue = IECore::runTimeCast<const IECore::CompoundObject>( evaluatePlug()->getValue() );
		if( !typedValue )
		{
			throw IECore::Exception( "BAD CACHE COMPUTE : " + std::string( evaluatePlug()->getValue()->typeName() ) );
		}

		// TODO - why is this compound instead of just Object?
		static_cast<CompoundObjectPlug *>( output )->setValue(
			IECore::runTimeCast<const IECore::CompoundObject>( evaluatePlug()->getValue() )
		);
		return;
	}
	else if( output == keysPlug() )
	{
		std::vector<std::string> keys;

		tbb::spin_rw_mutex::scoped_lock lock( m_mutex, /* write = */ false );

		for( const auto &i : m_caches )
		{
			keys.push_back( i.first );
		}

		// TODO - sort unnecessary?
		// TODO - should this be InternedStringVectorData?
		std::sort( keys.begin(), keys.end() );

		static_cast<StringVectorDataPlug *>( output )->setValue(
			new IECore::StringVectorData( std::move( keys ) )
		);
		return;
	}

	ComputeNode::compute( output, context );
}
