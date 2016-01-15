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
#include "GafferScene/ScenePlug.h"

using namespace std;
using namespace GafferScene;

static IECore::InternedString g_ellipsis( "..." );

//////////////////////////////////////////////////////////////////////////
// Name implementation
//////////////////////////////////////////////////////////////////////////

inline PathMatcher::Name::Name( IECore::InternedString name )
	: name( name ), type( name == g_ellipsis || Gaffer::hasWildcards( name.c_str() ) ? Wildcarded : Plain )
{
}

inline PathMatcher::Name::Name( IECore::InternedString name, Type type )
	: name( name ), type( type )
{
}

inline bool PathMatcher::Name::operator < ( const Name &other ) const
{
	return type < other.type || ( ( type == other.type ) && name < other.name );
}

//////////////////////////////////////////////////////////////////////////
// Node implementation
//////////////////////////////////////////////////////////////////////////

PathMatcher::Node::Node()
	:	terminator( false )
{
}

PathMatcher::Node::Node( const Node &other )
	:	children( other.children ), terminator( other.terminator )
{
}

PathMatcher::Node::~Node()
{
}

inline PathMatcher::Node::ConstChildMapIterator PathMatcher::Node::wildcardsBegin() const
{
	// The value for name used here will never be inserted in the map,
	// but it marks the transition from non-wildcarded to wildcarded names.
	return children.lower_bound( Name( IECore::InternedString(), Name::Boundary ) );
}

inline PathMatcher::Node *PathMatcher::Node::child( const Name &name )
{
	ChildMapIterator it = children.find( name );
	if( it != children.end() )
	{
		return it->second.get();
	}
	return NULL;
}

inline const PathMatcher::Node *PathMatcher::Node::child( const Name &name ) const
{
	ConstChildMapIterator it = children.find( name );
	if( it != children.end() )
	{
		return it->second.get();
	}
	return NULL;
}

bool PathMatcher::Node::operator == ( const Node &other ) const
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

	return true;
}

bool PathMatcher::Node::operator != ( const Node &other )
{
	return !( *this == other );
}

bool PathMatcher::Node::clearChildren()
{
	const bool result = !children.empty();
	children.clear();
	return result;
}

bool PathMatcher::Node::isEmpty()
{
	return !terminator && children.empty();
}

//////////////////////////////////////////////////////////////////////////
// PathMatcher implementation
//////////////////////////////////////////////////////////////////////////

PathMatcher::PathMatcher()
	:	m_root( new Node )
{
}

PathMatcher::PathMatcher( const PathMatcher &other )
	:	m_root( other.m_root )
{
}

void PathMatcher::clear()
{
	m_root = new Node;
}

bool PathMatcher::isEmpty() const
{
	return m_root->isEmpty();
}

void PathMatcher::paths( std::vector<std::string> &paths ) const
{
	for( Iterator it = begin(), eIt = end(); it != eIt; ++it )
	{
		paths.push_back( std::string() );
		ScenePlug::pathToString( *it, paths.back() );
	}
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

void PathMatcher::matchWalk( const Node *node, const NameIterator &start, const NameIterator &end, unsigned &result ) const
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
		if( const Node *ellipsis = node->child( g_ellipsis ) )
		{
			result |= Filter::DescendantMatch;
			if( ellipsis->terminator )
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

	Node::ConstChildMapIterator childIt = node->children.find( Name( *start, Name::Plain ) );
	const Node::ConstChildMapIterator childItEnd = node->children.end();
	if( childIt != childItEnd )
	{
		NameIterator newStart = start + 1;
		matchWalk( childIt->second.get(), newStart, end, result );
		// if we've found every kind of match then we can terminate early,
		// but otherwise we need to keep going even though we may
		// have found some of the match types already.
		if( result == Filter::EveryMatch )
		{
			return;
		}
	}

	// then check all the wildcarded children to see if they might match.

	const Node *ellipsis = NULL;
	for( childIt = node->wildcardsBegin(); childIt != childItEnd; ++childIt )
	{
		assert( childIt->first.type == Name::Wildcarded );
		if( childIt->first.name == g_ellipsis )
		{
			// store for use in next block.
			ellipsis = childIt->second.get();
			continue;
		}

		NameIterator newStart = start + 1;
		if( Gaffer::match( start->c_str(), childIt->first.name.c_str() ) )
		{
			matchWalk( childIt->second.get(), newStart, end, result );
			if( result == Filter::EveryMatch )
			{
				return;
			}
		}
	}

	// finally check for ellipsis matches. we do this last, since it
	// is the most expensive.

	if( ellipsis )
	{
		result |= Filter::DescendantMatch;
		if( ellipsis->terminator )
		{
			result |= Filter::ExactMatch;
		}

		NameIterator newStart = start;
		while( newStart != end )
		{
			matchWalk( ellipsis, newStart, end, result );
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
	bool result = false;
	NodePtr newRoot = addWalk( m_root.get(), path.begin(), path.end(), /* shared = */ false, result );
	if( newRoot )
	{
		m_root = newRoot;
	}
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

PathMatcher::RawIterator PathMatcher::begin() const
{
	return RawIterator( *this, false );
}

PathMatcher::RawIterator PathMatcher::end() const
{
	return RawIterator( *this, true );
}

PathMatcher::NodePtr PathMatcher::addWalk( Node *node, const NameIterator &start, const NameIterator &end, bool shared, bool &added )
{
	shared = shared || node->refCount() > 1;
	if( start == end )
	{
		// We're at the end of the path we wish to add.
		if( node->terminator )
		{
			// Nothing to do.
			return NULL;
		}

		added = true;
		if( shared )
		{
			NodePtr result = new Node( *node );
			result->terminator = true;
			return result;
		}
		else
		{
			node->terminator = true;
			return NULL;
		}
	}

	// Not at the end of the path yet. Need to make sure we
	// have an appropriate child and recurse.

	NodePtr newChild;
	NameIterator childStart = start; childStart++;

	if( Node *child = node->child( *start ) )
	{
		// Recurse using the child we've found. We may still need to replace this
		// child with a new one in the event that it is duplicated in order to be
		// written to.
		newChild = addWalk( child, childStart, end, shared, added );
	}
	else
	{
		// No matching child, so make a new one.
		newChild = new Node();
		addWalk( newChild.get(), childStart, end, /* shared = */ false, added );
	}

	// If there's a new child then add it. If we ourselves are shared
	// then we'll need to create a new node to do this in, and then
	// return that to our caller to be replaced in its node and so on.
	if( newChild )
	{
		if( shared )
		{
			NodePtr result = new Node( *node );
			result->children[*start] = newChild;
			return result;
		}
		else
		{
			node->children[*start] = newChild;
		}
	}

	return NULL;
}

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
	Node::ChildMapIterator childIt = node->children.find( name );
	if( childIt == node->children.end() )
	{
		return;
	}

	Node *childNode = childIt->second.get();

	NameIterator childStart = start; childStart++;
	removeWalk( childNode, childStart, end, prune, removed );
	if( childNode->isEmpty() )
	{
		node->children.erase( childIt );
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
		const Node *srcChild = it->second.get();
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
			Node *child = childIt->second.get();
			if( removePathsWalk( child, it->second.get() ) )
			{
				result = true;
				if( child->isEmpty() )
				{
					node->children.erase( childIt );
				}
			}
		}
	}

	return result;
}
