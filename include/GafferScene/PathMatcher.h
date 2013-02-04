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
		
		template<typename Iterator>
		PathMatcher( Iterator pathsBegin, Iterator pathsEnd );
		
		template<typename Iterator>
		void init( Iterator pathsBegin, Iterator pathsEnd );
	
		void clear();
		
		Filter::Result match( const std::string &path ) const;
		Filter::Result match( const std::vector<IECore::InternedString> &path ) const;
		
	private :

		typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
		typedef Tokenizer::iterator TokenIterator;
		struct Node;
		
		void addPath( const std::string &path );
		
		template<typename NameIterator>
		void matchWalk( Node *node, const NameIterator &start, const NameIterator &end, Filter::Result &result ) const;
		
		boost::shared_ptr<Node> m_root;
		
};
	
} // namespace GafferScene

#include "GafferScene/PathMatcher.inl"

#endif // GAFFER_PATHMATCHER_H
