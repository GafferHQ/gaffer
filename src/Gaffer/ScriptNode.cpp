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

#include "Gaffer/ScriptNode.h"

#include "Gaffer/Action.h"
#include "Gaffer/ApplicationRoot.h"
#include "Gaffer/BackgroundTask.h"
#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/Container.inl"
#include "Gaffer/Context.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/Exception.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/filesystem/convenience.hpp"
#include "boost/filesystem/path.hpp"

#include <fstream>

#include <unistd.h>

using namespace boost::placeholders;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// ScriptContainer implementation
//////////////////////////////////////////////////////////////////////////

namespace Gaffer
{

GAFFER_DECLARECONTAINERSPECIALISATIONS( ScriptContainer, ScriptContainerTypeId )
template class Container<GraphComponent, ScriptNode>;

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

		GraphComponent *subject() const override
		{
			return m_subject;
		}

		void doAction() override
		{
			for( std::vector<ActionPtr>::const_iterator it = m_actions.begin(), eIt = m_actions.end(); it != eIt; ++it )
			{
				(*it)->doAction();
				// we know we're only ever being redone, because the ScriptNode::addAction()
				// performs the original Do.
				m_subject->actionSignal()( m_subject, it->get(), Action::Redo );
			}
		}

		void undoAction() override
		{
			for( std::vector<ActionPtr>::const_reverse_iterator it = m_actions.rbegin(), eIt = m_actions.rend(); it != eIt; ++it )
			{
				(*it)->undoAction();
				m_subject->actionSignal()( m_subject, it->get(), Action::Undo );
			}
		}

		bool canMerge( const Action *other ) const override
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

			return m_mergeGroup == compoundAction->m_mergeGroup;
		}

		void merge( const Action *other ) override
		{
			const CompoundAction *compoundAction = static_cast<const CompoundAction *>( other );

			bool canMergeChildActions = false;
			if( m_actions.size() == compoundAction->m_actions.size() )
			{
				canMergeChildActions = true;
				for( size_t i = 0, e = m_actions.size(); i < e; ++i )
				{
					if( !m_actions[i]->canMerge( compoundAction->m_actions[i].get() ) )
					{
						canMergeChildActions = false;
						break;
					}
				}
			}

			if( canMergeChildActions )
			{
				for( size_t i = 0, e = m_actions.size(); i < e; ++i )
				{
					m_actions[i]->merge( compoundAction->m_actions[i].get() );
				}
			}
			else
			{
				for( std::vector<ActionPtr>::const_iterator it = compoundAction->m_actions.begin(), eIt = compoundAction->m_actions.end(); it != eIt; ++it )
				{
					m_actions.push_back( *it );
				}
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
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

std::string readFile( const std::string &fileName )
{
	std::ifstream f( fileName.c_str() );
	if( !f.good() )
	{
		throw IECore::IOException( "Unable to open file \"" + fileName + "\"" );
	}

	const IECore::Canceller *canceller = Context::current()->canceller();

	std::string s;
	while( !f.eof() )
	{
		IECore::Canceller::check( canceller );
		if( !f.good() )
		{
			throw IECore::IOException( "Failed to read from \"" + fileName + "\"" );
		}

		std::string line;
		std::getline( f, line );
		s += line + "\n";
	}

	return s;
}

const IECore::InternedString g_scriptName( "script:name" );
const IECore::InternedString g_frame( "frame" );
const IECore::InternedString g_frameStart( "frameRange:start" );
const IECore::InternedString g_frameEnd( "frameRange:end" );
const IECore::InternedString g_framesPerSecond( "framesPerSecond" );

} // namespace

class ScriptNode::FocusSet : public Gaffer::Set
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::ScriptNode::FocusSet, ScriptNodeFocusSetTypeId, Gaffer::Set );

		void setNode( Node *node )
		{
			if( node != m_node )
			{
				if( m_node )
				{
					NodePtr oldNode = m_node;
					m_node.reset();
					oldNode->parentChangedSignal().disconnect( boost::bind( &FocusSet::parentChanged, this, ::_1, ::_2 ) );
					memberRemovedSignal()( this, oldNode.get() );
				}

				m_node = node;

				if( node )
				{
					node->parentChangedSignal().connect( boost::bind( &FocusSet::parentChanged, this, ::_1, ::_2 ) );
					memberAddedSignal()( this, node );
				}
			}
		}

		Node *getNode() const
		{
			return m_node.get();
		}

		/// @name Set interface
		////////////////////////////////////////////////////////////////////
		//@{
		bool contains( const Member *object ) const override
		{
			return m_node && m_node.get() == object;
		}

		Member *member( size_t index ) override
		{
			return m_node.get();
		}

		const Member *member( size_t index ) const override
		{
			return m_node.get();
		}

		size_t size() const override
		{
			return m_node ? 1 : 0;
		}
		//@}

	private :

		void parentChanged( GraphComponent *member, GraphComponent *oldParent )
		{
			assert( member == m_node );
			if( !m_node->parent() )
			{
				setNode( nullptr );
				ScriptNode *script = IECore::runTimeCast<ScriptNode>( oldParent );
				if( !script )
				{
					script = oldParent->ancestor<ScriptNode>();
				}
				if( script )
				{
					script->focusChangedSignal()( script, nullptr );
				}
			}
		}

		Gaffer::NodePtr m_node;
};


//////////////////////////////////////////////////////////////////////////
// ScriptNode implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ScriptNode );

size_t ScriptNode::g_firstPlugIndex = 0;
ScriptNode::SerialiseFunction ScriptNode::g_serialiseFunction;
ScriptNode::ExecuteFunction ScriptNode::g_executeFunction;

ScriptNode::ScriptNode( const std::string &name )
	:
	Node( name ),
	m_selection( new StandardSet( /* removeOrphans = */ true ) ),
	m_focus( new FocusSet() ),
	m_undoIterator( m_undoList.end() ),
	m_currentActionStage( Action::Invalid ),
	m_executing( false ),
	m_context( new Context )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "fileName", Plug::In, "", Plug::Default & ~Plug::Serialisable ) );
	addChild( new BoolPlug( "unsavedChanges", Plug::In, false, Plug::Default & ~Plug::Serialisable ) );

	ValuePlugPtr frameRangePlug = new ValuePlug( "frameRange", Plug::In );
	IntPlugPtr frameStartPlug = new IntPlug( "start", Plug::In, 1 );
	IntPlugPtr frameEndPlug = new IntPlug( "end", Plug::In, 100 );
	frameRangePlug->addChild( frameStartPlug );
	frameRangePlug->addChild( frameEndPlug );
	addChild( frameRangePlug );

	addChild( new FloatPlug( "frame", Plug::In, 1.0f ) );
	addChild( new FloatPlug( "framesPerSecond", Plug::In, 24.0f, 0.0f ) );
	addChild( new CompoundDataPlug( "variables" ) );

	m_context->set( g_scriptName, std::string( "" ) );
	m_context->set( g_frameStart, 1 );
	m_context->set( g_frameEnd, 100 );

	m_selection->memberAcceptanceSignal().connect( boost::bind( &ScriptNode::selectionSetAcceptor, this, ::_1, ::_2 ) );

	plugSetSignal().connect( boost::bind( &ScriptNode::plugSet, this, ::_1 ) );
	m_context->changedSignal().connect( boost::bind( &ScriptNode::contextChanged, this, ::_1, ::_2 ) );
}

ScriptNode::~ScriptNode()
{
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

IntPlug *ScriptNode::frameStartPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 )->getChild<IntPlug>( 0 );
}

const IntPlug *ScriptNode::frameStartPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 )->getChild<IntPlug>( 0 );
}

IntPlug *ScriptNode::frameEndPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 )->getChild<IntPlug>( 1 );
}

const IntPlug *ScriptNode::frameEndPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 )->getChild<IntPlug>( 1 );
}

FloatPlug *ScriptNode::framePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const FloatPlug *ScriptNode::framePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

FloatPlug *ScriptNode::framesPerSecondPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const FloatPlug *ScriptNode::framesPerSecondPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

CompoundDataPlug *ScriptNode::variablesPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 5 );
}

const CompoundDataPlug *ScriptNode::variablesPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex + 5 );
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

void ScriptNode::parentChanging( Gaffer::GraphComponent *newParent )
{
	if( !newParent )
	{
		BackgroundTask::cancelAffectedTasks( this );
	}
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
	return m_selection.get();
}

void ScriptNode::setFocus( Node *node )
{
	if( node == m_focus->getNode() )
	{
		return;
	}
	if( node && !this->isAncestorOf( node ) )
	{
		throw IECore::Exception( boost::str( boost::format( "%s is not a child of this script" ) % node->fullName() ) );
	}
	m_focus->setNode( node );
	focusChangedSignal()( this, node );
}

Node *ScriptNode::getFocus()
{
	return m_focus->getNode();
}

const Node *ScriptNode::getFocus() const
{
	return m_focus->getNode();
}

ScriptNode::FocusChangedSignal &ScriptNode::focusChangedSignal()
{
	return m_focusChangedSignal;
}

Set *ScriptNode::focusSet()
{
	return m_focus.get();
}

const Set *ScriptNode::focusSet() const
{
	return m_focus.get();
}

void ScriptNode::pushUndoState( UndoScope::State state, const std::string &mergeGroup )
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
	if( m_actionAccumulator && m_undoStateStack.top() == UndoScope::Enabled )
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

	bool haveUnsavedChanges = false;
	if( m_undoStateStack.size()==0 )
	{
		if( m_actionAccumulator->numActions() )
		{
			m_undoList.erase( m_undoIterator, m_undoList.end() );

			bool merged = false;
			if( !m_undoList.empty() )
			{
				CompoundAction *lastAction = m_undoList.rbegin()->get();
				if( lastAction->canMerge( m_actionAccumulator.get() ) )
				{
					lastAction->merge( m_actionAccumulator.get() );
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

			haveUnsavedChanges = true;
		}
		m_actionAccumulator = nullptr;
		m_currentActionStage = Action::Invalid;
	}

	if( haveUnsavedChanges )
	{
		UndoScope undoDisabled( this, UndoScope::Disabled );
		unsavedChangesPlug()->setValue( true );
	}

}

void ScriptNode::postActionStageCleanup()
{
	m_currentActionStage = Action::Invalid;

	UndoScope undoDisabled( this, UndoScope::Disabled );
	unsavedChangesPlug()->setValue( true );
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

	DirtyPropagationScope dirtyPropagationScope;

	m_currentActionStage = Action::Undo;

	try
	{
		// NOTE : Decrement the undo iterator if undoAction() completes without throwing an exception

		UndoIterator it = m_undoIterator;
		(*(--it))->undoAction();
		m_undoIterator = it;
	}
	catch( ... )
	{
		postActionStageCleanup();
		throw;
	}

	postActionStageCleanup();
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

	DirtyPropagationScope dirtyPropagationScope;

	m_currentActionStage = Action::Redo;

	try
	{
		(*m_undoIterator)->doAction();
		++m_undoIterator;
	}
	catch( ... )
	{
		postActionStageCleanup();
		throw;
	}

	postActionStageCleanup();
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

void ScriptNode::paste( Node *parent, bool continueOnError )
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
			execute( s->readable(), parent, continueOnError );

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
			if( reconnect && dependencyNode )
			{
				for( Plug::RecursiveOutputIterator it( node ); !it.done(); ++it )
				{
					Plug *inPlug = nullptr;
					try
					{
						inPlug = dependencyNode->correspondingInput( it->get() );
					}
					catch( const std::exception &e )
					{
						msg(
							IECore::Msg::Warning,
							boost::str( boost::format( "correspondingInput error while deleting - cannot reconnect \"%s\"" ) % it->get()->fullName() ),
							e.what()
						);
					}

					if ( !inPlug )
					{
						continue;
					}

					Plug *srcPlug = inPlug->getInput();
					if ( !srcPlug )
					{
						continue;
					}

					// record this plug's current outputs, and reconnect them. This is a copy of (*it)->outputs() rather
					// than a reference, as reconnection can modify (*it)->outputs()...
					Plug::OutputContainer outputs = (*it)->outputs();
					for ( Plug::OutputContainer::const_iterator oIt = outputs.begin(); oIt != outputs.end(); ++oIt )
					{
						Plug *dstPlug = *oIt;
						if ( dstPlug && dstPlug->acceptsInput( srcPlug ) && this->isAncestorOf( dstPlug ) )
						{
							dstPlug->setInput( srcPlug );
						}
					}
				}
			}

			parent->removeChild( node );
		}
		i--;
	}
}

bool ScriptNode::isExecuting() const
{
	return m_executing;
}

std::string ScriptNode::serialise( const Node *parent, const Set *filter ) const
{
	return serialiseInternal( parent, filter );
}

void ScriptNode::serialiseToFile( const std::string &fileName, const Node *parent, const Set *filter ) const
{
	std::string s = serialiseInternal( parent, filter );

	std::ofstream f( fileName.c_str() );
	if( !f.good() )
	{
		throw IECore::IOException( "Unable to open file \"" + fileName + "\"" );
	}

	f << s;

	if( !f.good() )
	{
		throw IECore::IOException( "Failed to write to \"" + fileName + "\"" );
	}
}

bool ScriptNode::execute( const std::string &serialisation, Node *parent, bool continueOnError )
{
	return executeInternal( serialisation, parent, continueOnError, "" );
}

bool ScriptNode::executeFile( const std::string &fileName, Node *parent, bool continueOnError )
{
	const std::string serialisation = readFile( fileName );
	return executeInternal( serialisation, parent, continueOnError, fileName );
}

bool ScriptNode::load( bool continueOnError)
{
	DirtyPropagationScope dirtyScope;

	const std::string fileName = fileNamePlug()->getValue();
	const std::string s = readFile( fileName );

	deleteNodes();
	variablesPlug()->clearChildren();

	const bool result = executeInternal( s, nullptr, continueOnError, fileName );

	UndoScope undoDisabled( this, UndoScope::Disabled );
	unsavedChangesPlug()->setValue( false );

	return result;
}

void ScriptNode::save() const
{
	// Caution : `FileMenu.save()` currently contains a duplicate of this code,
	// so that `serialiseToFile()` can be done in a background task, and the
	// plug edit can be made on the UI thread. If editing this function, make
	// sure FileMenu stays in sync.
	serialiseToFile( fileNamePlug()->getValue() );
	UndoScope undoDisabled( const_cast<ScriptNode *>( this ), UndoScope::Disabled );
	const_cast<BoolPlug *>( unsavedChangesPlug() )->setValue( false );
}

bool ScriptNode::importFile( const std::string &fileName, Node *parent, bool continueOnError )
{
	DirtyPropagationScope dirtyScope;

	ScriptNodePtr script = new ScriptNode();
	script->fileNamePlug()->setValue( fileName );
	bool result = script->load( continueOnError );

	StandardSetPtr nodeSet = new StandardSet();
	nodeSet->add( Node::Iterator( script.get() ), Node::Iterator( script->children().end(), script->children().end() ) );
	const std::string nodeSerialisation = script->serialise( script.get(), nodeSet.get() );

	result |= execute( nodeSerialisation, parent, continueOnError );

	return result;
}

std::string ScriptNode::serialiseInternal( const Node *parent, const Set *filter ) const
{
	if( !g_serialiseFunction )
	{
		throw IECore::Exception( "Serialisation not available - please link to libGafferBindings." );
	}
	return g_serialiseFunction( parent ? parent : this, filter );
}

bool ScriptNode::executeInternal( const std::string &serialisation, Node *parent, bool continueOnError, const std::string &context )
{
	if( !g_executeFunction )
	{
		throw IECore::Exception( "Execution not available - please link to libGafferBindings." );
	}
	DirtyPropagationScope dirtyScope;
	bool result = false;
	bool wasExecuting = m_executing;

	m_executing = true;
	try
	{
		result = g_executeFunction( this, serialisation, parent ? parent : this, continueOnError, context );
	}
	catch( ... )
	{
		m_executing = wasExecuting;
		throw;
	}
	m_executing = wasExecuting;
	return result;
}

Context *ScriptNode::context()
{
	return m_context.get();
}

const Context *ScriptNode::context() const
{
	return m_context.get();
}

void ScriptNode::updateContextVariables()
{
	// Get contents of `variablesPlug()` and remove any previously transferred
	// variables that no longer exist.
	IECore::CompoundDataMap values;
	variablesPlug()->fillCompoundData( values );
	for( auto name : m_currentVariables )
	{
		if( values.find( name ) == values.end() )
		{
			context()->remove( name );
		}
	}

	// Transfer current variables and remember what we've done.
	m_currentVariables.clear();
	for( const auto &variable : values )
	{
		context()->set( variable.first, variable.second.get() );
		m_currentVariables.insert( variable.first );
	}
}

void ScriptNode::plugSet( Plug *plug )
{
	if( plug == frameStartPlug() )
	{
		frameEndPlug()->setValue( std::max( frameEndPlug()->getValue(), frameStartPlug()->getValue() ) );
		context()->set( g_frameStart, frameStartPlug()->getValue() );
	}
	else if( plug == frameEndPlug() )
	{
		frameStartPlug()->setValue( std::min( frameStartPlug()->getValue(), frameEndPlug()->getValue() ) );
		context()->set( g_frameEnd, frameEndPlug()->getValue() );
	}
	else if( plug == framePlug() )
	{
		context()->setFrame( framePlug()->getValue() );
	}
	else if( plug == framesPerSecondPlug() )
	{
		context()->setFramesPerSecond( framesPerSecondPlug()->getValue() );
	}
	else if( plug == variablesPlug() )
	{
		updateContextVariables();
	}
	else if( plug == fileNamePlug() )
	{
		const boost::filesystem::path fileName( fileNamePlug()->getValue() );
		context()->set( g_scriptName, fileName.stem().string() );
		MetadataAlgo::setReadOnly(
			this,
			boost::filesystem::exists( fileName ) && 0 != access( fileName.c_str(), W_OK ),
			/* persistent = */ false
		);
	}
}

void ScriptNode::contextChanged( const Context *context, const IECore::InternedString &name )
{
	if( name == g_frame )
	{
		framePlug()->setValue( context->getFrame() );
	}
	else if( name == g_framesPerSecond )
	{
		framesPerSecondPlug()->setValue( context->getFramesPerSecond() );
	}
	/// \todo Emit a warning if manual changes are made that
	/// wouldn't be preserved across save/load.
}
