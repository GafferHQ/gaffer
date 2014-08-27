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

#ifndef GAFFER_STRINGALGO_H
#define GAFFER_STRINGALGO_H

#include <string>

namespace Gaffer
{

/// A type which can be used to store a pattern to be matched against.
/// Note that the match() function can actually operate on other string
/// types as well so the use of this type is purely optional. The main
/// reason to use a MatchPattern is documentation - by including it in a function
/// signature, the use of an argument can be made more obvious.
///
/// Patterns currently support only the "*" wildcard, which matches any
/// sequence of characters.
typedef std::string MatchPattern;

/// Returns true if the string matches the pattern and false otherwise.
inline bool match( const std::string &s, const MatchPattern &pattern );
inline bool match( const char *s, const char *pattern );

/// As above, but considering multiple patterns, separated by spaces.
inline bool matchMultiple( const std::string &s, const MatchPattern &patterns );
inline bool matchMultiple( const char *s, const char *patterns );

/// A comparison function for strings, equivalent to std::less<> except
/// that strings are treated as equal if they have identical prefixes followed
/// by a wildcard character in at least one. This allows searches to be performed
/// to quickly find all patterns that potentially match a given string. See the
/// GafferScene::PathMatcher class for an example where this is used in conjunction
/// with std::multimap and equal_range() to perform rapid matching against multiple
/// patterns.
struct MatchPatternLess
{

	inline bool operator() ( const MatchPattern &s1, const MatchPattern &s2 ) const;

};

/// Returns the numeric suffix from the end of s, if one exists, and -1 if
/// one doesn't. If stem is specified then it will be filled with the contents
/// of s preceding the suffix, or the whole of s if no suffix exists.
int numericSuffix( const std::string &s, std::string *stem = NULL );
/// As above, but returns defaultSuffix in the case that no suffix exists.
int numericSuffix( const std::string &s, int defaultSuffix, std::string *stem = NULL );

} // namespace Gaffer

#include "Gaffer/StringAlgo.inl"

#endif // GAFFER_STRINGALGO_H
