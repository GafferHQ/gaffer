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

#include "GafferScene/PathMatcher.h"

using namespace std;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Supporting code
//////////////////////////////////////////////////////////////////////////

namespace GafferScene
{

namespace Detail
{

// wildcard matching function - basically fnmatch with a lot less gumph.
inline bool wildcardMatch( const char *s, const char *pattern )
{
	char c;
	while( true )
	{
		switch( c = *pattern++ )
		{
			case '\0' :
			
				return *s == c;
			
			case '*' :
			
				if( *pattern == '\0' )
				{
					// optimisation for when pattern
					// ends with '*'.
					return true;
				}
				
				// general case - recurse.
				while( *s != '\0' )
				{
					if( wildcardMatch( s, pattern ) )
					{
						return true;
					}
					s++;
				}
				return false;
				
			default :
		
				if( c != *s++ )
				{
					return false;
				} 
		}
	}
}

// we use this comparison for the multimap of child nodes - it's equivalent
// to std::less<string> except that it treats strings as equal if they
// have identical prefixes followed by a wildcard character in at least
// one. this allows us to use multimap::equal_range to find all the children
// that might match a given string.
struct Less
{
	
	bool operator() ( const std::string &s1, const std::string &s2 )
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
	
};

} // namespace Detail

} // namespace GafferScene

//////////////////////////////////////////////////////////////////////////
// Node implementation
//////////////////////////////////////////////////////////////////////////

struct PathMatcher::Node
{
	
	typedef std::multimap<std::string, Node *, Detail::Less> ChildMap;
	typedef ChildMap::const_iterator ChildMapIterator;
	typedef std::pair<ChildMapIterator, ChildMapIterator> ChildMapRange;
	
	Node()
		:	terminator( false ), ellipsis( 0 )
	{
	}
	
	// returns the child exactly matching name.
	Node *child( const std::string &name )
	{
		ChildMapRange range = m_children.equal_range( name );
		while( range.first != range.second )
		{
			if( range.first->first == name )
			{
				return range.first->second;
			}
			range.first++;
		}
		return 0;
	}
	
	// returns the range of children which /may/ match name
	// when wildcards are taken into account.
	ChildMapRange childRange( const std::string &name )
	{
		return m_children.equal_range( name );
	}
	
	~Node()
	{
		ChildMap::iterator it, eIt;
		for( it = m_children.begin(), eIt = m_children.end(); it != eIt; it++ )
		{
			delete it->second;
		}
		delete ellipsis;
	}
		
	bool terminator;
	// map of child nodes
	ChildMap m_children;
	// child node for "...". this is stored separately as it uses
	// a slightly different matching algorithm.
	Node *ellipsis;
	
};

//////////////////////////////////////////////////////////////////////////
// PathMatcher implementation
//////////////////////////////////////////////////////////////////////////

PathMatcher::PathMatcher()
{
}

void PathMatcher::clear()
{
	m_root = boost::shared_ptr<Node>( new Node );
}

Filter::Result PathMatcher::match( const std::string &path ) const
{
	Node *node = m_root.get();
	if( !node )
	{
		return Filter::NoMatch;
	}
	
	Filter::Result result = Filter::NoMatch;
	Tokenizer tokenizer( path, boost::char_separator<char>( "/" ) );	
	matchWalk( node, tokenizer.begin(), tokenizer.end(), result );
	return result;
}

Filter::Result PathMatcher::match( const std::vector<IECore::InternedString> &path ) const
{
   Node *node = m_root.get();
   if( !node )
   {
       return Filter::NoMatch;
   }

	Filter::Result result = Filter::NoMatch;
	matchWalk( node, path.begin(), path.end(), result );
	return result;
}

template<typename NameIterator>
void PathMatcher::matchWalk( Node *node, const NameIterator &start, const NameIterator &end, Filter::Result &result ) const
{
	// either we've matched to the end of the path
	if( start == end )
	{
		result = node->terminator ? Filter::Match : Filter::DescendantMatch;
		return;
	}
		
	// or we need to match the remainder of the path against child branches.
	Node::ChildMapRange range = node->childRange( *start );
	if( range.first != range.second )
	{
		NameIterator newStart = start; newStart++;
		for( Node::ChildMapIterator it = range.first; it != range.second; it++ )
		{
			if( Detail::wildcardMatch( start->c_str(), it->first.c_str() ) )
			{
				matchWalk( it->second, newStart, end, result );
				// if we've found a perfect match then we can terminate early,
				// but otherwise we need to keep going even though we may
				// have found a DescendantMatch already.
				if( result == Filter::Match )
				{
					return;
				}
			}
		}
	}
	
	if( node->ellipsis )
	{
		NameIterator newStart = start;
		while( newStart != end )
		{
			matchWalk( node->ellipsis, newStart, end, result );
			if( result == Filter::Match )
			{
				return;
			}
			newStart++;
		}
		result = node->ellipsis->terminator ? Filter::Match : Filter::DescendantMatch;
	}
}

void PathMatcher::addPath( const std::string &path )
{
	Node *node = m_root.get();
	Tokenizer tokenizer( path, boost::char_separator<char>( "/" ) );	
	Tokenizer::iterator it, eIt;
	for( it = tokenizer.begin(), eIt = tokenizer.end(); it != eIt; it++ )
	{
		Node *nextNode = 0;
		if( *it == "..." )
		{
			nextNode = node->ellipsis;
			if( !nextNode )
			{
				nextNode = new Node;
				node->ellipsis = nextNode;
			}
		}
		else
		{
			nextNode = node->child( *it );
			if( !nextNode )
			{
				nextNode = new Node;
				node->m_children.insert( pair<string, Node *>( *it, nextNode ) );
			}
		}
		node = nextNode;
	}
	node->terminator = true;
}
