//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

#include "IECore/Exception.h"
#include "IECore/SimpleTypedData.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/Action.h"
#include "Gaffer/ApplicationRoot.h"
#include "Gaffer/Context.h"
#include "Gaffer/CompoundPlug.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace Gaffer;

namespace Gaffer
{

GAFFER_DECLARECONTAINERSPECIALISATIONS( ScriptContainer, ScriptContainerTypeId )

}

IE_CORE_DEFINERUNTIMETYPED( ScriptNode );

ScriptNode::ScriptNode( const std::string &name )
	:	Node( name ), m_selection( new StandardSet ), m_undoIterator( m_undoList.end() ), m_context( new Context )
{
	m_fileNamePlug = new StringPlug( "fileName", Plug::In, "" );
	addChild( m_fileNamePlug );
	
	CompoundPlugPtr frameRangePlug = new CompoundPlug( "frameRange", Plug::In );
	IntPlugPtr frameStartPlug = new IntPlug( "start", Plug::In, 1 );
	IntPlugPtr frameEndPlug = new IntPlug( "end", Plug::In, 100 );
	frameRangePlug->addChild( frameStartPlug );
	frameRangePlug->addChild( frameEndPlug );
	addChild( frameRangePlug );
	
	m_selection->memberAcceptanceSignal().connect( boost::bind( &ScriptNode::selectionSetAcceptor, this, ::_1, ::_2 ) );

	childRemovedSignal().connect( boost::bind( &ScriptNode::childRemoved, this, ::_1, ::_2 ) );
	plugSetSignal().connect( boost::bind( &ScriptNode::plugSet, this, ::_1 ) );
}

ScriptNode::~ScriptNode()
{
}

bool ScriptNode::acceptsParent( const GraphComponent *potentialParent ) const
{
	return potentialParent->isInstanceOf( ScriptContainer::staticTypeId() );
}

ApplicationRoot *ScriptNode::applicationRoot()
{
	return ancestor<ApplicationRoot>();
}

const ApplicationRoot *ScriptNode::applicationRoot() const
{
	return ancestor<ApplicationRoot>();
}

bool ScriptNode::selectionSetAcceptor( Set::ConstPtr s, Set::ConstMemberPtr m )
{
	ConstNodePtr n = IECore::runTimeCast<const Node>( m );
	if( !n )
	{
		return false;
	}
	return n->parent<ScriptNode>()==this;
}

StandardSetPtr ScriptNode::selection()
{
	return m_selection;
}

ConstStandardSetPtr ScriptNode::selection() const
{
	return m_selection;
}

bool ScriptNode::undoAvailable() const
{
	return m_undoIterator != m_undoList.begin();
}

void ScriptNode::undo()
{
	if( !undoAvailable() )
	{
		throw IECore::Exception( "Nothing to undo" );
	}
	m_undoIterator--;
	for( ActionVector::reverse_iterator it=(*m_undoIterator)->rbegin(); it!=(*m_undoIterator)->rend(); it++ )
	{
		(*it)->undoAction();
	}
}

bool ScriptNode::redoAvailable() const
{
	return m_undoIterator != m_undoList.end();
}

void ScriptNode::redo()
{
	if( !redoAvailable() )
	{
		throw IECore::Exception( "Nothing to redo" );
	}
	for( ActionVector::iterator it=(*m_undoIterator)->begin(); it!=(*m_undoIterator)->end(); it++ )
	{
		(*it)->doAction();
	}
	m_undoIterator++;
}

void ScriptNode::copy( ConstSetPtr filter )
{
	ApplicationRoot *app = applicationRoot();
	if( !app )
	{
		throw( "ScriptNode has no ApplicationRoot" );
	}
	
	std::string s = serialise( filter );
	app->setClipboardContents( new IECore::StringData( s ) );
}

void ScriptNode::cut( ConstSetPtr filter )
{
	copy( filter );
	deleteNodes( filter );
}

void ScriptNode::paste()
{
	ApplicationRoot *app = applicationRoot();
	if( !app )
	{
		throw( "ScriptNode has no ApplicationRoot" );
	}
	
	IECore::ConstStringDataPtr s = IECore::runTimeCast<const IECore::StringData>( app->getClipboardContents() );
	if( s )
	{
		// set up something to catch all the newly created nodes
		StandardSetPtr newNodes = new StandardSet;
		childAddedSignal().connect( boost::bind( (bool (StandardSet::*)( IECore::RunTimeTypedPtr ) )&StandardSet::add, newNodes.get(), ::_2 ) );
			
			// do the paste
			execute( s->readable() );

		// transfer the newly created nodes into the selection
		selection()->clear();
		for( size_t i = 0, e = newNodes->size(); i < e; i++ )
		{
			selection()->add( newNodes->member( i ) );
		}
	}
}

void ScriptNode::deleteNodes( ConstSetPtr filter )
{
	ChildNodeIterator nIt;
	for( nIt=childrenBegin<Node>(); nIt!=childrenEnd<Node>(); )
	{
	
		ChildNodeIterator next = nIt; next++;
		if( !filter || filter->contains( *nIt ) )
		{
			(*nIt)->parent<GraphComponent>()->removeChild( (*nIt) );
		}
		
		nIt = next;
		
	}

}

StringPlugPtr ScriptNode::fileNamePlug()
{
	return m_fileNamePlug;
}

ConstStringPlugPtr ScriptNode::fileNamePlug() const
{
	return m_fileNamePlug;
}

void ScriptNode::execute( const std::string &pythonScript )
{
	throw IECore::Exception( "Cannot execute scripts on a ScriptNode not created in Python." );
}

ScriptNode::ScriptExecutedSignal &ScriptNode::scriptExecutedSignal()
{
	return m_scriptExecutedSignal;
}

PyObject *ScriptNode::evaluate( const std::string &pythonExpression )
{
	throw IECore::Exception( "Cannot execute scripts on a ScriptNode not created in Python." );
}

ScriptNode::ScriptEvaluatedSignal &ScriptNode::scriptEvaluatedSignal()
{
	return m_scriptEvaluatedSignal;
}

std::string ScriptNode::serialise( ConstSetPtr filter ) const
{
	throw IECore::Exception( "Cannot serialise scripts on a ScriptNode not created in Python." );
}

void ScriptNode::load()
{
	throw IECore::Exception( "Cannot load scripts on a ScriptNode not created in Python." );
}

void ScriptNode::save() const
{
	throw IECore::Exception( "Cannot save scripts on a ScriptNode not created in Python." );
}

Context *ScriptNode::context()
{
	return m_context.get();
}

const Context *ScriptNode::context() const
{
	return m_context.get();
}

IntPlug *ScriptNode::frameStartPlug()
{
	return getChild<CompoundPlug>( "frameRange" )->getChild<IntPlug>( "start" );
}

const IntPlug *ScriptNode::frameStartPlug() const
{
	return getChild<CompoundPlug>( "frameRange" )->getChild<IntPlug>( "start" );
}

IntPlug *ScriptNode::frameEndPlug()
{
	return getChild<CompoundPlug>( "frameRange" )->getChild<IntPlug>( "end" );
}

const IntPlug *ScriptNode::frameEndPlug() const
{
	return getChild<CompoundPlug>( "frameRange" )->getChild<IntPlug>( "end" );
}

void ScriptNode::childRemoved( GraphComponent *parent, GraphComponent *child )
{
	m_selection->remove( child );
}

void ScriptNode::plugSet( Plug *plug )
{
	/// \todo Should we introduce some plug constraints classes to assist in managing these
	/// kinds of relationships?
	if( plug == frameStartPlug() )
	{
		frameEndPlug()->setValue( std::max( frameEndPlug()->getValue(), frameStartPlug()->getValue() ) );
	}
	else if( plug == frameEndPlug() )
	{
		frameStartPlug()->setValue( std::min( frameStartPlug()->getValue(), frameEndPlug()->getValue() ) );	
	}
}
