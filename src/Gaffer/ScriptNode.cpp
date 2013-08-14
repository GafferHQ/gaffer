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
#include "boost/filesystem/path.hpp"
#include "boost/filesystem/convenience.hpp"

#include "IECore/Exception.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/MessageHandler.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/Action.h"
#include "Gaffer/ApplicationRoot.h"
#include "Gaffer/Context.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/CompoundDataPlug.h"

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// ScriptContainer implementation
//////////////////////////////////////////////////////////////////////////

namespace Gaffer
{

GAFFER_DECLARECONTAINERSPECIALISATIONS( ScriptContainer, ScriptContainerTypeId )

}

//////////////////////////////////////////////////////////////////////////
// CompoundAction implementation. We use this to group up all the actions
// that will become a single undo/redo event.
//////////////////////////////////////////////////////////////////////////

class ScriptNode::CompoundAction : public Gaffer::Action
{

	public :
	
		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::ScriptNode::CompoundAction, CompoundActionTypeId, Gaffer::Action );

		CompoundAction( ScriptNode *subject, const std::string &mergeGroup )
			:	m_subject( subject ), m_mergeGroup( mergeGroup )
		{
		}
		
		void addAction( ActionPtr action )
		{
			m_actions.push_back( action );
		}
		
		size_t numActions() const
		{
			return m_actions.size();
		}
		
	protected :

		friend class ScriptNode;

		virtual GraphComponent *subject() const
		{
			return m_subject;
		}
		
		virtual void doAction()
		{
			for( std::vector<ActionPtr>::const_iterator it = m_actions.begin(), eIt = m_actions.end(); it != eIt; ++it )
			{
				(*it)->doAction();
				// we know we're only ever being redone, because the ScriptNode::addAction()
				// performs the original Do.
				m_subject->actionSignal()( m_subject, it->get(), Action::Redo );
			}
		}
		
		virtual void undoAction()
		{
			for( std::vector<ActionPtr>::const_reverse_iterator it = m_actions.rbegin(), eIt = m_actions.rend(); it != eIt; ++it )
			{
				(*it)->undoAction();
				m_subject->actionSignal()( m_subject, it->get(), Action::Undo );
			}
		}
		
		virtual bool canMerge( const Action *other ) const
		{
			if( !Action::canMerge( other ) )
			{
				return false;
			}
			
			if( !m_mergeGroup.size() )
			{
				return false;
			}
			
			const CompoundAction *compoundAction = IECore::runTimeCast<const CompoundAction>( other );
			if( !compoundAction )
			{
				return false;
			}
			
			if( m_mergeGroup != compoundAction->m_mergeGroup )
			{
				return false;
			}
			
			if( m_actions.size() != compoundAction->m_actions.size() )
			{
				return false;
			}
			
			for( size_t i = 0, e = m_actions.size(); i < e; ++i )
			{
				if( !m_actions[i]->canMerge( compoundAction->m_actions[i] ) )
				{
					return false;
				}
			}
			
			return true;
		}
		
		virtual void merge( const Action *other )
		{
			const CompoundAction *compoundAction = static_cast<const CompoundAction *>( other );
			for( size_t i = 0, e = m_actions.size(); i < e; ++i )
			{
				m_actions[i]->merge( compoundAction->m_actions[i] );
			}
		}

	private :

		// this can't be a smart pointer because then we'd get
		// a reference cycle between us and the script.
		ScriptNode *m_subject;
		std::string m_mergeGroup;
		std::vector<ActionPtr> m_actions;
		
};

IE_CORE_DEFINERUNTIMETYPED( ScriptNode::CompoundAction );

//////////////////////////////////////////////////////////////////////////
// ScriptNode implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ScriptNode );

size_t ScriptNode::g_firstPlugIndex = 0;

ScriptNode::ScriptNode( const std::string &name )
	:
	Node( name ),
	m_selection( new StandardSet ),
	m_selectionOrphanRemover( m_selection ),
	m_undoIterator( m_undoList.end() ),
	m_currentActionStage( Action::Invalid ),
	m_context( new Context )
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
	
	addChild( new CompoundDataPlug( "variables" ) );
	
	m_context->set( "script:name", std::string( "" ) );
	
	m_selection->memberAcceptanceSignal().connect( boost::bind( &ScriptNode::selectionSetAcceptor, this, ::_1, ::_2 ) );

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

void ScriptNode::pushUndoState( UndoContext::State state, const std::string &mergeGroup )
{
	if( m_undoStateStack.size() == 0 )
	{
		assert( m_actionAccumulator==0 );
		m_actionAccumulator = new CompoundAction( this, mergeGroup );
		m_currentActionStage = Action::Do;
	}
	m_undoStateStack.push( state );
}

void ScriptNode::addAction( ActionPtr action )
{
	action->doAction();
	if( m_actionAccumulator && m_undoStateStack.top() == UndoContext::Enabled )
	{
		m_actionAccumulator->addAction( action );
		actionSignal()( this, action.get(), Action::Do );
	}
}

void ScriptNode::popUndoState()
{
	if( !m_undoStateStack.size() )
	{
		IECore::msg( IECore::Msg::Warning, "ScriptNode::popUndoState", "Bad undo stack nesting detected" );
		return;
	}
	
	m_undoStateStack.pop();
	
	if( m_undoStateStack.size()==0 )
	{
		if( m_actionAccumulator->numActions() )
		{
			m_undoList.erase( m_undoIterator, m_undoList.end() );
			
			bool merged = false;
			if( !m_undoList.empty() )
			{
				CompoundAction *lastAction = m_undoList.rbegin()->get();
				if( lastAction->canMerge( m_actionAccumulator ) )
				{
					lastAction->merge( m_actionAccumulator );
					merged = true;
				}
			}
			
			if( !merged )
			{
				m_undoList.insert( m_undoList.end(), m_actionAccumulator );		
			}
			
			m_undoIterator = m_undoList.end();
			
			if( !merged )
			{
				undoAddedSignal()( this );
			}
			
			UndoContext undoDisabled( this, UndoContext::Disabled );
			unsavedChangesPlug()->setValue( true );
		}
		m_actionAccumulator = 0;
		m_currentActionStage = Action::Invalid;
	}
	
}	

bool ScriptNode::undoAvailable() const
{
	return m_currentActionStage == Action::Invalid && m_undoIterator != m_undoList.begin();
}

void ScriptNode::undo()
{
	if( !undoAvailable() )
	{
		throw IECore::Exception( "Undo not available" );
	}
	
	m_currentActionStage = Action::Undo;
	
		m_undoIterator--;
		(*m_undoIterator)->undoAction();

	/// \todo It's conceivable that an exception from somewhere in
	/// Action::undoAction() could prevent this cleanup code from running,
	/// leaving us in a bad state. This could perhaps be addressed
	/// by using BOOST_SCOPE_EXIT. The most likely cause of such an
	/// exception would be in an errant slot connected to a signal
	/// triggered by the action performed. However, currently most
	/// python slot callers suppress python exceptions (printing
	/// them to the shell), so it's not even straightforward to
	/// write a test case for this potential problem. It could be
	/// argued that we shouldn't be suppressing exceptions in slots,
	/// but if we don't then well-behaved (and perhaps crucial) slots
	/// might not get called when badly behaved slots mess up. It seems
	/// best to simply report errors as we do, and allow the well behaved
	/// slots to have their turn - we might even want to extend this
	/// behaviour to the c++ slots.
	m_currentActionStage = Action::Invalid;
	
	UndoContext undoDisabled( this, UndoContext::Disabled );
	unsavedChangesPlug()->setValue( true );
}

bool ScriptNode::redoAvailable() const
{
	return m_currentActionStage == Action::Invalid && m_undoIterator != m_undoList.end();
}

void ScriptNode::redo()
{
	if( !redoAvailable() )
	{
		throw IECore::Exception( "Redo not available" );
	}
	
	m_currentActionStage = Action::Redo;

		(*m_undoIterator)->doAction();
		m_undoIterator++;

	m_currentActionStage = Action::Invalid;
	
	UndoContext undoDisabled( this, UndoContext::Disabled );
	unsavedChangesPlug()->setValue( true );
}

Action::Stage ScriptNode::currentActionStage() const
{
	return m_currentActionStage;
}

ScriptNode::ActionSignal &ScriptNode::actionSignal()
{
	return m_actionSignal;
}

ScriptNode::UndoAddedSignal &ScriptNode::undoAddedSignal()
{
	return m_undoAddedSignal;
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
					
					// record this plug's current outputs, and reconnect them. This is a copy of (*it)->outputs() rather
					// than a reference, as reconnection can modify (*it)->outputs()...
					Plug::OutputContainer outputs = (*it)->outputs();
					for ( Plug::OutputContainer::const_iterator oIt = outputs.begin(); oIt != outputs.end(); )
					{
						Plug *dstPlug = *oIt;
						if ( dstPlug && dstPlug->acceptsInput( srcPlug ) && this->isAncestorOf( dstPlug ) )
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

CompoundDataPlug *ScriptNode::variablesPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 3 );
}

const CompoundDataPlug *ScriptNode::variablesPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 3 );
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

void ScriptNode::plugSet( Plug *plug )
{
	/// \todo Implement this min/max behaviour enforcement as a Behaviour subclass.
	if( plug == frameStartPlug() )
	{
		frameEndPlug()->setValue( std::max( frameEndPlug()->getValue(), frameStartPlug()->getValue() ) );
	}
	else if( plug == frameEndPlug() )
	{
		frameStartPlug()->setValue( std::min( frameStartPlug()->getValue(), frameEndPlug()->getValue() ) );	
	}
	else if( plug == variablesPlug() )
	{
		IECore::CompoundDataMap values;
		variablesPlug()->fillCompoundData( values );
		for( IECore::CompoundDataMap::const_iterator it = values.begin(), eIt = values.end(); it != eIt; ++it )
		{
			context()->set( it->first, it->second.get() );
		}
	}
	else if( plug == fileNamePlug() )
	{
		boost::filesystem::path fileName( fileNamePlug()->getValue() );
		context()->set( "script:name", boost::filesystem::basename( fileName ) );
	}
}
