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

#include "GafferScene/RenderManifest.h"

#include "OpenEXR/ImfChannelList.h"
#include "OpenEXR/ImfFrameBuffer.h"
#include "OpenEXR/ImfHeader.h"
#include "OpenEXR/ImfIDManifest.h"
#include "OpenEXR/ImfIntAttribute.h"
#include "OpenEXR/ImfMultiPartInputFile.h"
#include "OpenEXR/ImfMultiPartOutputFile.h"
#include "OpenEXR/ImfOutputPart.h"
#include "OpenEXR/ImfPartType.h"
#include "OpenEXR/ImfStandardAttributes.h"

#include "boost/algorithm/string/predicate.hpp"

#include "boost/iostreams/stream.hpp"
#include "boost/property_tree/json_parser.hpp"

#include <regex>

using namespace GafferScene;

namespace
{

struct CacheKey
{
	CacheKey() {};
	CacheKey( IECore::ConstStringDataPtr loadedFromCryptomatteJSONStringData, std::string loadedFromFilePath, std::filesystem::file_time_type loadedFromFilePathModTime )
		: loadedFromCryptomatteJSONStringData( loadedFromCryptomatteJSONStringData ), loadedFromFilePath( loadedFromFilePath ), loadedFromFilePathModTime( loadedFromFilePathModTime )
	{
	}

	bool operator == ( const CacheKey &other ) const
	{
		if( other.loadedFromFilePath != loadedFromFilePath || other.loadedFromFilePathModTime != loadedFromFilePathModTime )
		{
			return false;
		}

		if( bool( other.loadedFromCryptomatteJSONStringData ) != bool( loadedFromCryptomatteJSONStringData ) )
		{
			return false;
		}

		if( ( !other.loadedFromCryptomatteJSONStringData ) && ( !loadedFromCryptomatteJSONStringData ) )
		{
			return true;
		}

		return other.loadedFromCryptomatteJSONStringData->isEqualTo( loadedFromCryptomatteJSONStringData.get() );
	}

	IECore::ConstStringDataPtr loadedFromCryptomatteJSONStringData;
	std::string loadedFromFilePath;
	std::filesystem::file_time_type loadedFromFilePathModTime;
};


struct CacheKeyHasher
{
	std::size_t operator()( const CacheKey &key ) const
	{
		IECore::MurmurHash h;
		// Don't want to hash the actual contents of what might be an extremely large string.
		// StringData's internal lazy-copy-on-write will mean that unmodified copies will share the
		// same address, so we hash that instead.
		h.append( reinterpret_cast<uintptr_t>( &key.loadedFromCryptomatteJSONStringData->readable() ) );
		h.append( key.loadedFromFilePath );
		h.append( key.loadedFromFilePathModTime.time_since_epoch().count() );
		return h.h1();
	}
};

tbb::spin_rw_mutex g_cacheMutex;
std::unordered_map< CacheKey, std::weak_ptr< RenderManifest >, CacheKeyHasher > g_cache;

} // namespace

RenderManifest::RenderManifest()
{
}

uint32_t RenderManifest::acquireID( const ScenePlug::ScenePath &path )
{
	Mutex::scoped_lock lock( m_mutex, /* write = */ false );

	auto it = m_map.find( path );
	if( it != m_map.end() )
	{
		return it->second;
	}

	lock.upgrade_to_writer();
	return m_map.insert( PathAndID( path, m_map.size() + 1 ) ).first->second;
}

uint32_t RenderManifest::idForPath( const ScenePlug::ScenePath &path ) const
{
	Mutex::scoped_lock lock( m_mutex, /* write = */ false );

	auto it = m_map.find( path );
	if( it != m_map.end() )
	{
		return it->second;
	}

	return 0;
}

std::optional<ScenePlug::ScenePath> RenderManifest::pathForID( uint32_t id ) const
{
	Mutex::scoped_lock lock( m_mutex, /* write = */ false );

	auto &index = m_map.get<1>();
	auto it = index.find( id );
	if( it != index.end() )
	{
		return it->first;
	}
	return std::nullopt;
}

std::vector<uint32_t> RenderManifest::acquireIDs( const IECore::PathMatcher &paths )
{
	Mutex::scoped_lock lock( m_mutex, /* write = */ false );

	std::vector<uint32_t> result;
	for( IECore::PathMatcher::Iterator pathIt = paths.begin(), eIt = paths.end(); pathIt != eIt; ++pathIt )
	{
		auto it = m_map.find( *pathIt );
		if( it != m_map.end() )
		{
			result.push_back( it->second );
		}
		else
		{
			// upgrade_to_writer() is specified to be a no-op if it's already been called.
			lock.upgrade_to_writer();
			result.push_back( m_map.insert( PathAndID( *pathIt, m_map.size() + 1 ) ).first->second );
		}
	}
	return result;
}

std::vector<uint32_t> RenderManifest::idsForPaths( const IECore::PathMatcher &paths ) const
{
	Mutex::scoped_lock lock( m_mutex, /* write = */ false );
	std::vector<uint32_t> result;
	result.reserve( paths.size() );
	for( IECore::PathMatcher::Iterator pathIt = paths.begin(), eIt = paths.end(); pathIt != eIt; ++pathIt )
	{
		auto it = m_map.find( *pathIt );
		if( it != m_map.end() )
		{
			result.push_back( it->second );
		}
	}
	return result;
}

IECore::PathMatcher RenderManifest::pathsForIDs( const std::vector<uint32_t> &ids ) const
{
	Mutex::scoped_lock lock( m_mutex, /* write = */ false );
	IECore::PathMatcher result;
	auto &index = m_map.get<1>();
	for( auto id : ids )
	{
		auto it = index.find( id );
		if( it != index.end() )
		{
			result.addPath( it->first );
		}
	}
	return result;
}

void RenderManifest::clear()
{
	Mutex::scoped_lock lock( m_mutex, /* write = */ true );
	m_map.clear();
}

size_t RenderManifest::size() const
{
	Mutex::scoped_lock lock( m_mutex, /* write = */ false );
	return m_map.size();
}

std::shared_ptr<const RenderManifest> RenderManifest::loadFromImageMetadata( const IECore::CompoundData *metadata, const std::string &cryptomatteLayerName )
{
	std::string sideCarManifestPath;
	bool isCryptomatte = false;
	IECore::ConstStringDataPtr cryptoManifestStringData;

	const IECore::StringData *filePathData = metadata->member<IECore::StringData>( "filePath" );
	const IECore::StringData *manifestFilePathData = metadata->member<IECore::StringData>( "gaffer:renderManifestFilePath" );
	if( manifestFilePathData )
	{
		std::filesystem::path rawManifestPath( manifestFilePathData->readable() );
		if( rawManifestPath.is_absolute() )
		{
			sideCarManifestPath = rawManifestPath.generic_string();
		}
		else
		{
			if( !filePathData )
			{
				throw IECore::Exception( "Can't find \"filePath\" metadata to locate relative manifest path. It should have been set by the ImageReader." );
			}
			sideCarManifestPath = ( std::filesystem::path( filePathData->readable() ).parent_path() / rawManifestPath ).generic_string();
		}
	}

	// If we couldn't find a manifest using the Gaffer convention, look for a Cryptomatte
	if( !sideCarManifestPath.size() )
	{
		static const std::regex g_cryptoNameRegex( R"((cryptomatte/[^/]{1,7})/name)" );

		for( auto &i : metadata->readable() )
		{
			std::smatch match;
			if( std::regex_match( i.first.string(), match, g_cryptoNameRegex ) )
			{
				const IECore::StringData *nameData = IECore::runTimeCast<IECore::StringData>( i.second.get() );

				if( !nameData || nameData->readable() != cryptomatteLayerName )
				{
					continue;
				}

				const std::string metadataPrefix = match.str( 1 );

				// Look for a valid Cryptomatte sidecar json.
				const IECore::StringData *cryptoManifestPathData = metadata->member<IECore::StringData>(
					fmt::format( "{}/manif_file", metadataPrefix )
				);

				if( cryptoManifestPathData )
				{
					if( !filePathData )
					{
						throw IECore::Exception( "Can't find \"filePath\" metadata to locate relative manifest path. It should have been set by the ImageReader." );
					}

					sideCarManifestPath = ( std::filesystem::path( filePathData->readable() ).parent_path() / cryptoManifestPathData->readable() ).generic_string();
					isCryptomatte = true;
				}
				else
				{
					// Didn't find a sidecar file, look for a manifest stored directly in the header
					cryptoManifestStringData = metadata->member<IECore::StringData>(
						fmt::format( "{}/manifest", metadataPrefix )
					);
				}
			}
		}
	}

	if( sideCarManifestPath == "" && !cryptoManifestStringData )
	{
		throw IECore::Exception( "No gaffer:renderManifestFilePath metadata or cryptomatte metadata found." );
	}

	if( cryptoManifestStringData )
	{

		// This copy should never actually result in the string being copied, because we don't modify it.
		CacheKey cacheKey( cryptoManifestStringData->copy(), "", std::filesystem::file_time_type() );

		Mutex::scoped_lock lock( g_cacheMutex, /* write = */ false );
		auto existing = g_cache.find( cacheKey );
		if( existing != g_cache.end() )
		{
			std::shared_ptr<RenderManifest> validPointer = existing->second.lock();
			if( validPointer )
			{
				return validPointer;
			}
		}


		const std::string &cryptoManifestString = cryptoManifestStringData->readable();
		boost::iostreams::stream<boost::iostreams::array_source> stream( cryptoManifestString.c_str(), cryptoManifestString.size() );

		std::shared_ptr<RenderManifest> result = std::make_shared<RenderManifest>();
		result->loadCryptomatteJSON( stream );

		lock.upgrade_to_writer();
		g_cache[ cacheKey ] = result;

		return result;

	}

	std::filesystem::file_time_type currentModTime;
	try
	{
		currentModTime = std::filesystem::last_write_time( sideCarManifestPath );
	}
	catch( std::exception &e )
	{
		throw IECore::Exception( std::string( "Could not find manifest file : " ) + sideCarManifestPath + " : " + e.what() );
	}


	CacheKey cacheKey( nullptr, sideCarManifestPath, currentModTime );

	Mutex::scoped_lock lock( g_cacheMutex, /* write = */ false );
	auto existing = g_cache.find( cacheKey );
	if( existing != g_cache.end() )
	{
		std::shared_ptr<RenderManifest> validPointer = existing->second.lock();
		if( validPointer )
		{
			return validPointer;
		}
	}


	std::shared_ptr<RenderManifest> result = std::make_shared<RenderManifest>();
	if( !isCryptomatte )
	{
		result->loadEXRManifest( sideCarManifestPath.c_str() );
	}
	else
	{
		std::ifstream stream( sideCarManifestPath.c_str() );
		result->loadCryptomatteJSON( stream );
	}

	lock.upgrade_to_writer();
	g_cache[ cacheKey ] = result;

	return result;
}

void RenderManifest::loadEXRManifest( const std::filesystem::path &filePath )
{
	Imf::MultiPartInputFile exrInput( filePath.generic_string().c_str() );
	int idManifestPart = -1;
	for( int part = 0; part < exrInput.parts (); part++ )
	{
		if( Imf::hasIDManifest( exrInput.header( part ) ) )
		{
			idManifestPart = part;
			break;
		}
	}

	if( idManifestPart == -1 )
	{
		throw IECore::Exception( "No manifest found" );
	}

	const Imf::Header header = exrInput.header( idManifestPart );

	const Imf::CompressedIDManifest& compressedManifest = Imf::idManifest( header );
	const Imf::IDManifest manifest( compressedManifest );
	const Imf::IDManifest::ChannelGroupManifest &idManifest = manifest[0];

	for( Imf::IDManifest::ChannelGroupManifest::ConstIterator i = idManifest.begin(); i != idManifest.end(); ++i )
	{
		m_map.insert( PathAndID( ScenePlug::stringToPath( i.text()[0] ), i.id() ) );
	}
}

void RenderManifest::writeEXRManifest( const std::filesystem::path &filePath ) const
{
	Imf::IDManifest::ChannelGroupManifest idManifest;
	// We're actually using this as a sidecar manifest ... there is no actual id pass in this exr. But if there
	// were, we would call it "id".
	idManifest.setChannel( "id" );

	// Each id corresponds to a single string, which is a path
	idManifest.setComponent( "path" );
	idManifest.setEncodingScheme( Imf::IDManifest::ID_SCHEME );
	idManifest.setHashScheme( Imf::IDManifest::NOTHASHED );
	idManifest.setLifetime( Imf::IDManifest::LIFETIME_FRAME );

	Mutex::scoped_lock lock( m_mutex, /* write = */ false );
	for( const auto &i : m_map )
	{
		idManifest.insert( i.second, ScenePlug::pathToString( i.first ) );
	}

	std::vector< Imf::Header > headers( 1 );

	Imath::Box2i window( Imath::V2i( 0 ), Imath::V2i( 30, 2 ) );

	headers[0].dataWindow() = window;
	headers[0].displayWindow() = window;
	headers[0].setType( Imf::SCANLINEIMAGE );
	headers[0].channels().insert( "id", Imf::Channel( Imf::FLOAT ) );

	Imf::IDManifest manifestContainer;
	manifestContainer.add( idManifest );
	Imf::addIDManifest( headers[0], manifestContainer );

	Imf::MultiPartOutputFile exrOutput( filePath.generic_string().c_str(), headers.data(), 1 );

	float image[93] = {
		1,1,0,0,0,1,1,0,1,1,0,0,0,1,0,0,1,1,1,0,1,1,1,0,0,1,1,0,1,1,1,
		1,1,1,0,1,0,1,0,1,0,1,0,0,1,0,0,1,1,0,0,1,1,0,0,0,1,0,0,0,1,0,
		1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,0,1,0,0,0,1,1,1,0,1,1,0,0,0,1,0
	};
	Imf::FrameBuffer outBuf;
	outBuf.insert (
		"id",
		Imf::Slice (
			Imf::FLOAT,
			(char*)image,
			sizeof( float ),
			sizeof( float ) * 31
		)
	);

	Imf::OutputPart outPart( exrOutput, 0 );
	outPart.setFrameBuffer( outBuf );
	outPart.writePixels( 3 );
}

void RenderManifest::loadCryptomatteJSON( std::istream &in )
{
	boost::property_tree::ptree pt;

	try
	{
		boost::property_tree::read_json( in, pt );
	}
	catch( const boost::property_tree::json_parser::json_parser_error &e )
	{
		throw IECore::Exception( fmt::format( "Error parsing manifest file: {}", e.what() ) );
	}

	static const std::regex instanceDataRegex( R"(^instance:[0-9a-f]+$)" );

	std::smatch match;
	for( auto &it : pt )
	{
		// NOTE: exclude locations starting with "instance:" under root
		if( std::regex_match( it.first, match, instanceDataRegex ) )
		{
			continue;
		}

		const std::string &hashString = it.second.data().c_str();
		uint32_t hash;
		auto [_unused, errorCode] = std::from_chars( hashString.data(), hashString.data() + hashString.size(), hash, 16 );
		if( errorCode != std::errc() )
		{
			throw IECore::Exception( fmt::format( "Expected hexadecimal while parsing manifest: {}", hashString ) );
		}

		m_map.insert( PathAndID( ScenePlug::stringToPath( it.first ), hash ) );
	}
}
