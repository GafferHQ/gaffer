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
	: name( name ), type( name == g_ellipsis || Gaffer::StringAlgo::hasWildcards( name.c_str() ) ? Wildcarded : Plain )
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

PathMatcher::Node::Node( bool terminator )
	:	terminator( terminator )
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

PathMatcher::Node *PathMatcher::Node::leaf()
{
	static NodePtr g_leaf = new Node( true );
	assert( g_leaf->terminator );
	assert( g_leaf->children.empty() );
	return g_leaf.get();
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

PathMatcher::PathMatcher( const NodePtr &root )
	:	m_root( root )
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
	if( path.empty() )
	{
		return Filter::NoMatch;
	}
	std::vector<IECore::InternedString> tokenizedPath;
	Gaffer::StringAlgo::tokenize( path, '/', tokenizedPath );
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
		if( Gaffer::StringAlgo::match( start->c_str(), childIt->first.name.c_str() ) )
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
	if( path.empty() )
	{
		return false;
	}
	std::vector<IECore::InternedString> tokenizedPath;
	Gaffer::StringAlgo::tokenize( path, '/', tokenizedPath );
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
	if( path.empty() )
	{
		return false;
	}
	std::vector<IECore::InternedString> tokenizedPath;
	Gaffer::StringAlgo::tokenize( path, '/', tokenizedPath );
	return removePath( tokenizedPath );
}

bool PathMatcher::removePath( const std::vector<IECore::InternedString> &path )
{
	bool result = false;
	NodePtr newRoot = removeWalk( m_root.get(), path.begin(), path.end(), /* shared = */ false, /* prune = */ false, result );
	if( newRoot )
	{
		m_root = newRoot;
	}
	return result;
}

bool PathMatcher::addPaths( const PathMatcher &paths )
{
	bool result = false;
	NodePtr newRoot = addPathsWalk( m_root.get(), paths.m_root.get(), /* shared = */ false, result );
	if( newRoot )
	{
		m_root = newRoot;
	}
	return result;
}

bool PathMatcher::addPaths( const PathMatcher &paths, const std::vector<IECore::InternedString> &prefix )
{
	if( paths.isEmpty() )
	{
		return false;
	}

	bool result = false;
	NodePtr newRoot = addPrefixedPathsWalk( m_root.get(), paths.m_root.get(), prefix.begin(), prefix.end(), /* shared = */ false, result );
	if( newRoot )
	{
		m_root = newRoot;
	}
	return result;
}

bool PathMatcher::removePaths( const PathMatcher &paths )
{
	bool result = false;
	NodePtr newRoot = removePathsWalk( m_root.get(), paths.m_root.get(), /* shared = */ false, result );
	if( newRoot )
	{
		m_root = newRoot;
	}
	return result;
}

bool PathMatcher::prune( const std::string &path )
{
	if( path.empty() )
	{
		return false;
	}
	std::vector<IECore::InternedString> tokenizedPath;
	Gaffer::StringAlgo::tokenize( path, '/', tokenizedPath );
	return prune( tokenizedPath );;
}

bool PathMatcher::prune( const std::vector<IECore::InternedString> &path )
{
	bool result = false;
	NodePtr newRoot = removeWalk( m_root.get(), path.begin(), path.end(), /* shared = */ false, /* prune = */ true, result );
	if( newRoot )
	{
		m_root = newRoot;
	}
	return result;
}

PathMatcher PathMatcher::subTree( const std::string &root ) const
{
	if( root.empty() )
	{
		return PathMatcher();
	}
	std::vector<IECore::InternedString> tokenizedRoot;
	Gaffer::StringAlgo::tokenize( root, '/', tokenizedRoot );
	return subTree( tokenizedRoot );
}

PathMatcher PathMatcher::subTree( const std::vector<IECore::InternedString> &root ) const
{
	RawIterator it = find( root );
	if( it == end() )
	{
		return PathMatcher();
	}
	else
	{
		return PathMatcher( it.node() );
	}
}

PathMatcher::RawIterator PathMatcher::begin() const
{
	return RawIterator( *this, false );
}

PathMatcher::RawIterator PathMatcher::end() const
{
	return RawIterator( *this, true );
}

PathMatcher::RawIterator PathMatcher::find( const std::vector<IECore::InternedString> &path ) const
{
	return RawIterator( *this, path );
}

PathMatcher::Node *PathMatcher::writable( Node *node, NodePtr &writableCopy, bool shared )
{
	if( !shared )
	{
		return node;
	}

	if( !writableCopy )
	{
		writableCopy = new Node( *node );
	}
	return writableCopy.get();
}

PathMatcher::NodePtr PathMatcher::addWalk( Node *node, const NameIterator &start, const NameIterator &end, bool shared, bool &added )
{
	shared = shared || node->refCount() > 1;
	NodePtr result;

	if( start == end )
	{
		// We're at the end of the path we wish to add.
		if( node->terminator )
		{
			// Nothing to do.
			return NULL;
		}

		writable( node, result, shared )->terminator = true;
		added = true;
		return result;
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
		if( childStart == end )
		{
			// We're adding a leaf node. Rather than allocate a brand
			// new node for this, we can just reuse a single shared
			// instance. If later on the node needs to be edited, our
			// lazy-copy-on-write behaviour will avoid editing the
			// shared node anyway. Since leaf nodes often dominate within
			// our trees, this optimisation saves significant amounts of
			// memory.
			newChild = Node::leaf();
			added = true;
		}
		else
		{
			newChild = new Node();
			addWalk( newChild.get(), childStart, end, /* shared = */ false, added );
		}
	}

	// If there's a new child then add it. If we ourselves are shared
	// then we'll need to create a new node to do this in, and then
	// return that to our caller to be replaced in its node and so on.
	if( newChild )
	{
		writable( node, result, shared )->children[*start] = newChild;
	}

	return result;
}

PathMatcher::NodePtr PathMatcher::removeWalk( Node *node, const NameIterator &start, const NameIterator &end, bool shared, const bool prune, bool &removed )
{
	shared = shared || node->refCount() > 1;
	NodePtr result;

	if( start == end )
	{
		// we've found the end of the path we wish to remove.
		if( prune )
		{
			removed = writable( node, result, shared )->clearChildren();
		}
		removed = removed || node->terminator;
		writable( node, result, shared )->terminator = false;
		/// \todo When we're pruning, we end up creating a new empty
		/// node to return, just to signal to the caller that they
		/// should erase the original child. We could use a single
		/// shared instance for this return value instead of allocating
		/// a new one with writable() all the time.
		return result;
	}

	Node::ChildMapIterator childIt = node->children.find( *start );
	if( childIt == node->children.end() )
	{
		return result;
	}

	Node *childNode = childIt->second.get();

	NameIterator childStart = start; childStart++;
	NodePtr newChild = removeWalk( childIt->second.get(), childStart, end, shared, prune, removed );

	if( newChild && !newChild->isEmpty() )
	{
		writable( node, result, shared )->children[childIt->first] = newChild;
	}
	else if( childNode->isEmpty() || ( newChild && newChild->isEmpty() ) )
	{
		writable( node, result, shared )->children.erase( childIt->first );
	}

	return result;
}

PathMatcher::NodePtr PathMatcher::addPathsWalk( Node *node, const Node *srcNode, bool shared, bool &added )
{
	shared = shared || node->refCount() > 1;

	NodePtr result;
	if( !node->terminator && srcNode->terminator )
	{
		added = true;
		writable( node, result, shared )->terminator = true;
	}

	for( Node::ChildMap::const_iterator it = srcNode->children.begin(), eIt = srcNode->children.end(); it != eIt; ++it )
	{
		Node *srcChild = it->second.get();
		NodePtr newChild;
		if( Node *child = node->child( it->first ) )
		{
			if( child != srcChild )
			{
				newChild = addPathsWalk( child, srcChild, shared, added );
			}
		}
		else
		{
			newChild = srcChild;
			added = true; // source node can only exist if it or a descendant is a terminator
		}
		if( newChild )
		{
			writable( node, result, shared )->children[it->first] = newChild;
		}
	}

	return result;
}

PathMatcher::NodePtr PathMatcher::addPrefixedPathsWalk( Node *node, const Node *srcNode, const NameIterator &start, const NameIterator &end, bool shared, bool &added  )
{
	shared = shared || node->refCount() > 1;

	if( start == end )
	{
		// At the end of the prefix path. Defer to addPathsWalk()
		// to actually add the paths.
		return addPathsWalk( node, srcNode, shared, added );
	}

	// Not at the end of the prefix path yet. Need to make sure we
	// have an appropriate child and recurse.

	NodePtr newChild;
	NameIterator childStart = start; childStart++;

	if( Node *child = node->child( *start ) )
	{
		// Recurse using the child we've found. We may still need to replace this
		// child with a new one in the event that it is duplicated in order to be
		// written to.
		newChild = addPrefixedPathsWalk( child, srcNode, childStart, end, shared, added );
	}
	else
	{
		// No matching child, so make a new one.
		newChild = new Node();
		addPrefixedPathsWalk( newChild.get(), srcNode, childStart, end, /* shared = */ false, added );
	}

	// If there's a new child then add it. If we ourselves are shared
	// then we'll need to create a new node to do this in, and then
	// return that to our caller to be replaced in its node and so on.
	NodePtr result;
	if( newChild )
	{
		writable( node, result, shared )->children[*start] = newChild;
	}

	return result;
}

PathMatcher::NodePtr PathMatcher::removePathsWalk( Node *node, const Node *srcNode, bool shared, bool &removed )
{
	shared = shared || node->refCount() > 1;
	NodePtr result;

	if( node->terminator && srcNode->terminator )
	{
		writable( node, result, shared )->terminator = false;
		removed = true;
	}

	for( Node::ChildMap::const_iterator it = srcNode->children.begin(), eIt = srcNode->children.end(); it != eIt; ++it )
	{
		const Node::ChildMapIterator childIt = node->children.find( it->first );
		if( childIt != node->children.end() )
		{
			Node *child = childIt->second.get();
			NodePtr newChild = removePathsWalk( child, it->second.get(), shared, removed );

			if( newChild && !newChild->isEmpty() )
			{
				writable( node, result, shared )->children[childIt->first] = newChild;
			}
			else if( child->isEmpty() || ( newChild && newChild->isEmpty() ) )
			{
				writable( node, result, shared )->children.erase( childIt->first );
			}
		}
	}

	return result;
}
