//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
//      * Neither the name of Cinesite VFX Ltd. nor the names of
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
/////////////////////////////////////////////////////////////////////////

#include "Gaffer/Private/IECorePreview/Messages.h"

#include <algorithm>

using namespace IECorePreview;

void Message::hash( IECore::MurmurHash &h ) const
{
	h.append( level );
	h.append( context );
	h.append( message );
}

bool Message::operator == ( const Message &other ) const
{
	return level == other.level && context == other.context && message == other.message;
}

bool Message::operator != ( const Message &other ) const
{
	return !( *this == other );
}

Messages::Messages()
	: m_bucketSize( 100 )
{
	m_nextBucket.reserve( m_bucketSize );
	clear();
}

bool Messages::operator == ( const Messages &other ) const
{
	return m_hash == other.m_hash;
}

bool Messages::operator != ( const Messages &other ) const
{
	return !( *this == other );
}

void Messages::add( const Message &message )
{
	m_nextBucket.push_back( message );
	message.hash( m_hash );

	++m_counts[ int(message.level) ];

	if( m_nextBucket.size() == m_bucketSize )
	{
		const std::shared_ptr<const Bucket> b( new Bucket( std::move(m_nextBucket) ) );
		m_buckets.push_back( b );
		m_nextBucket.reserve( m_bucketSize );
	}
}

void Messages::clear()
{
	m_nextBucket.clear();
	m_buckets.clear();
	std::fill( m_counts.begin(), m_counts.end(), 0 );
	m_hash = IECore::MurmurHash();
}

size_t Messages::size() const
{
	return ( m_buckets.size() * m_bucketSize ) + m_nextBucket.size();
}

const Message& Messages::operator[]( size_t index ) const
{
	const size_t item = index % m_bucketSize;
	const size_t bucket = index / m_bucketSize;
	return bucket == m_buckets.size() ? m_nextBucket[ item ] : (*m_buckets[ bucket ])[ item ];
}

size_t Messages::count( const IECore::MessageHandler::Level &level ) const
{
	if( level == IECore::MessageHandler::Level::Invalid )
	{
		return 0;
	}

	return m_counts[ int(level) ];
}

std::optional<size_t> Messages::firstDifference( const Messages &other ) const
{
	if( size() == 0 )
	{
		return std::nullopt;
	}

	if( other.size() == 0 )
	{
		return 0;
	}

	// If a container is copied, then it will share full buckets
	// with the other container. As such, we can reverse iterate
	// the list of completed buckets looking for a match. If a later
	// bucket matches, then all the previous buckets must match,
	// so we can skip checking any messages in shared buckets.

	size_t comparisonStartIndex = 0;

	const size_t numComparableBuckets = std::min( m_buckets.size(), other.m_buckets.size() );
	if( numComparableBuckets > 0 )
	{
		for( size_t i = numComparableBuckets - 1; ; --i )
		{
			if( m_buckets[i] == other.m_buckets[i] )
			{
				comparisonStartIndex = ( i + 1 ) * m_bucketSize;
				break;
			}

			if( i == 0 ) { break; }
		}
	}

	// Now we've found the latest safe comparison start point, actually check messages
	const size_t numComparableMessages = std::min( size(), other.size() );
	for( size_t i = comparisonStartIndex; i < numComparableMessages; ++i )
	{
		if( (*this)[i] != other[i] )
		{
			return i;
		}
	}

	// No differences - only return the index if other has fewer messages
	if( numComparableMessages < size() )
	{
		return numComparableMessages;
	}

	return std::nullopt;
}

IECore::MurmurHash Messages::hash() const
{
	return m_hash;
}
