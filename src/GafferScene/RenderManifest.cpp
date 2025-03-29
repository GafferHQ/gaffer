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

using namespace GafferScene;

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
	return m_map.insert( PathAndId( path, m_map.size() + 1 ) ).first->second;
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

std::optional<ScenePlug::ScenePath> RenderManifest::pathForId( uint32_t id ) const
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
			lock.upgrade_to_writer();
			result.push_back( m_map.insert( PathAndId( *pathIt, m_map.size() + 1 ) ).first->second );
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

void RenderManifest::readEXRManifest( const std::filesystem::path &filePath )
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

	Mutex::scoped_lock lock( m_mutex, /* write = */ true );
	m_map.clear();
	for( Imf::IDManifest::ChannelGroupManifest::ConstIterator i = idManifest.begin(); i != idManifest.end(); ++i )
	{
		m_map.insert( PathAndId( ScenePlug::stringToPath( i.text()[0] ), i.id() ) );
	}
}

void RenderManifest::writeEXRManifest( const std::filesystem::path &filePath ) const
{
	if( !boost::ends_with( filePath.generic_string(), ".exr" ) )
	{
		throw IECore::Exception( "Id manifest file path does not end in \".exr\": " + filePath.generic_string() );
	}

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
