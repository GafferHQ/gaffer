//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Node.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/ScriptNode.h"

using namespace Gaffer;

size_t Node::g_firstPlugIndex;

IE_CORE_DEFINERUNTIMETYPED( Node );

Node::Node( const std::string &name )
	:	GraphComponent( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundPlug( "user" ) );
}

Node::~Node()
{
}
		
Node::UnaryPlugSignal &Node::plugSetSignal()
{
	return m_plugSetSignal;
}

Node::UnaryPlugSignal &Node::plugInputChangedSignal()
{
	return m_plugInputChangedSignal;
}

Node::UnaryPlugSignal &Node::plugFlagsChangedSignal()
{
	return m_plugFlagsChangedSignal;
}

Node::UnaryPlugSignal &Node::plugDirtiedSignal()
{
	return m_plugDirtiedSignal;
}

Gaffer::CompoundPlug *Node::userPlug()
{
	return getChild<CompoundPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundPlug *Node::userPlug() const
{
	return getChild<CompoundPlug>( g_firstPlugIndex );
}

ScriptNode *Node::scriptNode()
{
	return ancestor<ScriptNode>();
}

const ScriptNode *Node::scriptNode() const
{
	return ancestor<ScriptNode>();
}
		
bool Node::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !GraphComponent::acceptsChild( potentialChild ) )
	{
		return false;
	}
	return potentialChild->isInstanceOf( (IECore::TypeId)PlugTypeId ) || potentialChild->isInstanceOf( (IECore::TypeId)NodeTypeId );
}

bool Node::acceptsParent( const GraphComponent *potentialParent ) const
{
	if( !GraphComponent::acceptsParent( potentialParent ) )
	{
		return false;
	}
	return potentialParent->isInstanceOf( (IECore::TypeId)NodeTypeId );
}

bool Node::acceptsInput( const Plug *plug, const Plug *inputPlug ) const
{
	return true;
}

void Node::parentChanging( Gaffer::GraphComponent *newParent )
{
	// if we're losing our parent then remove all connections first.
	// this must be done here rather than from parentChangedSignal()
	// because we need a current parent for the operation to be
	// undoable.
	
	if( !newParent )
	{
		for( InputPlugIterator it( this ); it!=it.end(); it++ )
		{
			(*it)->setInput( 0 );
		}

		for( OutputPlugIterator it( this ); it!=it.end(); it++ )
		{
			(*it)->removeOutputs();
		}
	}
}

BoolPlug *Node::enabledPlug()
{
	return 0;
}

const BoolPlug *Node::enabledPlug() const
{
	return 0;
}

Plug *Node::correspondingInput( const Plug *output )
{
	return 0;
}

const Plug *Node::correspondingInput( const Plug *output ) const
{
	return 0;
}
