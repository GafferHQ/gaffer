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

#include "Gaffer/ComputeNode.h"

#include "Gaffer/ValuePlug.h"

using namespace Gaffer;

GAFFER_NODE_DEFINE_TYPE( ComputeNode );

ComputeNode::ComputeNode( const std::string &name )
	:	DependencyNode( name )
{
}

ComputeNode::~ComputeNode()
{
}

void ComputeNode::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	// Hash in the TypeId for this node - this does two things.
	// Firstly, it breaks apart hashes for nodes which use identical
	// inputs to produce an output (think of a mult vs an add both taking
	// a pair of input plugs (op1,op2) for a trivial example). Secondly,
	// it breaks apart ComputeNode hashes and IECore::Object hashes, because
	// IECore::Object hashes always start by appending the Object::typeId(),
	// which is guaranteed to be different to any ComputeNode::typeId().
	h.append( typeId() );
	// Append on the name of the output relative to the node. This
	// breaks apart hashes for different output plugs. We do our own
	// traversal rather than call output->relativeName() because
	// relativeName() allocates memory and is therefore too costly.
	const GraphComponent *g = output;
	while( g && g != this )
	{
		h.append( g->getName() );
		g = g->parent();
	}
}

void ComputeNode::compute( ValuePlug *output, const Context *context ) const
{
}

ValuePlug::CachePolicy ComputeNode::hashCachePolicy( const ValuePlug *output ) const
{
	return ValuePlug::CachePolicy::Default;
}

ValuePlug::CachePolicy ComputeNode::computeCachePolicy( const ValuePlug *output ) const
{
	if( !output->getFlags( Plug::Cacheable ) )
	{
		return ValuePlug::CachePolicy::Uncached;
	}
	return ValuePlug::CachePolicy::Default;
}
