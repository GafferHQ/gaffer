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
// Iterator
//////////////////////////////////////////////////////////////////////////

inline void PathMatcher::Iterator::prune()
{
	m_pruned = true;
}

inline PathMatcher::Iterator::Iterator( const PathMatcher &matcher, bool atEnd )
	:	m_atRoot( !atEnd ), m_pruned( false )
{
	if( atEnd )
	{
		m_stack.push_back( Level( matcher.m_root->children, matcher.m_root->children.end() ) );
	}
	else
	{
		m_stack.push_back( Level( matcher.m_root->children, matcher.m_root->children.begin() ) );
	}

	if( m_atRoot && !matcher.m_root->terminator )
	{
		incrementFromRoot();
	}
	incrementWhileNonTerminal();
}

inline void PathMatcher::Iterator::increment()
{
	incrementOnce();
	incrementWhileNonTerminal();
}

inline bool PathMatcher::Iterator::equal( const Iterator &other ) const
{
	return m_stack == other.m_stack && m_atRoot == other.m_atRoot;
}

inline const std::vector<IECore::InternedString> &PathMatcher::Iterator::dereference() const
{
	return m_path;
}

inline bool PathMatcher::Iterator::atEnd() const
{
	if( m_atRoot )
	{
		return false;
	}
	if( m_stack.size() > 1 )
	{
		return false;
	}
	return m_stack.back().it == m_stack.back().end;
}

inline void PathMatcher::Iterator::incrementFromRoot()
{
	assert( m_atRoot );
	m_atRoot = false;
	if( m_stack.back().it != m_stack.back().end )
	{
		m_path.push_back( m_stack.back().it->first.name );
	}
	return;
}

inline void PathMatcher::Iterator::incrementOnce()
{
	if( m_atRoot )
	{
		incrementFromRoot();
		return;
	}

	const Node *node = m_stack.back().it->second;
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

inline void PathMatcher::Iterator::incrementWhileNonTerminal()
{
	while( !atEnd() && !m_stack.back().it->second->terminator )
	{
		incrementOnce();
	}
}

inline PathMatcher::Iterator::Level::Level( const Node::ChildMap &children, Node::ConstChildMapIterator it )
	:	end( children.end() ), it( it )
{
}

inline bool PathMatcher::Iterator::Level::operator == ( const Level &other ) const
{
	return end == other.end && it == other.it;
}

} // namespace GafferScene

#endif // GAFFER_PATHMATCHER_INL
