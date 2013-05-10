//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "IECore/Exception.h"
#include "IECore/SimpleTypedData.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/Action.h"
#include "Gaffer/ApplicationRoot.h"
#include "Gaffer/Context.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/DependencyNode.h"

using namespace Gaffer;

namespace Gaffer
{

GAFFER_DECLARECONTAINERSPECIALISATIONS( ScriptContainer, ScriptContainerTypeId )

}

IE_CORE_DEFINERUNTIMETYPED( ScriptNode );

size_t ScriptNode::g_firstPlugIndex = 0;

ScriptNode::ScriptNode( const std::string &name )
	:	Node( name ), m_selection( new StandardSet ), m_undoIterator( m_undoList.end() ), m_context( new Context )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "fileName", Plug::In, "", Plug::Default & ~Plug::Serialisable ) );	
	addChild( new BoolPlug( "unsavedChanges", Plug::In, false, Plug::Default & ~Plug::Serialisable ) );
	
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

bool ScriptNode::selectionSetAcceptor( const Set *s, const Set::Member *m )
{
	const Node *n = IECore::runTimeCast<const Node>( m );
	if( !n )
	{
		return false;
	}
	return this->isAncestorOf( n );
}

StandardSet *ScriptNode::selection()
{
	return m_selection.get();
}

const StandardSet *ScriptNode::selection() const
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
		{
			UndoContext undoDisabled( this, UndoContext::Disabled );
			unsavedChangesPlug()->setValue( true );
		}
		actionSignal()( this, it->get(), Action::Undo );
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
		{
			UndoContext undoDisabled( this, UndoContext::Disabled );
			unsavedChangesPlug()->setValue( true );
		}
		actionSignal()( this, it->get(), Action::Redo );
	}
	m_undoIterator++;
}

ScriptNode::ActionSignal &ScriptNode::actionSignal()
{
	return m_actionSignal;
}

void ScriptNode::copy( const Node *parent, const Set *filter )
{
	ApplicationRoot *app = applicationRoot();
	if( !app )
	{
		throw( "ScriptNode has no ApplicationRoot" );
	}
	
	std::string s = serialise( parent, filter );
	app->setClipboardContents( new IECore::StringData( s ) );
}

void ScriptNode::cut( Node *parent, const Set *filter )
{
	copy( parent, filter );
	deleteNodes( parent, filter );
}

void ScriptNode::paste( Node *parent )
{
	ApplicationRoot *app = applicationRoot();
	if( !app )
	{
		throw( "ScriptNode has no ApplicationRoot" );
	}
	
	IECore::ConstStringDataPtr s = IECore::runTimeCast<const IECore::StringData>( app->getClipboardContents() );
	if( s )
	{
		parent = parent ? parent : this;
		// set up something to catch all the newly created nodes
		StandardSetPtr newNodes = new StandardSet;
		parent->childAddedSignal().connect( boost::bind( (bool (StandardSet::*)( IECore::RunTimeTypedPtr ) )&StandardSet::add, newNodes.get(), ::_2 ) );
			
			// do the paste
			execute( s->readable(), parent );

		// transfer the newly created nodes into the selection
		selection()->clear();
		for( size_t i = 0, e = newNodes->size(); i < e; i++ )
		{
			StandardSet::Member *member = newNodes->member( i );
			if( member->isInstanceOf( Node::staticTypeId() ) )
			{
				selection()->add( member );
			}
		}
	}
}

void ScriptNode::deleteNodes( Node *parent, const Set *filter, bool reconnect )
{
	parent = parent ? parent : this;
	// because children are stored as a vector, it's
	// much more efficient to delete those at the end before
	// those at the beginning.
	int i = (int)(parent->children().size()) - 1;
	while( i >= 0 )
	{
		Node *node = parent->getChild<Node>( i );
		if( node && ( !filter || filter->contains( node ) ) )
		{
			// reconnect the inputs and outputs as though the node was disabled
			DependencyNode *dependencyNode = IECore::runTimeCast<DependencyNode>( node );
			if( reconnect && dependencyNode && dependencyNode->enabledPlug() )
			{
				for ( OutputPlugIterator it( node ); it != it.end(); ++it )
				{
					Plug *inPlug = dependencyNode->correspondingInput( *it );
					if ( !inPlug )
					{
						continue;
					}
					
					Plug *srcPlug = inPlug->getInput<Plug>();
					if ( !srcPlug )
					{
						continue;
					}
					
					const Plug::OutputContainer &outputs = (*it)->outputs();
					for ( Plug::OutputContainer::const_iterator oIt = outputs.begin(); oIt != outputs.end(); )
					{
						Plug *dstPlug = *oIt;
						if ( dstPlug && dstPlug->acceptsInput( srcPlug ) )
						{
							oIt++;
							dstPlug->setInput( srcPlug );
						}
						else
						{
							oIt++;
						}
					}
				}
			}
			
			parent->removeChild( node );
		}
		i--;
	}
}

StringPlug *ScriptNode::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const StringPlug *ScriptNode::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

BoolPlug *ScriptNode::unsavedChangesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const BoolPlug *ScriptNode::unsavedChangesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}
		
void ScriptNode::execute( const std::string &pythonScript, Node *parent )
{
	throw IECore::Exception( "Cannot execute scripts on a ScriptNode not created in Python." );
}

void ScriptNode::executeFile( const std::string &pythonFile, Node *parent )
{
	throw IECore::Exception( "Cannot execute files on a ScriptNode not created in Python." );
}

ScriptNode::ScriptExecutedSignal &ScriptNode::scriptExecutedSignal()
{
	return m_scriptExecutedSignal;
}

PyObject *ScriptNode::evaluate( const std::string &pythonExpression, Node *parent )
{
	throw IECore::Exception( "Cannot execute scripts on a ScriptNode not created in Python." );
}

ScriptNode::ScriptEvaluatedSignal &ScriptNode::scriptEvaluatedSignal()
{
	return m_scriptEvaluatedSignal;
}

std::string ScriptNode::serialise( const Node *parent, const Set *filter ) const
{
	throw IECore::Exception( "Cannot serialise scripts on a ScriptNode not created in Python." );
}

void ScriptNode::serialiseToFile( const std::string &fileName, const Node *parent, const Set *filter ) const
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
	return getChild<CompoundPlug>( g_firstPlugIndex + 2 )->getChild<IntPlug>( 0 );
}

const IntPlug *ScriptNode::frameStartPlug() const
{
	return getChild<CompoundPlug>( g_firstPlugIndex + 2 )->getChild<IntPlug>( 0 );
}

IntPlug *ScriptNode::frameEndPlug()
{
	return getChild<CompoundPlug>( g_firstPlugIndex + 2 )->getChild<IntPlug>( 1 );
}

const IntPlug *ScriptNode::frameEndPlug() const
{
	return getChild<CompoundPlug>( g_firstPlugIndex + 2 )->getChild<IntPlug>( 1 );
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
