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

#include "GafferScene/PathIdMap.h"

using namespace GafferScene;

PathIdMap::PathIdMap( bool threadsafe ) : m_threadsafe( threadsafe )
{
}

uint32_t PathIdMap::mapPath( const ScenePlug::ScenePath &path )
{
	std::optional<Mutex::scoped_lock> lock;
	if( m_threadsafe )
	{
		lock.emplace( m_mutex, /* write = */ false );
	}

	auto it = m_map.find( path );
	if( it != m_map.end() )
	{
		return it->second;
	}

	if( lock )
	{
		lock->upgrade_to_writer();
	}
	return m_map.insert( PathAndId( path, m_map.size() + 1 ) ).first->second;
}

void PathIdMap::insertPath( const ScenePlug::ScenePath &path, uint32_t id )
{
	std::optional<Mutex::scoped_lock> lock;
	if( m_threadsafe )
	{
		lock.emplace( m_mutex, /* write = */ true );
	}
	m_map.insert( PathAndId( path, id ) );
}

uint32_t PathIdMap::idForPath( const ScenePlug::ScenePath &path ) const
{
	std::optional<Mutex::scoped_lock> lock;
	if( m_threadsafe )
	{
		lock.emplace( m_mutex, /* write = */ false );
	}

	auto it = m_map.find( path );
	if( it != m_map.end() )
	{
		return it->second;
	}

	return 0;
}

std::optional<ScenePlug::ScenePath> PathIdMap::pathForId( uint32_t id ) const
{
	std::optional<Mutex::scoped_lock> lock;
	if( m_threadsafe )
	{
		lock.emplace( m_mutex, /* write = */ false );
	}

	auto &index = m_map.get<1>();
	auto it = index.find( id );
	if( it != index.end() )
	{
		return it->first;
	}
	return std::nullopt;
}

void PathIdMap::clear()
{
	m_map.clear();
}

size_t PathIdMap::size() const
{
	return m_map.size();
}
