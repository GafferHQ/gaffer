//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Cinesite VFX Ltd. nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "Gaffer/Export.h"

#include "IECore/MessageHandler.h"
#include "IECore/MurmurHash.h"

#include <array>
#include <optional>
#include <vector>

namespace IECorePreview
{

struct GAFFER_API Message
{
	Message( IECore::MessageHandler::Level l, const std::string &c, const std::string &m )
		:	level( l ), context( c ), message( m )
	{}

	IECore::MessageHandler::Level level;
	std::string context;
	std::string message;

	void hash( IECore::MurmurHash &h ) const;

	bool operator == ( const Message &other ) const;
	bool operator != ( const Message &other ) const;
};

/// Messages provides a cheap-to-copy container for messages as passed by the
/// IECore::MessageHandler. Once added, messages are immutable. Messages are stored
/// in such a way that copying an instance of the Messages container with a large
/// number of messages is orders of magnitude cheaper than copying the same
/// number of messages directly.
///
class GAFFER_API Messages
{
	public :

		Messages();
		Messages( const Messages &other ) = default;
		Messages &operator = ( const Messages &other ) = default;

		/// Equality implies all messages in the container are the same.
		bool operator == ( const Messages &other ) const;
		bool operator != ( const Messages &other ) const;

		void add( const Message &message );
		void clear();

		size_t size() const;

		const Message& operator[]( size_t index ) const;

		/// The number of messages of a specific severity
		/// Messages are counted when they are added, so this is cheap.
		size_t count( const IECore::MessageHandler::Level &level ) const;

		/// The index of the first message that differs to the messages in
		/// the other container. std::nullopt is returned if :
		///  - This container is empty.
		///  - This container's messages match those in others, and others
		///    is of equal or greater size.
		std::optional<size_t> firstDifference( const Messages &others ) const;

		/// The hash of all messages in the container.  Messages are hashed
		/// when they are added, so this is cheap.
		IECore::MurmurHash hash() const;

	private :

		// \todo The current implementation is naive and is sensitive to
		// bucketSize .vs. ingest/copy rate and total number of messages.
		//
		// Messages are stored in const buckets whose size is determined by the
		// m_bucketSize. Each bucket of messages is shared between all copies
		// of the container, so the copy cost is that of the pointers to the
		// full buckets themselves, rather than any of the messages. Only `size
		// % m_bucketSize` messages from the 'next' bucket are ever directly
		// copied.
		//
		// As such there is a trade-off between the expected number of
		// messages, and the rate of ingest .vs. copies. If the bucketSize is
		// much smaller than the total number of messages, then the cost of
		// copying the bucket list can become significant. If the bucket size
		// is too large, then the cost of copying messages for the next bucket
		// may be significant. There is much scope for improvement here.
		//
		size_t m_bucketSize;
		using Bucket = std::vector<Message>;

		Bucket m_nextBucket;
		std::vector<std::shared_ptr<const Bucket>> m_buckets;

		std::array<size_t, int(IECore::MessageHandler::Level::Invalid)> m_counts;

		IECore::MurmurHash m_hash;
};

} // IECorePreview
