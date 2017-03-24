//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_STRINGALGO_INL
#define GAFFER_STRINGALGO_INL

#include <string.h>

namespace Gaffer
{

namespace Detail
{

inline bool matchInternal( const char * const ss, const char *pattern, bool multiple = false )
{
	char c;
	const char *s = ss;
	while( true )
	{
		// Each case either returns a result if it can determine one,
		// continues if the match is ok so far, or breaks if the match
		// has failed.
		switch( c = *pattern++ )
		{
			case '\0' :

				return *s == c;

			case '*' :

				if( *pattern == '\0' || ( multiple && *pattern == ' ' ) )
				{
					// optimisation for when pattern
					// ends with '*'.
					return true;
				}

				// general case - recurse.
				for( const char *rs = s; *rs != '\0'; ++rs )
				{
					if( matchInternal( rs, pattern, multiple ) )
					{
						return true;
					}
				}
				break;

			case '?' :

				if( *s++ != '\0' )
				{
					continue;
				}
				break;

			case '\\' :

				if( *pattern++ == *s++ )
				{
					continue;
				}
				break;

			case ' ' :

				if( multiple && *s == '\0' )
				{
					// Space terminates sub-patterns, so we've
					// found a match.
					return true;
				}
				// Fall through to default

			default :

				if( c == *s++ )
				{
					continue;
				}

		}

		// Match failed

		if( !multiple )
		{
			return false;
		}
		else
		{
			// Reset to start of string, and advance to next pattern.
			s = ss;
			while( c != ' ' )
			{
				if( c == '\0' )
				{
					return false;
				}
				c = *pattern++;
			}
		}
	}
}

} // namespace Detail

namespace StringAlgo
{

inline bool match( const std::string &string, const std::string &pattern )
{
	return match( string.c_str(), pattern.c_str() );
}

inline bool match( const char *s, const char *pattern )
{
	return Detail::matchInternal( s, pattern );
}

inline bool matchMultiple( const std::string &s, const MatchPattern &patterns )
{
	return matchMultiple( s.c_str(), patterns.c_str() );
}

inline bool matchMultiple( const char *s, const char *patterns )
{
	return Detail::matchInternal( s, patterns, /* multiple = */ true );
}

inline bool hasWildcards( const std::string &pattern )
{
	return hasWildcards( pattern.c_str() );
}

inline bool hasWildcards( const char *pattern )
{
	return pattern[strcspn( pattern, "*?\\" )];
}

template<typename Token, typename OutputIterator>
void tokenize( const std::string &s, const char separator, OutputIterator outputIterator )
{
	size_t index = 0, size = s.size();
	while( index < size )
	{
		const size_t prevIndex = index;
		index = s.find( separator, index );
		index = index == std::string::npos ? size : index;
		if( index > prevIndex )
		{
			*outputIterator++ = Token( s.c_str() + prevIndex, index - prevIndex );
		}
		index++;
	}
}

template<typename OutputContainer>
void tokenize( const std::string &s, const char separator, OutputContainer &outputContainer )
{
	tokenize<typename OutputContainer::value_type>( s, separator, std::back_inserter( outputContainer ) );
}

} // namespace StringAlgo

} // namespace Gaffer

#endif // GAFFER_STRINGALGO_INL
