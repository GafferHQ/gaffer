//////////////////////////////////////////////////////////////////////////
//
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

#include "Gaffer/SubGraph.h"

using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( SubGraph );

SubGraph::SubGraph( const std::string &name )
	:	DependencyNode( name )
{
}

SubGraph::~SubGraph()
{
}

void SubGraph::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	DependencyNode::affects( input, outputs );
}

BoolPlug *SubGraph::enabledPlug()
{
	return getChild<BoolPlug>( "enabled" );
}

const BoolPlug *SubGraph::enabledPlug() const
{
	return getChild<BoolPlug>( "enabled" );
}

Plug *SubGraph::correspondingInput( const Plug *output )
{
	return const_cast<Plug *>( const_cast<const SubGraph *>( this )->SubGraph::correspondingInput( output ) );
}

const Plug *SubGraph::correspondingInput( const Plug *output ) const
{
	const Plug *internalOutput = output->getInput<Plug>();
	if( !internalOutput )
	{
		return NULL;
	}

	const DependencyNode *node = IECore::runTimeCast<const DependencyNode>( internalOutput->node() );
	if( !node )
	{
		return NULL;
	}

	const BoolPlug *externalEnabledPlug = enabledPlug();
	if( !externalEnabledPlug )
	{
		return NULL;
	}

	const BoolPlug *internalEnabledPlug = node->enabledPlug();
	if( !internalEnabledPlug )
	{
		return NULL;
	}

	if( internalEnabledPlug->getInput<Plug>() != externalEnabledPlug )
	{
		return NULL;
	}

	const Plug *internalInput = node->correspondingInput( internalOutput );
	if( !internalInput )
	{
		return NULL;
	}

	const Plug *input = internalInput->getInput<Plug>();
	if( !input || input->node() != this )
	{
		return NULL;
	}

	return input;
}
