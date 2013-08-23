//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//  
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//  
//	  * Redistributions of source code must retain the above
//		copyright notice, this list of conditions and the following
//		disclaimer.
//  
//	  * Redistributions in binary form must reproduce the above
//		copyright notice, this list of conditions and the following
//		disclaimer in the documentation and/or other materials provided with
//		the distribution.
//  
//	  * Neither the name of John Haddon nor the names of
//		any other contributors to this software may be used to endorse or
//		promote products derived from this software without specific prior
//		written permission.
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

#include "Gaffer/Node.h"
#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/Executable.h"
#include "Gaffer/Despatcher.h"

using namespace IECore;
using namespace Gaffer;

/*
 * Executable::Task functions
 */

Executable::Task::Task() : node(0), context(0)
{
}

Executable::Task::Task( const Task &t ) : node(t.node), context(t.context)
{
}

Executable::Task::Task( NodePtr n, ContextPtr c ) : node(n), context(c)
{
}

MurmurHash Executable::Task::hash() const
{
	MurmurHash h;
	const Node *nodePtr = node.get();
	h.append( (const char *)nodePtr, sizeof(Node*) );
	h.append( context->hash() );
	return h;
}

bool Executable::Task::operator == ( const Task &rhs ) const
{
	return (node.get() == rhs.node.get()) && (*context == *rhs.context);
}

bool Executable::Task::operator < ( const Task &rhs ) const
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

/*
 * Executable functions
 */

Executable::Executable( Node *node )
{
	node->addChild( new ArrayPlug( "requirements", Plug::In, new Plug( "requirement0" ) ) );
	node->addChild( new Plug( "requirement", Plug::Out ) );

	CompoundPlugPtr despatcherPlug = new CompoundPlug( "despatcherParameters", Plug::In );
	node->addChild( despatcherPlug );
	
	Despatcher::addAllPlugs( despatcherPlug );
}

Executable::~Executable()
{
}

/*
 * Static functions
 */

void Executable::defaultRequirements( const Node *node, const Context *context, Tasks &requirements )
{
	const ArrayPlug *rPlug = node->getChild<ArrayPlug>( "requirements" );
	if ( !rPlug )
	{
		throw Exception( "No requirements plug found!" );
	}
	
	for( PlugIterator cIt( rPlug ); cIt != cIt.end(); ++cIt )
	{
		Plug *p = (*cIt)->source<Plug>();
		if( p != *cIt )
		{
			Node *n = p->node();
			if( n )
			{
				Task newTask;
				newTask.node = n;
				newTask.context = new Context(*context);
				requirements.push_back( newTask );
			}
		}
	}
}

bool Executable::acceptsRequirementsInput( const Plug *plug, const Plug *inputPlug )
{
	const ArrayPlug *ancestor = plug->ancestor<ArrayPlug>();
	if ( ancestor && ancestor->getName() == "requirements" )
	{
		const Plug *p = inputPlug->source<Plug>();
		if ( !p )
		{
			return false;
		}
		const Node *n = p->node();
		if ( !n )
		{
			return false;
		}
		const Executable *e = dynamic_cast< const Executable * >(n);
		if ( !e )
		{
			return false;
		}
	}
	return true;
}
