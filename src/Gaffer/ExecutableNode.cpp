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

#include "Gaffer/Context.h"
#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Despatcher.h"
#include "Gaffer/ExecutableNode.h"

using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Task implementation
//////////////////////////////////////////////////////////////////////////

ExecutableNode::Task::Task() : node(0), context(0)
{
}

ExecutableNode::Task::Task( const Task &t ) : node(t.node), context(t.context)
{
}

ExecutableNode::Task::Task( ExecutableNodePtr n, ContextPtr c ) : node(n), context(c)
{
}

MurmurHash ExecutableNode::Task::hash() const
{
	MurmurHash h;
	const Node *nodePtr = node.get();
	h.append( (const char *)nodePtr, sizeof(Node*) );
	h.append( context->hash() );
	return h;
}

bool ExecutableNode::Task::operator == ( const Task &rhs ) const
{
	return (node.get() == rhs.node.get()) && (*context == *rhs.context);
}

bool ExecutableNode::Task::operator < ( const Task &rhs ) const
{
	if ( node.get() < rhs.node.get() )
	{
		return -1;
	}
	if ( node.get() > rhs.node.get() )
	{
		return 1;
	}
	if ( *context == *rhs.context )
	{
		return 0;
	}
	return ( context.get() < rhs.context.get() ? -1 : 1 );
}

//////////////////////////////////////////////////////////////////////////
// ExecutableNode implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ExecutableNode )

size_t ExecutableNode::g_firstPlugIndex;

ExecutableNode::ExecutableNode( const std::string &name )
	:	Node( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ArrayPlug( "requirements", Plug::In, new Plug( "requirement0" ) ) );
	addChild( new Plug( "requirement", Plug::Out ) );

	CompoundPlugPtr despatcherPlug = new CompoundPlug( "despatcherParameters", Plug::In );
	addChild( despatcherPlug );
	
	Despatcher::addAllPlugs( despatcherPlug );
}

ExecutableNode::~ExecutableNode()
{
}

ArrayPlug *ExecutableNode::requirementsPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex );
}

const ArrayPlug *ExecutableNode::requirementsPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex );
}

Plug *ExecutableNode::requirementPlug()
{
	return getChild<Plug>( g_firstPlugIndex + 1 );
}

const Plug *ExecutableNode::requirementPlug() const
{
	return getChild<Plug>( g_firstPlugIndex + 1 );
}

void ExecutableNode::executionRequirements( const Context *context, Tasks &requirements ) const
{
	for( PlugIterator cIt( requirementsPlug() ); cIt != cIt.end(); ++cIt )
	{
		Plug *p = (*cIt)->source<Plug>();
		if( p != *cIt )
		{
			if( ExecutableNode *n = runTimeCast<ExecutableNode>( p->node() ) )
			{
				/// \todo Can we not just reuse the context? Maybe we need to make
				/// the context in Task const?
				requirements.push_back( Task( n, new Context( *context ) ) );
			}
		}
	}
}

IECore::MurmurHash ExecutableNode::executionHash( const Context *context ) const
{
	return MurmurHash();
}

void ExecutableNode::execute( const Contexts &contexts ) const
{
}

bool ExecutableNode::acceptsInput( const Plug *plug, const Plug *inputPlug ) const
{
	if( !Node::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug->parent<ArrayPlug>() == requirementsPlug() )
	{
		const Plug *sourcePlug = inputPlug->source<Plug>();
		const ExecutableNode *sourceNode = runTimeCast<const ExecutableNode>( sourcePlug->node() );
		return sourceNode && sourcePlug == sourceNode->requirementPlug();
	}

	return true;
}

