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

#include "Gaffer/StringAlgo.h"

#include "GafferScene/PathMatcher.h"

using namespace std;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Node implementation
//////////////////////////////////////////////////////////////////////////

// Struct used to store the name for each node in the tree of paths.
// This is just an InternedString with an extra flag to specify whether
// or not the name contains wildcards (and will therefore need to
// be used with `match()`).
struct PathMatcher::Name
{

	Name( IECore::InternedString name )
		: name( name ), hasWildcards( Gaffer::hasWildcards( name.c_str() ) )
	{
	}

	/// Allows explicit instantiation of the hasWildcards member -
	/// use with care!
	Name( IECore::InternedString name, bool hasWildcards )
		: name( name ), hasWildcards( hasWildcards )
	{
	}

	// Less than implemented to do a lexicographical comparison,
	// first on hasWildcards and then on the name. All names are
	// defined to be > the empty string, so Node::wildcardsBegin()
	// gives consistent results (otherwise results would depend on
	// the empty string's memory address). The comparison of the
	// name uses the InternedString operator which compares via
	// pointer rather than string content, which gives improved performance.
	bool operator < ( const Name &other ) const
	{
		return hasWildcards < other.hasWildcards || ( ( hasWildcards == other.hasWildcards && other.name.c_str()[0] != '\0' ) && name < other.name );
	}

	const IECore::InternedString name;
	const bool hasWildcards;

};

struct PathMatcher::Node
{

	// Container used to store all the children of the node.
	// We need two things out of this structure - quick access
	// to the child with a specific name, and also partitioning
	// between names with wildcards and those without. This is
	// achieved by using an ordered container, and having the
	// less than operation for Names sort first on hasWildcards
	// and second on the name.
	typedef std::map<Name, Node *> ChildMap;
	typedef ChildMap::iterator ChildMapIterator;
	typedef ChildMap::value_type ChildMapValue;
	typedef ChildMap::const_iterator ConstChildMapIterator;

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
			hint = children.insert( hint, ChildMapValue( it->first, new Node( *(it->second) ) ) );
		}
	}

	~Node()
	{
		clearChildren();
	}

	// Returns an iterator to the first child whose name contains wildcards.
	// All children between here and children.end() will also contain wildcards.
	ConstChildMapIterator wildcardsBegin() const
	{
		// The value for name used here will never be inserted in the map,
		// but it marks the transition from non-wildcarded to wildcarded names.
		return children.lower_bound( Name( IECore::InternedString(), true ) );
	}

	Node *child( const Name &name )
	{
		ChildMapIterator it = children.find( name );
		if( it != children.end() )
		{
			return it->second;
		}
		return NULL;
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
			ConstChildMapIterator oIt = other.children.find( it->first );
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

	bool clearChildren()
	{
		const bool result = !children.empty() || ellipsis;
		ChildMap::iterator it, eIt;
		for( it = children.begin(), eIt = children.end(); it != eIt; it++ )
		{
			delete it->second;
		}
		children.clear();
		delete ellipsis;
		ellipsis = NULL;
		return result;
	}

	bool isEmpty()
	{
		return !terminator && !ellipsis && children.empty();
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

static IECore::InternedString g_ellipsis( "..." );

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

bool PathMatcher::isEmpty() const
{
	return m_root->isEmpty();
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
	std::vector<IECore::InternedString> tokenizedPath;
	Gaffer::tokenize( path, '/', tokenizedPath );
	return match( tokenizedPath );
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
	///////////////////////////////////////////////////////////////////////////

	// first check for a child with the exact name we're looking for.
	// we can use the specialised Name constructor to explicitly say we're
	// not interested in finding a child with wildcards here - this avoids
	// a call to hasWildcards() and gives us a decent little performance boost.

	Node::ConstChildMapIterator childIt = node->children.find( Name( *start, false ) );
	const Node::ConstChildMapIterator childItEnd = node->children.end();
	if( childIt != childItEnd )
	{
		NameIterator newStart = start + 1;
		matchWalk( childIt->second, newStart, end, result );
		// if we've found every kind of match then we can terminate early,
		// but otherwise we need to keep going even though we may
		// have found some of the match types already.
		if( result == Filter::EveryMatch )
		{
			return;
		}
	}

	// then check all the wildcarded children to see if they might match

	for( childIt = node->wildcardsBegin(); childIt != childItEnd; ++childIt )
	{
		assert( childIt->first.hasWildcards );
		NameIterator newStart = start + 1;
		if( Gaffer::match( start->c_str(), childIt->first.name.c_str() ) )
		{
			matchWalk( childIt->second, newStart, end, result );
			if( result == Filter::EveryMatch )
			{
				return;
			}
		}
	}

	// finally check for ellipsis matches. we do this last, since it
	// is the most expensive.

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
	std::vector<IECore::InternedString> tokenizedPath;
	Gaffer::tokenize( path, '/', tokenizedPath );
	return addPath( tokenizedPath );
}

bool PathMatcher::addPath( const std::vector<IECore::InternedString> &path )
{
	return addPath( path.begin(), path.end() );
}

template<typename NameIterator>
bool PathMatcher::addPath( const NameIterator &start, const NameIterator &end )
{
	Node *node = m_root.get();
	for( NameIterator it = start; it != end; ++it )
	{
		Node *nextNode = 0;
		const Name name( *it );
		if( name.name == g_ellipsis )
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
			nextNode = node->child( name );
			if( !nextNode )
			{
				nextNode = new Node;
				node->children.insert( Node::ChildMapValue( name, nextNode ) );
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
	std::vector<IECore::InternedString> tokenizedPath;
	Gaffer::tokenize( path, '/', tokenizedPath );
	return removePath( tokenizedPath );
}

bool PathMatcher::removePath( const std::vector<IECore::InternedString> &path )
{
	bool result = false;
	removeWalk( m_root.get(), path.begin(), path.end(), /* prune = */ false, result );
	return result;
}

bool PathMatcher::addPaths( const PathMatcher &paths )
{
	return addPathsWalk( m_root.get(), paths.m_root.get() );
}

bool PathMatcher::removePaths( const PathMatcher &paths )
{
	return removePathsWalk( m_root.get(), paths.m_root.get() );
}

bool PathMatcher::prune( const std::string &path )
{
	std::vector<IECore::InternedString> tokenizedPath;
	Gaffer::tokenize( path, '/', tokenizedPath );
	return prune( tokenizedPath );;
}

bool PathMatcher::prune( const std::vector<IECore::InternedString> &path )
{
	bool result = false;
	removeWalk( m_root.get(), path.begin(), path.end(), /* prune = */ true, result );
	return result;
}

template<typename NameIterator>
void PathMatcher::removeWalk( Node *node, const NameIterator &start, const NameIterator &end, const bool prune, bool &removed )
{
	if( start == end )
	{
		// we've found the end of the path we wish to remove.
		if( prune )
		{
			removed = node->clearChildren();
		}
		removed = removed || node->terminator;
		node->terminator = false;
		return;
	}

	const IECore::InternedString name( *start );
	Node::ChildMapIterator childIt = node->children.end();
	Node *childNode = 0;
	if( name == g_ellipsis )
	{
		childNode = node->ellipsis;
	}
	else
	{
		childIt = node->children.find( name );
		if( childIt != node->children.end() )
		{
			childNode = childIt->second;
		}
	}

	if( !childNode )
	{
		return;
	}

	NameIterator childStart = start; childStart++;
	removeWalk( childNode, childStart, end, prune, removed );
	if( childNode->isEmpty() )
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

bool PathMatcher::addPathsWalk( Node *node, const Node *srcNode )
{
	bool result = false;
	if( !node->terminator && srcNode->terminator )
	{
		node->terminator = result = true;
	}

	for( Node::ChildMap::const_iterator it = srcNode->children.begin(), eIt = srcNode->children.end(); it != eIt; ++it )
	{
		const Node *srcChild = it->second;
		if( Node *child = node->child( it->first ) )
		{
			// result must be on right of ||, to avoid short-circuiting addPathsWalk().
			result = addPathsWalk( child, srcChild ) || result;
		}
		else
		{
			node->children.insert( Node::ChildMapValue( it->first, new Node( *srcChild ) ) );
			result = true; // source node can only exist if it or a descendant is a terminator
		}
	}

	if( srcNode->ellipsis )
	{
		if( node->ellipsis )
		{
			// result must be on right of ||, to avoid short-circuiting addPathsWalk().
			result = addPathsWalk( node->ellipsis, srcNode->ellipsis ) || result;
		}
		else
		{
			node->ellipsis = new Node( *srcNode->ellipsis );
			result = true; // source node can only exist if it or a descendant is a terminator
		}
	}

	return result;
}

bool PathMatcher::removePathsWalk( Node *node, const Node *srcNode )
{
	bool result = false;
	if( node->terminator && srcNode->terminator )
	{
		node->terminator = false;
		result = true;
	}

	for( Node::ChildMap::const_iterator it = srcNode->children.begin(), eIt = srcNode->children.end(); it != eIt; ++it )
	{
		const Node::ChildMapIterator childIt = node->children.find( it->first );
		if( childIt != node->children.end() )
		{
			Node *child = childIt->second;
			if( removePathsWalk( child, it->second ) )
			{
				result = true;
				if( child->isEmpty() )
				{
					node->children.erase( childIt );
					delete child;
				}
			}
		}
	}

	if( node->ellipsis && srcNode->ellipsis )
	{
		if( removePathsWalk( node->ellipsis, srcNode->ellipsis ) )
		{
			result = true;
			if( node->ellipsis->isEmpty() )
			{
				delete node->ellipsis;
				node->ellipsis = NULL;
			}
		}
	}

	return result;
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
		childPath += it->first.name;
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
