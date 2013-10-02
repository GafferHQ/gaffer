//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_PATHMATCHER_H
#define GAFFER_PATHMATCHER_H

#include "boost/shared_ptr.hpp"

#include "IECore/TypedData.h"

#include "GafferScene/Filter.h"

namespace GafferScene
{

/// The PathMatcher class provides an acceleration structure for matching
/// paths against a sequence of reference paths. It provides the internal
/// implementation for the PathFilter.
class PathMatcher
{

	public :
	
		PathMatcher();
		/// Constructs a deep copy of other.
		PathMatcher( const PathMatcher &other );
		
		template<typename Iterator>
		PathMatcher( Iterator pathsBegin, Iterator pathsEnd );
		
		/// \todo Should this keep the existing tree in place,
		/// but just remove the terminator flags on any items
		/// not present in the new paths? This might give
		/// better performance for selections and expansions
		/// which will tend to be adding and removing the same
		/// paths repeatedly.
		template<typename Iterator>
		void init( Iterator pathsBegin, Iterator pathsEnd );

		/// Returns true if the path was added, false if
		/// it was already there.
		bool addPath( const std::string &path );
		/// Returns true if the path was removed, false if
		/// it was not there.
		bool removePath( const std::string &path );
	
		void clear();
		
		/// Fills the paths container with all the paths held
		/// within this matcher.
		void paths( std::vector<std::string> &paths ) const;
		
		/// Result is a bitwise or of the relevant values
		/// from Filter::Result.
		unsigned match( const std::string &path ) const;
		unsigned match( const std::vector<IECore::InternedString> &path ) const;
		
		bool operator == ( const PathMatcher &other ) const;
		bool operator != ( const PathMatcher &other ) const;
		
	private :

		typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
		typedef Tokenizer::iterator TokenIterator;
		struct Node;
		
		void removeWalk( Node *node, const TokenIterator &start, const TokenIterator &end, bool &removed );
		void pathsWalk( Node *node, const std::string &path, std::vector<std::string> &paths ) const;

		template<typename NameIterator>
		void matchWalk( Node *node, const NameIterator &start, const NameIterator &end, unsigned &result ) const;
		
		boost::shared_ptr<Node> m_root;
		
};
	
} // namespace GafferScene

#include "GafferScene/PathMatcher.inl"

#endif // GAFFER_PATHMATCHER_H
