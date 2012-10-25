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

#include "GafferScene/PathMatcher.h"

using namespace GafferScene;

typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;

//////////////////////////////////////////////////////////////////////////
// Node implementation
//////////////////////////////////////////////////////////////////////////

struct PathMatcher::Node
{
	
	typedef std::map<std::string, Node *> ChildMap;
	
	Node()
		:	terminator( false )
	{
	}
	
	Node *child( const std::string &name )
	{
		ChildMap::iterator it = m_children.find( name );
		if( it != m_children.end() )
		{
			return it->second;
		}
		return 0;
	}
	
	~Node()
	{
		ChildMap::iterator it, eIt;
		for( it = m_children.begin(), eIt = m_children.end(); it != eIt; it++ )
		{
			delete it->second;
		}				
	}
	
	bool terminator;
	ChildMap m_children;
	
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
	
	Tokenizer tokenizer( path, boost::char_separator<char>( "/" ) );	
	Tokenizer::iterator it, eIt;
	for( it = tokenizer.begin(), eIt = tokenizer.end(); it != eIt; it++ )
	{
		node = node->child( *it );
		if( !node )
		{
			return Filter::NoMatch;
		}
	}
	
	return node->terminator ? Filter::Match : Filter::DescendantMatch;
}

void PathMatcher::addPath( const std::string &path )
{
	Node *node = m_root.get();
	Tokenizer tokenizer( path, boost::char_separator<char>( "/" ) );	
	Tokenizer::iterator it, eIt;
	for( it = tokenizer.begin(), eIt = tokenizer.end(); it != eIt; it++ )
	{
		Node *nextNode = node->child( *it );
		if( !nextNode )
		{
			nextNode = new Node;
			node->m_children[*it] = nextNode;
		}
		node = nextNode;
	}
	node->terminator = true;
}
