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
#include "Gaffer/Monitor.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/StringPlug.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

#include "IECore/MessageHandler.h"

#include "boost/algorithm/string/classification.hpp"
#include "boost/algorithm/string/find_iterator.hpp"
#include "boost/algorithm/string/replace.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/regex.hpp"

#include "fmt/format.h"

#include <memory>
#include <regex>

using namespace boost;
using namespace Gaffer;
using namespace GafferBindings;

//////////////////////////////////////////////////////////////////////////
// Serialisation
//////////////////////////////////////////////////////////////////////////

namespace
{

const std::string formattedErrorContext( int lineNumber, const std::string &context )
{
	return fmt::format( "Line {}{}{}",
		lineNumber, !context.empty() ? " of " : "",
		context
	);
}

const std::regex g_blockStartRegex( R"(^if[ \t(])" );
const std::regex g_blockContinuationRegex( R"(^[ \t]+)" );

// Execute the script one line at a time, reporting errors that occur,
// but otherwise continuing with execution.
bool tolerantExec( const std::string &pythonScript, boost::python::object globals, boost::python::object locals, const std::string &context )
{
	bool result = false;
	int lineNumber = 0;

	const IECore::Canceller *canceller = Context::current()->canceller();

	auto it = make_split_iterator( pythonScript, token_finder( is_any_of( "\n" ) ) );
	while( it != split_iterator<std::string::const_iterator>() )
	{
		IECore::Canceller::check( canceller );

		std::string toExecute( it->begin(), it->end() );
		++it; ++lineNumber;

		// Our serialisations have always been in a form that can be executed
		// line-by-line. But certain third parties have used custom serialisers
		// that output multi-line `if` statements that must be executed in a
		// single call. Here we detect them and group them together.
		//
		// Notes :
		//
		// - Historically, we used a Python C AST API to support _any_ compound
		//   statements here. But that is [no longer available](9d15bd21c4049d89118faf3ac27d01c5799b8264),
		//   and using the `ast` module instead would be a significant performance
		//   regression.
		// - While using Python as our serialisation format is great from an
		//   educational and reuse perspective, it has never been good from a
		//   performance perspective. A likely future direction is to constrain
		//   the serialisation syntax further such that it is still valid
		//   Python, but we can parse and execute the majority of it directly in C++
		//   for improvement performance.
		// - We are therefore deliberately supporting only the absolute minimum of syntax
		//   needed for the legacy third-party serialisations here, to give us
		//   more flexibility in optimising the parsing in future.
		if( std::regex_search( toExecute, g_blockStartRegex )  )
		{
			while( it != split_iterator<std::string::const_iterator>() )
			{
				const std::string line( it->begin(), it->end() );
				if( std::regex_search( line, g_blockContinuationRegex ) )
				{
					toExecute += "\n" + line;
					++it; ++lineNumber;
				}
				else
				{
					break;
				}
			}
		}

		try
		{
			exec( toExecute.c_str(), globals, locals );
		}
		catch( const boost::python::error_already_set & )
		{
			const std::string message = IECorePython::ExceptionAlgo::formatPythonException( /* withTraceback = */ false );
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

	boost::python::object builtIn = boost::python::import( "builtins" );
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
	if( !Py_IsInitialized() )
	{
		Py_Initialize();
	}

	IECorePython::ScopedGILLock gilLock;

	// Remove current Process from ThreadState, because it would
	// cause `StringPlug::getValue()` to perform unwanted substitutions
	// that would accidentally be baked into the serialisation.
	/// \todo Consider having a serialisation process instead (and
	/// perhaps a more general concept of a non-computing process)
	/// and making StringPlug skip substitutions when it sees one.
	const Context *context = Context::current();
	const Monitor::MonitorSet &monitors = Monitor::current();
	const ThreadState defaultThreadState;
	ThreadState::Scope defaultThreadStateScope( defaultThreadState );
	Context::Scope contextScope( context );
	Monitor::Scope monitorScope( monitors );

	std::string result;
	try
	{
		Serialisation serialisation( parent, "parent", filter );
		result = serialisation.result();
	}
	catch( boost::python::error_already_set & )
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
			catch( boost::python::error_already_set & )
			{
				int lineNumber = 0;
				std::string message = IECorePython::ExceptionAlgo::formatPythonException( /* withTraceback = */ false, &lineNumber );
				throw IECore::Exception( formattedErrorContext( lineNumber, context ) + " : " + message );
			}
		}
		else
		{
			result = tolerantExec( toExecute, e, e, context );
		}
	}
	catch( boost::python::error_already_set & )
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

SetPtr focusSet( ScriptNode &s )
{
	return s.focusSet();
}

void setFocus( ScriptNode &s, Node *node )
{
	IECorePython::ScopedGILRelease gilRelease;
	s.setFocus( node );
}

NodePtr getFocus( ScriptNode &s )
{
	return s.getFocus();
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

bool executeFile( ScriptNode &s, const std::filesystem::path &fileName, Node *parent, bool continueOnError )
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

bool importFile( ScriptNode &s, const std::filesystem::path &fileName, Node *parent, bool continueOnError )
{
	IECorePython::ScopedGILRelease r;
	return s.importFile( fileName, parent, continueOnError );
}

struct ActionSlotCaller
{

	void operator()( boost::python::object slot, ScriptNodePtr script, ConstActionPtr action, Action::Stage stage )
	{
		try
		{
			slot( script, boost::const_pointer_cast<Action>( action ), stage );
		}
		catch( const boost::python::error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}

};

struct UndoAddedSlotCaller
{

	void operator()( boost::python::object slot, ScriptNodePtr script )
	{
		try
		{
			slot( script );
		}
		catch( const boost::python::error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}

};

struct FocusChangedSlotCaller
{

	void operator()( boost::python::object slot, ScriptNodePtr script, NodePtr node )
	{
		try
		{
			slot( script, node );
		}
		catch( const boost::python::error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}

};


} // namespace

void GafferModule::bindScriptNode()
{

	GraphComponentClass<ScriptContainer>();

	boost::python::scope s = NodeClass<ScriptNode, ScriptNodeWrapper>()
		.def( "applicationRoot", &applicationRoot )
		.def( "selection", &selection )
		.def( "setFocus", &setFocus )
		.def( "getFocus", &getFocus )
		.def( "focusChangedSignal", &ScriptNode::focusChangedSignal, boost::python::return_internal_reference<1>() )
		.def( "focusSet", &focusSet )
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
	SignalClass<ScriptNode::FocusChangedSignal, DefaultSignalCaller<ScriptNode::FocusChangedSignal>, FocusChangedSlotCaller>( "FocusChangedSignal" );

}
