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
	
	bool operator() ( const std::string &s1, const std::string &s2 ) const
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
	typedef ChildMap::iterator ChildMapIterator;
	typedef ChildMap::const_iterator ConstChildMapIterator;
	typedef std::pair<ChildMapIterator, ChildMapIterator> ChildMapRange;
	typedef std::pair<ConstChildMapIterator, ConstChildMapIterator> ConstChildMapRange;
	
	Node()
		:	terminator( false ), ellipsis( 0 )
	{
	}
	
	Node( const Node &other )
		:	terminator( other.terminator ), ellipsis( other.ellipsis ? new Node( *(other.ellipsis) ) : 0 )
	{
		ChildMapIterator hint = children.begin();
		for( ConstChildMapIterator it = other.children.begin(), eIt = other.children.end(); it != eIt; it++ )
		{
			hint = children.insert( hint, pair<string, Node *>( it->first, new Node( *(it->second) ) ) );
		}
	}

	~Node()
	{
		ChildMap::iterator it, eIt;
		for( it = children.begin(), eIt = children.end(); it != eIt; it++ )
		{
			delete it->second;
		}
		delete ellipsis;
	}
	
	ChildMapIterator childIterator( const std::string &name )
	{
		ChildMapRange range = children.equal_range( name );
		while( range.first != range.second )
		{
			if( range.first->first == name )
			{
				return range.first;
			}
			range.first++;
		}
		return children.end();
	}
	
	ConstChildMapIterator childIterator( const std::string &name ) const
	{
		ConstChildMapRange range = children.equal_range( name );
		while( range.first != range.second )
		{
			if( range.first->first == name )
			{
				return range.first;
			}
			range.first++;
		}
		return children.end();
	}
	
	// returns the child exactly matching name.
	Node *child( const std::string &name )
	{
		ChildMapIterator it = childIterator( name );
		if( it != children.end() )
		{
			return it->second;
		}
		return 0;
	}
	
	// returns the range of children which /may/ match name
	// when wildcards are taken into account.
	ChildMapRange childRange( const std::string &name )
	{
		return children.equal_range( name );
	}
	
	ConstChildMapRange childRange( const std::string &name ) const
	{
		return children.equal_range( name );
	}
	
	bool operator == ( const Node &other ) const
	{
		if( terminator != other.terminator )
		{
			return false;
		}
		
		if( children.size() != other.children.size() )
		{
			return false;
		}
		
		for( ConstChildMapIterator it = children.begin(), eIt = children.end(); it != eIt; it++ )
		{
			ConstChildMapIterator oIt = other.childIterator( it->first );
			if( oIt == other.children.end() )
			{
				return false;
			}
			if( !(*(it->second) == *(oIt->second) ) )
			{
				return false;
			}
		}
		
		if( (bool)ellipsis != (bool)other.ellipsis )
		{
			return false;
		}
		else if( ellipsis )
		{
			if( (*ellipsis) != (*other.ellipsis) )
			{
				return false;
			}
		}
		
		return true;
	}
	
	bool operator != ( const Node &other )
	{
		return !( *this == other );
	}
			
	bool terminator;
	// map of child nodes
	ChildMap children;
	// child node for "...". this is stored separately as it uses
	// a slightly different matching algorithm.
	Node *ellipsis;
	
};

//////////////////////////////////////////////////////////////////////////
// PathMatcher implementation
//////////////////////////////////////////////////////////////////////////

PathMatcher::PathMatcher()
{
	m_root = boost::shared_ptr<Node>( new Node );
}

PathMatcher::PathMatcher( const PathMatcher &other )
{
	m_root = boost::shared_ptr<Node>( new Node( *(other.m_root) ) );
}

void PathMatcher::clear()
{
	m_root = boost::shared_ptr<Node>( new Node );
}

void PathMatcher::paths( std::vector<std::string> &paths ) const
{
	pathsWalk( m_root.get(), "/", paths );
}

bool PathMatcher::operator == ( const PathMatcher &other ) const
{
	return *m_root == *other.m_root;
}

bool PathMatcher::operator != ( const PathMatcher &other ) const
{
	return !(*this == other );
}

unsigned PathMatcher::match( const std::string &path ) const
{
	unsigned result = Filter::NoMatch;
	Tokenizer tokenizer( path, boost::char_separator<char>( "/" ) );	
	matchWalk( m_root.get(), tokenizer.begin(), tokenizer.end(), result );
	return result;
}

unsigned PathMatcher::match( const std::vector<IECore::InternedString> &path ) const
{
   Node *node = m_root.get();
   if( !node )
   {
       return Filter::NoMatch;
   }

	unsigned result = Filter::NoMatch;
	matchWalk( node, path.begin(), path.end(), result );
	return result;
}

template<typename NameIterator>
void PathMatcher::matchWalk( Node *node, const NameIterator &start, const NameIterator &end, unsigned &result ) const
{
	// see if we've matched to the end of the path, and terminate the recursion if we have.
	if( start == end )
	{
		if( node->terminator )
		{
			result |= Filter::ExactMatch;
		}
		if( node->children.size() ) 
		{
			result |= Filter::DescendantMatch;
		}
		if( node->ellipsis )
		{
			result |= Filter::DescendantMatch;
			if( node->ellipsis->terminator )
			{
				result |= Filter::ExactMatch;
			}
		}
		return;
	}
		
	// we haven't matched to the end of the path - there are still path elements
	// to check. if this node is a terminator then we have found an ancestor match
	// though.
	if( node->terminator )
	{
		result |= Filter::AncestorMatch;
	}
	
	// now we can match the remainder of the path against child branches to see
	// if we have any exact or descendant matches.
	Node::ChildMapRange range = node->childRange( *start );
	if( range.first != range.second )
	{
		NameIterator newStart = start; newStart++;
		for( Node::ChildMapIterator it = range.first; it != range.second; it++ )
		{
			if( Detail::wildcardMatch( start->c_str(), it->first.c_str() ) )
			{
				matchWalk( it->second, newStart, end, result );
				// if we've found every kind of match then we can terminate early,
				// but otherwise we need to keep going even though we may
				// have found some of the match types already.
				if( result == Filter::EveryMatch )
				{
					return;
				}
			}
		}
	}
	
	if( node->ellipsis )
	{
		result |= Filter::DescendantMatch;
		if( node->ellipsis->terminator )
		{
			result |= Filter::ExactMatch;
		}
		
		NameIterator newStart = start;
		while( newStart != end )
		{
			matchWalk( node->ellipsis, newStart, end, result );
			if( result == Filter::EveryMatch )
			{
				return;
			}
			newStart++;
		}		
	}
}

bool PathMatcher::addPath( const std::string &path )
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
				node->children.insert( pair<string, Node *>( *it, nextNode ) );
			}
		}
		node = nextNode;
	}
	
	bool result = !node->terminator;
	node->terminator = true;
	return result;
}

bool PathMatcher::removePath( const std::string &path )
{
	bool result = false;
	Tokenizer tokenizer( path, boost::char_separator<char>( "/" ) );	
	removeWalk( m_root.get(), tokenizer.begin(), tokenizer.end(), result );
	return result;
}

void PathMatcher::removeWalk( Node *node, const TokenIterator &start, const TokenIterator &end, bool &removed )
{
	if( start == end )
	{
		// we've found the end of the path we wish to remove.
		if( node->terminator )
		{
			node->terminator = false;
			removed = true;
		}
		return;
	}

	Node::ChildMapIterator childIt = node->children.end();
	Node *childNode = 0;
	if( *start == "..." )
	{
		childNode = node->ellipsis;
	}
	else
	{
		childIt = node->childIterator( *start );
		if( childIt != node->children.end() )
		{
			childNode = childIt->second;
		}
	}
	
	if( !childNode )
	{
		return;
	}	
	
	TokenIterator childStart = start; childStart++;
	removeWalk( childNode, childStart, end, removed );
	if( !childNode->terminator && !childNode->ellipsis && !childNode->children.size() )
	{
		delete childNode;
		if( childIt != node->children.end() )
		{
			node->children.erase( childIt );
		}
		else
		{
			node->ellipsis = 0;
		}
	}
}

void PathMatcher::pathsWalk( Node *node, const std::string &path, std::vector<std::string> &paths ) const
{
	if( node->terminator )
	{
		paths.push_back( path );
	}
	
	for( Node::ChildMapIterator it = node->children.begin(), eIt = node->children.end(); it != eIt; it++ )
	{
		std::string childPath = path;
		if( node != m_root.get() )
		{
			childPath += "/";
		}
		childPath += it->first;
		pathsWalk( it->second, childPath, paths );			
	}

	if( node->ellipsis )
	{
		std::string childPath = path;
		if( node != m_root.get() )
		{
			childPath += "/";
		}
		childPath += "...";
		pathsWalk( node->ellipsis, childPath, paths );			
		
	}
}
