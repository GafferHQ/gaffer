//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_PATHMATCHER_INL
#define GAFFER_PATHMATCHER_INL

namespace GafferScene
{

//////////////////////////////////////////////////////////////////////////
// PathMatcher
//////////////////////////////////////////////////////////////////////////

template<typename PathIterator>
PathMatcher::PathMatcher( PathIterator pathsBegin, PathIterator pathsEnd )
{
	init( pathsBegin, pathsEnd );
}

template<typename PathIterator>
void PathMatcher::init( PathIterator pathsBegin, PathIterator pathsEnd )
{
	clear();
	for( PathIterator it = pathsBegin; it != pathsEnd; it++ )
	{
		addPath( *it );
	}
}

//////////////////////////////////////////////////////////////////////////
// RawIterator
//////////////////////////////////////////////////////////////////////////

inline void PathMatcher::RawIterator::prune()
{
	m_pruned = true;
}

inline const bool PathMatcher::RawIterator::exactMatch() const
{
	if( const Node *n = node() )
	{
		return n->terminator;
	}
	return false;
}

inline PathMatcher::RawIterator::RawIterator( const PathMatcher &matcher, bool atEnd )
	:	m_nodeIfRoot( NULL ), m_pruned( false )
{
	if( atEnd )
	{
		m_stack.push_back( Level( matcher.m_root->children, matcher.m_root->children.end() ) );
	}
	else
	{
		m_stack.push_back( Level( matcher.m_root->children, matcher.m_root->children.begin() ) );
		if( !matcher.isEmpty() )
		{
			m_nodeIfRoot = matcher.m_root.get();
		}
	}
}

inline PathMatcher::RawIterator::RawIterator( const PathMatcher &matcher, const std::vector<IECore::InternedString> &path )
	:	m_nodeIfRoot( NULL ), m_pruned( false )
{
	if( !path.size() )
	{
		m_stack.push_back( Level( matcher.m_root->children, matcher.m_root->children.begin() ) );
		if( !matcher.isEmpty() )
		{
			m_nodeIfRoot = matcher.m_root.get();
		}
		return;
	}

	Node *node = matcher.m_root.get();
	for( std::vector<IECore::InternedString>::const_iterator it = path.begin(), eIt = path.end(); it != eIt; ++it )
	{
		Node::ConstChildMapIterator cIt = node->children.find( *it );
		if( cIt == node->children.end() )
		{
			// path doesn't exist
			m_stack.clear();
			m_stack.push_back( Level( matcher.m_root->children, matcher.m_root->children.end() ) );
			return;
		}
		m_stack.push_back( Level( node->children, cIt ) );
		node = cIt->second.get();
	}
	m_path = path;
}

inline void PathMatcher::RawIterator::increment()
{
	if( m_nodeIfRoot )
	{
		m_path.push_back( m_stack.back().it->first.name );
		m_nodeIfRoot = NULL;
		return;
	}

	const Node *node = m_stack.back().it->second.get();
	if( !m_pruned && !node->children.empty() )
	{
		m_stack.push_back(
			Level(
				node->children,
				node->children.begin()
			)
		);
		m_path.push_back( m_stack.back().it->first.name );
	}
	else
	{
		++(m_stack.back().it);
		while( m_stack.size() > 1 && m_stack.back().it == m_stack.back().end )
		{
			m_stack.pop_back();
			m_path.pop_back();
			++(m_stack.back().it);
		}

		if( m_stack.back().it != m_stack.back().end )
		{
			m_path.back() = m_stack.back().it->first.name;
		}
	}
	m_pruned = false;
}

inline bool PathMatcher::RawIterator::equal( const RawIterator &other ) const
{
	return m_stack == other.m_stack && m_nodeIfRoot == other.m_nodeIfRoot;
}

inline const std::vector<IECore::InternedString> &PathMatcher::RawIterator::dereference() const
{
	return m_path;
}

inline PathMatcher::Node *PathMatcher::RawIterator::node() const
{
	if( m_nodeIfRoot )
	{
		return m_nodeIfRoot;
	}
	else
	{
		if( m_stack.back().it != m_stack.back().end )
		{
			return m_stack.back().it->second.get();
		}
	}
	return NULL;
}

inline PathMatcher::RawIterator::Level::Level( const Node::ChildMap &children, Node::ConstChildMapIterator it )
	:	end( children.end() ), it( it )
{
}

inline bool PathMatcher::RawIterator::Level::operator == ( const Level &other ) const
{
	return end == other.end && it == other.it;
}

//////////////////////////////////////////////////////////////////////////
// Iterator
//////////////////////////////////////////////////////////////////////////

inline PathMatcher::Iterator::Iterator( const RawIterator &it )
	: boost::iterator_adaptor<Iterator, PathMatcher::RawIterator>( it )
{
	satisfyTerminatorRequirement();
}

inline bool PathMatcher::Iterator::operator==( const RawIterator &rhs ) const
{
	return base() == rhs;
}

inline bool PathMatcher::Iterator::operator!=( const RawIterator &rhs ) const
{
	return base() != rhs;
}

inline void PathMatcher::Iterator::prune()
{
	base_reference().prune();
}

inline void PathMatcher::Iterator::increment()
{
	++base_reference();
	satisfyTerminatorRequirement();
}

inline void PathMatcher::Iterator::satisfyTerminatorRequirement()
{
	const Node *node = base().node();
	while( node && !node->terminator )
	{
		++base_reference();
		node = base().node();
	}
}

} // namespace GafferScene

#endif // GAFFER_PATHMATCHER_INL
