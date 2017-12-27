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

#include "Gaffer/Export.h"

namespace Gaffer
{

namespace StringAlgo
{

/// A type which can be used to store a pattern to be matched against.
/// Note that the match() function can actually operate on other string
/// types as well so the use of this type is purely optional. The main
/// reason to use a MatchPattern is documentation - by including it in a function
/// signature, the use of an argument can be made more obvious.
///
/// Patterns support the following syntax, which is
/// based on shell glob expressions :
///
/// - "*", which matches any sequence of characters
/// - "?", which matches any single character
/// - "\", which escapes a subsequent wildcard
/// - [ABC], which matches any single character from the specified set
/// - [A-Z], which matches any single character from the specified range
/// - [!ABC], which matches any character not in the specified set
/// - [!A-Z], which matches any character not in the specified range
GAFFER_API typedef std::string MatchPattern;

/// Returns true if the string matches the pattern and false otherwise.
GAFFER_API inline bool match( const std::string &s, const MatchPattern &pattern );
GAFFER_API inline bool match( const char *s, const char *pattern );

/// As above, but considering multiple patterns, separated by spaces.
GAFFER_API inline bool matchMultiple( const std::string &s, const MatchPattern &patterns );
GAFFER_API inline bool matchMultiple( const char *s, const char *patterns );

/// Returns true if the specified pattern contains characters which
/// have special meaning to the match() function.
GAFFER_API inline bool hasWildcards( const MatchPattern &pattern );
GAFFER_API inline bool hasWildcards( const char *pattern );

/// Returns the numeric suffix from the end of s, if one exists, and -1 if
/// one doesn't. If stem is specified then it will be filled with the contents
/// of s preceding the suffix, or the whole of s if no suffix exists.
GAFFER_API int numericSuffix( const std::string &s, std::string *stem = nullptr );
/// As above, but returns defaultSuffix in the case that no suffix exists.
GAFFER_API int numericSuffix( const std::string &s, int defaultSuffix, std::string *stem = nullptr );

/// Splits the input string wherever the separator is found, outputting all non-empty tokens
/// in sequence. Note that this is significantly quicker than boost::tokenizer
/// where TokenType is IECore::InternedString.
template<typename TokenType, typename OutputIterator>
GAFFER_API void tokenize( const std::string &s, const char separator, OutputIterator outputIterator );
template<typename OutputContainer>
GAFFER_API void tokenize( const std::string &s, const char separator, OutputContainer &outputContainer );

} // namespace StringAlgo

} // namespace Gaffer

#include "Gaffer/StringAlgo.inl"

#endif // GAFFER_STRINGALGO_H
