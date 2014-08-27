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
				while( *s != '\0' )
				{
					if( matchInternal( s, pattern, multiple ) )
					{
						return true;
					}
					s++;
				}
				return false;

			default :

				if( c == *s )
				{
					s++;
				}
				else if( !multiple )
				{
					return false;
				}
				else
				{
					if( c == ' ' && *s == '\0' )
					{
						// space terminates sub-patterns, so we've
						// found a match.
						return true;
					}
					else
					{
						// no match in this pattern. reset to start
						// of string, and advance to next pattern.
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
	}
}

} // namespace Detail

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

inline bool MatchPatternLess::operator() ( const std::string &s1, const std::string &s2 ) const
{
	register const char *c1 = s1.c_str();
	register const char *c2 = s2.c_str();

	while( *c1 == *c2 && *c1 )
	{
		c1++; c2++;
	}

	if( *c1 == '*' || *c2 == '*' )
	{
		return false;
	}

	return *c1 < *c2;
}

} // namespace Gaffer

#endif // GAFFER_STRINGALGO_INL
