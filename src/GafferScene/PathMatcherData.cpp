//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "IECore/MessageHandler.h"

#include "GafferScene/PathMatcherData.h"
#include "IECore/TypedData.inl"

using namespace GafferScene;

namespace
{

//////////////////////////////////////////////////////////////////////////
// Support code for SharedDataHolder<GafferScene::PathMatcher>::hash()
//////////////////////////////////////////////////////////////////////////

struct HashNode
{

	HashNode( const char *name, unsigned char exactMatch )
		:	name( name ), exactMatch( exactMatch )
	{
	}

	bool operator < ( const HashNode &rhs ) const
	{
		return strcmp( name, rhs.name ) < 0;
	}

	const char *name;
	unsigned char exactMatch;

};

typedef std::vector<HashNode> HashNodes;
typedef std::stack<HashNodes> HashStack;

void popHashNodes( HashStack &stack, size_t size, IECore::MurmurHash &h )
{
	while( stack.size() > size )
	{
		h.append( (uint64_t)stack.top().size() );
		std::sort( stack.top().begin(), stack.top().end() );
		for( HashNodes::const_iterator nIt = stack.top().begin(), nEIt = stack.top().end(); nIt != nEIt; ++nIt )
		{
			h.append( nIt->name );
			h.append( nIt->exactMatch );
		}
		stack.pop();
	}
}

} // namespace

namespace IECore
{

IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( IECore::PathMatcherData, GafferScene::PathMatcherDataTypeId )

template<>
void PathMatcherData::save( SaveContext *context ) const
{
	Data::save( context );
	msg( Msg::Warning, "PathMatcherData::save", "Not implemented" );
}

template<>
void PathMatcherData::load( LoadContextPtr context )
{
	Data::load( context );
	msg( Msg::Warning, "PathMatcherData::load", "Not implemented" );
}

// Our hash is complicated by the fact that PathMatcher::Iterator doesn't
// guarantee the order of visiting child nodes in its tree (because it
// sorts using InternedString addresses for the fastest possible match()
// implementation). We therefore have to use a stack to keep track of
// our traversal through the tree, and output all the children at each
// level only after sorting them alphabetically.
template<>
MurmurHash SharedDataHolder<GafferScene::PathMatcher>::hash() const
{
	IECore::MurmurHash result;

	HashStack stack;
	GafferScene::PathMatcher m = readable();
	for( PathMatcher::RawIterator it = m.begin(), eIt = m.end(); it != eIt; ++it )
	{
		// The iterator is recursive, so we use a stack to keep
		// track of where we are. Resize the stack to match our
		// current depth. The required size has the +1 because
		// we need a stack entry for the root item.
		size_t requiredStackSize = it->size() + 1;
		if( requiredStackSize > stack.size() )
		{
			// Going a level deeper.
			stack.push( HashNodes() );
			assert( stack.size() == requiredStackSize );
		}
		else if( requiredStackSize < stack.size() )
		{
			// Returning from recursion to the child nodes.
			// Output the hashes for the children we visited
			// and stored on the stack previously.
			popHashNodes( stack, requiredStackSize, result );
		}

		stack.top().push_back( HashNode( it->size() ? it->back().c_str() : "", it.exactMatch() ) );
	}
	popHashNodes( stack, 0, result );

	return result;
}

template class TypedData<GafferScene::PathMatcher>;

} // namespace IECore
