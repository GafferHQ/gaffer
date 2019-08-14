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

#include "boost/python.hpp"

#include "ScriptNodeBinding.h"

#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/ApplicationRoot.h"
#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/StringPlug.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

#include "IECore/MessageHandler.h"

#include "boost/algorithm/string/replace.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/regex.hpp"

#include <memory>

using namespace Gaffer;
using namespace GafferBindings;

//////////////////////////////////////////////////////////////////////////
// Access to Python AST
//////////////////////////////////////////////////////////////////////////

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

//////////////////////////////////////////////////////////////////////////
// Serialisation
//////////////////////////////////////////////////////////////////////////

namespace
{

const std::string formattedErrorContext( int lineNumber, const std::string &context )
{
	return boost::str(
		boost::format( "Line %d%s%s" ) %
			lineNumber %
			(!context.empty() ? " of " : "") %
			context
	);
}

// Execute the script one top level statement at a time,
// reporting errors that occur, but otherwise continuing
// with execution.
bool tolerantExec( const char *pythonScript, boost::python::object globals, boost::python::object locals, const std::string &context )
{
	// The python parsing framework uses an arena to simplify memory allocation,
	// which is handy for us, since we're going to manipulate the AST a little.
	std::unique_ptr<PyArena, decltype( &PyArena_Free )> arena( PyArena_New(), PyArena_Free );

	// Parse the whole script, getting an abstract syntax tree for a
	// module which would execute everything.
	mod_ty mod = PyParser_ASTFromString(
		pythonScript,
		"<string>",
		Py_file_input,
		nullptr,
		arena.get()
	);

	if( !mod )
	{
		int lineNumber = 0;
		std::string message = IECorePython::ExceptionAlgo::formatPythonException( /* withTraceback = */ false, &lineNumber );
		IECore::msg( IECore::Msg::Error, formattedErrorContext( lineNumber, context ), message );
		return false;
	}

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
		boost::python::handle<PyCodeObject> code( PyAST_Compile( newModule, "<string>", nullptr, arena.get() ) );

		// And execute it.
		boost::python::handle<> v( boost::python::allow_null(
			PyEval_EvalCode(
				code.get(),
				globals.ptr(),
				locals.ptr()
			)
		) );

		// Report any errors.
		if( v == nullptr)
		{
			int lineNumber = 0;
			std::string message = IECorePython::ExceptionAlgo::formatPythonException( /* withTraceback = */ false, &lineNumber );
			IECore::msg( IECore::Msg::Error, formattedErrorContext( lineNumber, context ), message );
			result = true;
		}
	}

	return result;
}

// The dict returned will form both the locals and the globals for
// the execute() methods. It's not possible to have a separate locals
// and globals dictionary and have things work as intended. See
// ScriptNodeTest.testClassScope() for an example, and
// http://bugs.python.org/issue991196 for an explanation.
boost::python::object executionDict( ScriptNodePtr script, NodePtr parent )
{
	boost::python::dict result;

	boost::python::object builtIn = boost::python::import( "__builtin__" );
	result["__builtins__"] = builtIn;

	boost::python::object gafferModule = boost::python::import( "Gaffer" );
	result["Gaffer"] = gafferModule;

	boost::python::object imathModule = boost::python::import( "imath" );
	result["imath"] = imathModule;

	result["script"] = boost::python::object( script );
	result["parent"] = boost::python::object( parent );

	return std::move( result );
}

std::string serialise( const Node *parent, const Set *filter )
{
	IECorePython::ScopedGILLock gilLock;
	if( !Py_IsInitialized() )
	{
		Py_Initialize();
	}

	std::string result;
	try
	{
		Serialisation serialisation( parent, "parent", filter );
		result = serialisation.result();
	}
	catch( boost::python::error_already_set &e )
	{
		IECorePython::ExceptionAlgo::translatePythonException();
	}

	return result;
}

std::string replaceImath( const std::string &serialisation )
{
	// Figure out the version of Gaffer which serialised the file.

	int milestoneVersion = 0;
	int majorVersion = 0;
	boost::regex milestoneVersionRegex( R"(Gaffer\.Metadata\.registerNodeValue\( parent, "serialiser:milestoneVersion", ([0-9]+), )" );
	boost::regex majorVersionRegex( R"(Gaffer\.Metadata\.registerNodeValue\( parent, "serialiser:majorVersion", ([0-9]+), )" );
	boost::match_results<const char *> matchResults;
	if( regex_search( serialisation.c_str(), matchResults, milestoneVersionRegex ) )
	{
		milestoneVersion = boost::lexical_cast<int>( matchResults.str( 1 ) );
	}
	if( regex_search( serialisation.c_str(), matchResults, majorVersionRegex ) )
	{
		majorVersion = boost::lexical_cast<int>( matchResults.str( 1 ) );
	}

	// If it's from a version which used the imath bindings
	// then we have no work to do.

	if( milestoneVersion > 0 || majorVersion >= 42 )
	{
		return serialisation;
	}

	// Otherwise we need to replace all references to imath
	// types to use the imath module rather than IECore.

	std::string result = serialisation;
	for(
		const auto &x : {
			"V2i", "V2f", "V2d",
			"V3i", "V3f", "V3d",
			"Color3f", "Color4f",
			"Box2i", "Box2f", "Box2d",
			"Box3i", "Box3f", "Box3d",
			"M33f", "M33d",
			"M44f", "M44d",
			"Eulerf", "Eulerd",
			"Plane3f", "Plane3d",
			"Quatf", "Quatd"
		}
	)
	{
		boost::replace_all( result, std::string( "IECore." ) + x + "(", std::string( "imath." ) + x + "(" );
		boost::replace_all( result, std::string( "IECore." ) + x + ".", std::string( "imath." ) + x + "." );
	}

	return result;
}

bool execute( ScriptNode *script, const std::string &serialisation, Node *parent, bool continueOnError, const std::string &context = "" )
{
	if( !Py_IsInitialized() )
	{
		Py_Initialize();
	}

	const std::string toExecute = replaceImath( serialisation );

	IECorePython::ScopedGILLock gilLock;
	bool result = false;
	try
	{
		boost::python::object e = executionDict( script, parent );

		if( !continueOnError )
		{
			try
			{
				exec( toExecute.c_str(), e, e );
			}
			catch( boost::python::error_already_set &e )
			{
				int lineNumber = 0;
				std::string message = IECorePython::ExceptionAlgo::formatPythonException( /* withTraceback = */ false, &lineNumber );
				throw IECore::Exception( formattedErrorContext( lineNumber, context ) + " : " + message );
			}
		}
		else
		{
			result = tolerantExec( toExecute.c_str(), e, e, context );
		}
	}
	catch( boost::python::error_already_set &e )
	{
		IECorePython::ExceptionAlgo::translatePythonException();
	}

	return result;
}

} // namespace

namespace GafferModule
{

struct SerialiserRegistration
{
	SerialiserRegistration()
	{
		ScriptNode::g_serialiseFunction = serialise;
		ScriptNode::g_executeFunction = execute;
	}
};

static SerialiserRegistration g_registrar;

} // namespace GafferModule

//////////////////////////////////////////////////////////////////////////
//  Bindings
//////////////////////////////////////////////////////////////////////////

namespace
{

class ScriptNodeWrapper : public NodeWrapper<ScriptNode>
{

	public :

		ScriptNodeWrapper( PyObject *self, const std::string &name )
			:	NodeWrapper<ScriptNode>( self, name )
		{
		}

		~ScriptNodeWrapper() override
		{
		}

		bool isInstanceOf( IECore::TypeId typeId ) const override
		{
			if( typeId == (IECore::TypeId)Gaffer::ScriptNodeTypeId )
			{
				// Correct for the slightly overzealous (but hugely beneficial)
				// optimisation in NodeWrapper::isInstanceOf().
				return true;
			}
			return NodeWrapper<ScriptNode>::isInstanceOf( typeId );
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

void cut( ScriptNode &s, Node *parent, const Set *filter )
{
	IECorePython::ScopedGILRelease gilRelease;
	s.cut( parent, filter );
}

void paste( ScriptNode &s, Node *parent, bool continueOnError )
{
	IECorePython::ScopedGILRelease gilRelease;
	s.paste( parent, continueOnError );
}

void deleteNodes( ScriptNode &s, Node *parent, const Set *filter, bool reconnect )
{
	IECorePython::ScopedGILRelease r;
	s.deleteNodes( parent, filter, reconnect );
}

bool executeWrapper( ScriptNode &s, const std::string &serialisation, Node *parent, bool continueOnError )
{
	IECorePython::ScopedGILRelease r;
	return s.execute( serialisation, parent, continueOnError );
}

bool executeFile( ScriptNode &s, const std::string &fileName, Node *parent, bool continueOnError )
{
	IECorePython::ScopedGILRelease r;
	return s.executeFile( fileName, parent, continueOnError );
}

bool load( ScriptNode &s, bool continueOnError )
{
	IECorePython::ScopedGILRelease r;
	return s.load( continueOnError );
}

void save( ScriptNode &s )
{
	IECorePython::ScopedGILRelease r;
	s.save();
}

bool importFile( ScriptNode &s, const std::string &fileName, Node *parent, bool continueOnError )
{
	IECorePython::ScopedGILRelease r;
	return s.importFile( fileName, parent, continueOnError );
}

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

void GafferModule::bindScriptNode()
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
		.def( "cut", &cut, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "filter" ) = boost::python::object() ) )
		.def( "paste", &paste, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "continueOnError" ) = false ) )
		.def( "deleteNodes", &deleteNodes, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "filter" ) = boost::python::object(), boost::python::arg( "reconnect" ) = true ) )
		.def( "execute", &executeWrapper, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "continueOnError" ) = false ) )
		.def( "executeFile", &executeFile, ( boost::python::arg( "fileName" ), boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "continueOnError" ) = false ) )
		.def( "isExecuting", &ScriptNode::isExecuting )
		.def( "serialise", &ScriptNode::serialise, ( boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "filter" ) = boost::python::object() ) )
		.def( "serialiseToFile", &ScriptNode::serialiseToFile, ( boost::python::arg( "fileName" ), boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "filter" ) = boost::python::object() ) )
		.def( "save", &save )
		.def( "load", &load, ( boost::python::arg( "continueOnError" ) = false ) )
		.def( "importFile", &importFile, ( boost::python::arg( "fileName" ), boost::python::arg( "parent" ) = boost::python::object(), boost::python::arg( "continueOnError" ) = false ) )
		.def( "context", &context )
	;

	SignalClass<ScriptNode::ActionSignal, DefaultSignalCaller<ScriptNode::ActionSignal>, ActionSlotCaller>( "ActionSignal" );
	SignalClass<ScriptNode::UndoAddedSignal, DefaultSignalCaller<ScriptNode::UndoAddedSignal>, UndoAddedSlotCaller>( "UndoAddedSignal" );

}
