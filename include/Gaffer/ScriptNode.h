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

#ifndef GAFFER_SCRIPTNODE_H
#define GAFFER_SCRIPTNODE_H

#include <stack>

#include "Gaffer/Node.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/Container.h"
#include "Gaffer/Set.h"
#include "Gaffer/UndoScope.h"
#include "Gaffer/Action.h"
#include "Gaffer/Behaviours/OrphanRemover.h"

#include "GafferBindings/ScriptNodeBinding.h" // to enable friend declaration for SerialiserRegistration

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( ScriptNode );
IE_CORE_FORWARDDECLARE( ApplicationRoot );
IE_CORE_FORWARDDECLARE( Context );
IE_CORE_FORWARDDECLARE( StandardSet );
IE_CORE_FORWARDDECLARE( CompoundDataPlug );
IE_CORE_FORWARDDECLARE( StringPlug );

typedef Container<GraphComponent, ScriptNode> ScriptContainer;
IE_CORE_DECLAREPTR( ScriptContainer );

/// The ScriptNode class represents a script - that is a single collection of
/// nodes which are stored in a single file.
class ScriptNode : public Node
{

	public :

		ScriptNode( const std::string &name=defaultName<Node>() );
		virtual ~ScriptNode();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::ScriptNode, ScriptNodeTypeId, Node );

		/// Accepts parenting only to a ScriptContainer.
		virtual bool acceptsParent( const GraphComponent *potentialParent ) const;

		/// Convenience function which simply returns ancestor<ApplicationRoot>().
		ApplicationRoot *applicationRoot();
		const ApplicationRoot *applicationRoot() const;

		//! @name Selection
		/// The ScriptNode maintains a list of child Nodes which are considered
		/// to be selected - actions performing on the script can then use that
		/// selection any way they see fit.
		////////////////////////////////////////////////////////////////////
		//@{
		StandardSet *selection();
		const StandardSet *selection() const;
		//@}

		//! @name History and undo
		/// Certain methods in the graph API are undoable on request.
		/// These methods are implemented in terms of the Action class -
		/// when the methods are called an Action instance is stored in an
		/// undo list on the relevant ScriptNode so it can later be undone.
		/// To enable undo for a series of operations an UndoScope must
		/// be active while those operations are being performed.
		////////////////////////////////////////////////////////////////////
		//@{
		typedef boost::signal<void ( ScriptNode *, const Action *, Action::Stage stage )> ActionSignal;
		typedef boost::signal<void ( ScriptNode * )> UndoAddedSignal;
		bool undoAvailable() const;
		void undo();
		bool redoAvailable() const;
		void redo();
		/// Can be used to query whether the actions currently being
		/// performed on the script represent a Do, Undo or Redo.
		Action::Stage currentActionStage() const;
		/// A signal emitted after an action is performed on the script or
		/// one of its children. Note that this is only emitted for actions
		/// performed within an UndoScope.
		/// \todo Have methods on Actions to provide a textual description
		/// of what is being done, for use in Undo/Redo menu items, history
		/// displays etc.
		ActionSignal &actionSignal();
		/// A signal emitted when an item is added to the undo stack.
		UndoAddedSignal &undoAddedSignal();
		//@}

		//! @name Editing
		/// These methods provide higher level editing functions for the
		/// script.
		////////////////////////////////////////////////////////////////////
		/// Copies nodes from this script to the clipboard in the
		/// application(). Only children of the parent which are contained by
		/// the filter will be copied. If unspecified, parent defaults to
		/// the ScriptNode and if no filter is specified all children will
		/// be copied.
		void copy( const Node *parent = NULL, const Set *filter = NULL );
		/// Performs a copy() and then deletes the copied nodes.
		/// \undoable
		void cut( Node *parent = NULL, const Set *filter = NULL );
		/// Pastes the contents of the global clipboard into the script below
		/// the specified parent. If parent is unspecified then it defaults
		/// to the script itself. The continueOnError argument behaves as
		/// for `execute()`.
		/// \undoable
		void paste( Node *parent = NULL, bool continueOnError = false );
		/// Removes Nodes from the parent node, making sure they are
		/// disconnected from the remaining Nodes and removed from the current
		/// selection. If unspecified then the parent defaults to the script
		/// itself. If specified then filter limits what is deleted. Note
		/// that it is also possible to call removeChild( node ) to remove
		/// nodes, and that the node will still be properly disconnected
		/// and unselected - this function is just a convenience method
		/// for efficiently deleting many nodes at once.
		/// \undoable
		void deleteNodes( Node *parent = NULL, const Set *filter = NULL, bool reconnect = true );
		//@}

		//! @name Serialisation and execution
		///
		/// Scripts may be serialised into a string form, which will rebuild
		/// the node network when executed. This process is used for both the
		/// saving and loading of scripts and for the cut and paste mechanism.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Returns a string which when executed will recreate the children
		/// of the parent and the connections between them. If unspecified, parent
		/// defaults to the ScriptNode itself. The filter may be specified to limit
		/// serialised nodes to those contained in the set.
		std::string serialise( const Node *parent = NULL, const Set *filter = NULL ) const;
		/// Calls serialise() and saves the result into the specified file.
		void serialiseToFile( const std::string &fileName, const Node *parent = NULL, const Set *filter = NULL ) const;
		/// Executes a previously generated serialisation. If continueOnError is true, then
		/// errors are reported via IECore::MessageHandler rather than as exceptions, and
		/// execution continues at the point after the error. This allows scripts to be loaded as
		/// best as possible even when certain nodes/plugs/shaders may be missing or
		/// may have been renamed. A true return value indicates that one or more errors
		/// were ignored.
		bool execute( const std::string &serialisation, Node *parent = NULL, bool continueOnError = false );
		/// As above, but loads the serialisation from the specified file.
		bool executeFile( const std::string &fileName, Node *parent = NULL, bool continueOnError = false );
		/// Returns true if a script is currently being executed. Note that
		/// `execute()`, `executeFile()`, `load()`, `importFile()` and `paste()` are all
		/// sources of execution, and there is intentionally no way of
		/// distinguishing between them.
		bool isExecuting() const;
		/// This signal is emitted following successful execution of a script.
		typedef boost::signal<void ( ScriptNodePtr, const std::string )> ScriptExecutedSignal;
		ScriptExecutedSignal &scriptExecutedSignal();
		//@}

		//! @name Saving and loading
		////////////////////////////////////////////////////////////////////
		/// Returns the plug which specifies the file used in all load and save
		/// operations.
		StringPlug *fileNamePlug();
		const StringPlug *fileNamePlug() const;
		/// Returns a plug which is used to flag when the script has had changes
		/// made since the last call to save().
		BoolPlug *unsavedChangesPlug();
		const BoolPlug *unsavedChangesPlug() const;
		/// Loads the script specified in the filename plug.
		/// See execute() for a description of the continueOnError argument
		/// and the return value.
		bool load( bool continueOnError = false );
		/// Saves the script to the file specified by the filename plug.
		void save() const;
		/// Imports the nodes from the specified script, adding them to
		/// the contents of this script. See `execute()` for a description
		/// of the continueOnError argument and the return value.
		bool importFile( const std::string &fileName, Node *parent = NULL, bool continueOnError = false );
		//@}

		//! @name Computation context
		///
		/// The ScriptNode provides a default context that is
		/// driven by plug values, so that it is serialised
		/// with the script. This allows the user to :
		///
		/// - Set the frame and framesPerSecond variables
		/// - Add arbitrary variables of their own
		/// - Use a "script:name" variable generated from
		///   the filename.
		///
		/// It is expected that all computations will use a context
		/// derived from this default context, but note that this does
		/// _not_ imply that there is a single global "current time".
		/// Derived contexts may have their own frame and even framesPerSecond
		/// values, and can be used in parallel with the default context
		/// or any other context. This allows features like TimeWarp nodes
		/// and UI elements which view a different frame than the default.
		////////////////////////////////////////////////////////////////////
		//@{
		/// The default context - all computations should be performed
		/// with this context, or one derived from it.
		Context *context();
		const Context *context() const;
		/// Drives the frame variable in the context.
		///
		/// > Warning : This exists primarily as a convenience for the
		/// > user, so that the "current frame" is saved within the
		/// > script file. To perform a computation at a particular time,
		/// > create your own context rather than change the value of
		/// > this plug. Likewise, don't refer to this plug from an
		/// > expression - always use `context.getFrame()` instead.
		FloatPlug *framePlug();
		const FloatPlug *framePlug() const;
		/// Drives the framesPerSecond variable in the context.
		FloatPlug *framesPerSecondPlug();
		const FloatPlug *framesPerSecondPlug() const;
		/// All members of this plug are mapped into custom variables
		/// in the context.
		CompoundDataPlug *variablesPlug();
		const CompoundDataPlug *variablesPlug() const;
		//@}

		//! @name Frame range
		/// The ScriptNode defines the valid frame range using two numeric plugs.
		/// \todo Perhaps these should also drive context variables? It might
		/// be useful to use the frame range in expressions etc.
		////////////////////////////////////////////////////////////////////
		//@{
		IntPlug *frameStartPlug();
		const IntPlug *frameStartPlug() const;
		IntPlug *frameEndPlug();
		const IntPlug *frameEndPlug() const;
		//@}

	private :

		// Selection
		// =========

		bool selectionSetAcceptor( const Set *s, const Set::Member *m );
		StandardSetPtr m_selection;
		Behaviours::OrphanRemover m_selectionOrphanRemover;

		// Actions and undo
		// ================

		IE_CORE_FORWARDDECLARE( CompoundAction );

		friend class Action;
		friend class UndoScope;

		// Called by the UndoScope and Action classes to
		// implement the undo system.
		void pushUndoState( UndoScope::State state, const std::string &mergeGroup );
		void addAction( ActionPtr action );
		void popUndoState();

		typedef std::stack<UndoScope::State> UndoStateStack;
		typedef std::list<CompoundActionPtr> UndoList;
		typedef UndoList::iterator UndoIterator;

		ActionSignal m_actionSignal;
		UndoAddedSignal m_undoAddedSignal;
		UndoStateStack m_undoStateStack; // pushed and popped by the creation and destruction of UndoScopes
		CompoundActionPtr m_actionAccumulator; // Actions are accumulated here until the state stack hits 0 size
		UndoList m_undoList; // then the accumulated actions are transferred to this list for storage
		UndoIterator m_undoIterator; // points to the next thing to redo
		Action::Stage m_currentActionStage;

		// Serialisation and execution
		// ===========================

		std::string serialiseInternal( const Node *parent, const Set *filter ) const;
		bool executeInternal( const std::string &serialisation, Node *parent, bool continueOnError, const std::string &context = "" );

		typedef boost::function<std::string ( const Node *, const Set * )> SerialiseFunction;
		typedef boost::function<bool ( ScriptNode *, const std::string &, Node *, bool, const std::string &context )> ExecuteFunction;

		// Actual implementations reside in libGafferBindings (due to Python
		// dependency), and are injected into these functions.
		static SerialiseFunction g_serialiseFunction;
		static ExecuteFunction g_executeFunction;
		friend struct GafferBindings::SerialiserRegistration;

		bool m_executing;
		ScriptExecutedSignal m_scriptExecutedSignal;

		// Context and plugs
		// =================

		ContextPtr m_context;

		void plugSet( Plug *plug );
		void contextChanged( const Context *context, const IECore::InternedString &name );

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ScriptNode );

} // namespace Gaffer

#endif // GAFFER_SCRIPTNODE_H
