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

#include "boost/python.hpp" // must be the first include

#include <fstream>

#include "IECore/MessageHandler.h"

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/Context.h"
#include "Gaffer/ApplicationRoot.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/CompoundDataPlug.h"

#include "GafferBindings/ScriptNodeBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/ExceptionAlgo.h"

extern "C"
{
// essential to include this last, since it defines macros which
// clash with other headers.
#include "Python-ast.h"
};

namespace boost {
namespace python {

// Specialisation to allow use of handle<PyCodeObject>
template<>
struct base_type_traits<PyCodeObject>
{
	typedef PyObject type;
};

} // namespace python
} // namespace boost

using namespace Gaffer;
using namespace GafferBindings;

namespace
{

/// The ScriptNodeWrapper class implements the scripting
/// components of the ScriptNode base class. In this way
/// scripting is available provided that the ScriptNode was
/// created from python.
class ScriptNodeWrapper : public NodeWrapper<ScriptNode>
{

	public :

		ScriptNodeWrapper( PyObject *self, const std::string &name )
			:	NodeWrapper<ScriptNode>( self, name )
		{
		}

		virtual ~ScriptNodeWrapper()
		{
		}

		virtual bool isInstanceOf( IECore::TypeId typeId ) const
		{
			if( typeId == (IECore::TypeId)Gaffer::ScriptNodeTypeId )
			{
				// Correct for the slightly overzealous (but hugely beneficial)
				// optimisation in NodeWrapper::isInstanceOf().
				return true;
			}
			return NodeWrapper<ScriptNode>::isInstanceOf( typeId );
		}

		virtual bool execute( const std::string &pythonScript, Node *parent = 0, bool continueOnError = false )
		{
			IECorePython::ScopedGILLock gilLock;
			boost::python::object e = executionDict( parent );

			bool result = false;
			if( !continueOnError )
			{
				exec( pythonScript.c_str(), e, e );
			}
			else
			{
				result = tolerantExec( pythonScript.c_str(), e, e );
			}

			scriptExecutedSignal()( this, pythonScript );
			return result;
		}

		bool executeFile( const std::string &pythonFile, Node *parent = 0, bool continueOnError = false )
		{
			const std::string pythonScript = readFile( pythonFile );
			return execute( pythonScript, parent, continueOnError );
		}

		virtual PyObject *evaluate( const std::string &pythonExpression, Node *parent = 0 )
		{
			IECorePython::ScopedGILLock gilLock;
			boost::python::object e = executionDict( parent );
			boost::python::object result = eval( pythonExpression.c_str(), e, e );
			scriptEvaluatedSignal()( this, pythonExpression, result.ptr() );

			// make a reference to keep the result alive - the caller then
			// assumes responsibility for dealing with this
			Py_XINCREF( result.ptr() );
			return result.ptr();
		}

		virtual std::string serialise( const Node *parent = 0, const Set *filter = 0 ) const
		{
			Serialisation serialisation( parent ? parent : this, "parent", filter );
			return serialisation.result();
		}

		virtual void serialiseToFile( const std::string &fileName, const Node *parent, const Set *filter ) const
		{
			std::string s = serialise( parent, filter );

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

		virtual bool load( bool continueOnError = false )
		{
			const std::string s = readFile( fileNamePlug()->getValue() );

			deleteNodes();
			variablesPlug()->clearChildren();

			const bool result = execute( s, NULL, continueOnError );

			UndoContext undoDisabled( this, UndoContext::Disabled );
			unsavedChangesPlug()->setValue( false );

			return result;
		}

		virtual void save() const
		{
			serialiseToFile( fileNamePlug()->getValue(), 0, 0 );
			UndoContext undoDisabled( const_cast<ScriptNodeWrapper *>( this ), UndoContext::Disabled );
			const_cast<BoolPlug *>( unsavedChangesPlug() )->setValue( false );
		}

	private :

		std::string readFile( const std::string &fileName )
		{
			std::ifstream f( fileName.c_str() );
			if( !f.good() )
			{
				throw IECore::IOException( "Unable to open file \"" + fileName + "\"" );
			}

			std::string s;
			while( !f.eof() )
			{
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

		// the dict returned will form both the locals and the globals for the execute()
		// and evaluate() methods. it's not possible to have a separate locals
		// and globals dictionary and have things work as intended. see
		// ScriptNodeTest.testClassScope() for an example, and
		// http://bugs.python.org/issue991196 for an explanation.
		boost::python::object executionDict( Node *parent )
		{
			boost::python::dict result;

			boost::python::object builtIn = boost::python::import( "__builtin__" );
			result["__builtins__"] = builtIn;

			boost::python::object gafferModule = boost::python::import( "Gaffer" );
			result["Gaffer"] = gafferModule;

			result["script"] = boost::python::object( ScriptNodePtr( this ) );
			result["parent"] = boost::python::object( NodePtr( parent ? parent : this ) );

			return result;
		}

		// Execute the script one top level statement at a time,
		// reporting errors that occur, but otherwise continuing
		// with execution.
		/////////////////////////////////////////////////////////
		bool tolerantExec( const char *pythonScript, boost::python::object globals, boost::python::object locals )
		{
			// The python parsing framework uses an arena to simplify memory allocation,
			// which is handy for us, since we're going to manipulate the AST a little.
			boost::shared_ptr<PyArena> arena( PyArena_New(), PyArena_Free );

			// Parse the whole script, getting an abstract syntax tree for a
			// module which would execute everything.
			mod_ty mod = PyParser_ASTFromString(
				pythonScript,
				"<string>",
				Py_file_input,
				NULL,
				arena.get()
			);

			assert( mod->kind == Module_kind );

			// Loop over the top-level statements in the module body,
			// executing one at a time.
			bool result = false;
			int numStatements = asdl_seq_LEN( mod->v.Module.body );
			for( int i=0; i<numStatements; ++i )
			{
				// Make a new module containing just this one statement.
				asdl_seq *newBody = asdl_seq_new( 1, arena.get() );
				asdl_seq_SET( newBody, 0, asdl_seq_GET( mod->v.Module.body, i ) );
				mod_ty newModule = Module(
					newBody,
					arena.get()
				);

				// Compile it.
				boost::python::handle<PyCodeObject> code( PyAST_Compile( newModule, "<string>", NULL, arena.get() ) );

				// And execute it.
				boost::python::handle<> v( boost::python::allow_null(
					PyEval_EvalCode(
						code.get(),
						globals.ptr(),
						locals.ptr()
					)
				) );

				// Report any errors.
				if( v == NULL)
				{
					int lineNumber = 0;
					std::string message = formatPythonException( /* withTraceback = */ false, &lineNumber );
					IECore::msg( IECore::Msg::Error, boost::str( boost::format( "Line %d" ) % lineNumber ), message );
					result = true;
				}
			}

			return result;
		}

};

struct ScriptEvaluatedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, ScriptNodePtr node, const std::string script, PyObject *result )
	{
		try
		{
			boost::python::object o( boost::python::handle<>( boost::python::borrowed( result ) ) );
			slot( node, script, o );
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears error status
		}
		return boost::signals::detail::unusable();
	}
};

ContextPtr context( ScriptNode &s )
{
	return s.context();
}

ApplicationRootPtr applicationRoot( ScriptNode &s )
{
	return s.applicationRoot();
}

StandardSetPtr selection( ScriptNode &s )
{
	return s.selection();
}

void undo( ScriptNode &s )
{
	IECorePython::ScopedGILRelease gilRelease;
	s.undo();
}

void redo( ScriptNode &s )
{
	IECorePython::ScopedGILRelease gilRelease;
	s.redo();
}

void deleteNodes( ScriptNode &s, Node *parent, const Set *filter, bool reconnect )
{
	IECorePython::ScopedGILRelease r;
	s.deleteNodes( parent, filter, reconnect );
}

class ScriptNodeSerialiser : public NodeSerialiser
{

	virtual bool childNeedsSerialisation( const Gaffer::GraphComponent *child ) const
	{
		if( child->isInstanceOf( Node::staticTypeId() ) )
		{
			return true;
		}
		return NodeSerialiser::childNeedsSerialisation( child );
	}

	virtual bool childNeedsConstruction( const Gaffer::GraphComponent *child ) const
	{
		if( child->isInstanceOf( Node::staticTypeId() ) )
		{
			return true;
		}
		return NodeSerialiser::childNeedsConstruction( child );
	}

};

struct ActionSlotCaller
{

	boost::signals::detail::unusable operator()( boost::python::object slot, ScriptNodePtr script, ConstActionPtr action, Action::Stage stage )
	{
		try
		{
			slot( script, boost::const_pointer_cast<Action>( action ), stage );
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}

};

struct UndoAddedSlotCaller
{

	boost::signals::detail::unusable operator()( boost::python::object slot, ScriptNodePtr script )
	{
		try
		{
			slot( script );
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}

};

} // namespace

void GafferBindings::bindScriptNode()
{
	boost::python::scope s = NodeClass<ScriptNode, ScriptNodeWrapper>()
		.def( "applicationRoot", &applicationRoot )
		.def( "selection", &selection )
		.def( "undoAvailable", &ScriptNode::undoAvailable )
		.def( "undo", &undo )
		.def( "redoAvailable", &ScriptNode::redoAvailable )
		.def( "redo", &redo )
		.def( "currentActionStage", &ScriptNode::currentActionStage )
		.def( "actionSignal", &ScriptNode::actionSignal, boost::python::return_internal_reference<1>() )
		.def( "undoAddedSignal", &ScriptNode::undoAddedSignal, boost::python::return_internal_reference<1>() )
		.def( "copy", &ScriptNode::copy, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "filter" ) = boost::python::object() ) )
		.def( "cut", &ScriptNode::cut, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "filter" ) = boost::python::object() ) )
		.def( "paste", &ScriptNode::paste, ( boost::python::arg( "parent" ) = boost::python::object() ) )
		.def( "deleteNodes", &deleteNodes, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "filter" ) = boost::python::object(), boost::python::arg( "reconnect" ) = true ) )
		.def( "execute", &ScriptNode::execute, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "continueOnError" ) = false ) )
		.def( "executeFile", &ScriptNode::executeFile, ( boost::python::arg( "fileName" ), boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "continueOnError" ) = false ) )
		.def( "evaluate", &ScriptNode::evaluate, ( boost::python::arg( "parent" ) = boost::python::object() ) )
		.def( "scriptExecutedSignal", &ScriptNode::scriptExecutedSignal, boost::python::return_internal_reference<1>() )
		.def( "scriptEvaluatedSignal", &ScriptNode::scriptEvaluatedSignal, boost::python::return_internal_reference<1>() )
		.def( "serialise", &ScriptNode::serialise, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "filter" ) = boost::python::object() ) )
		.def( "serialiseToFile", &ScriptNode::serialiseToFile, ( boost::python::arg( "fileName" ), boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "filter" ) = boost::python::object() ) )
		.def( "save", &ScriptNode::save )
		.def( "load", &ScriptNode::load, ( boost::python::arg( "continueOnError" ) = false ) )
		.def( "context", &context )
	;

	SignalBinder<ScriptNode::ActionSignal, DefaultSignalCaller<ScriptNode::ActionSignal>, ActionSlotCaller>::bind( "ActionSignal" );
	SignalBinder<ScriptNode::UndoAddedSignal, DefaultSignalCaller<ScriptNode::UndoAddedSignal>, UndoAddedSlotCaller>::bind( "UndoAddedSignal" );

	SignalBinder<ScriptNode::ScriptExecutedSignal>::bind( "ScriptExecutedSignal" );
	SignalBinder<ScriptNode::ScriptEvaluatedSignal, DefaultSignalCaller<ScriptNode::ScriptEvaluatedSignal>, ScriptEvaluatedSlotCaller>::bind( "ScriptEvaluatedSignal" );

	Serialisation::registerSerialiser( ScriptNode::staticTypeId(), new ScriptNodeSerialiser );

}
