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

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/Context.h"
#include "Gaffer/ApplicationRoot.h"
#include "Gaffer/StandardSet.h"

#include "GafferBindings/ScriptNodeBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/NodeBinding.h"

using namespace boost::python;
using namespace Gaffer;

namespace GafferBindings
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

		virtual void execute( const std::string &pythonScript, Node *parent = 0 )
		{
			IECorePython::ScopedGILLock gilLock;
			object e = executionDict( parent );
			exec( pythonScript.c_str(), e, e );
			scriptExecutedSignal()( this, pythonScript );
		}

		void executeFile( const std::string &pythonFile, Node *parent = 0 )
		{
			const std::string pythonScript = readFile( pythonFile );
			execute( pythonScript, parent );
		}
		
		virtual PyObject *evaluate( const std::string &pythonExpression, Node *parent = 0 )
		{
			IECorePython::ScopedGILLock gilLock;
			object e = executionDict( parent );
			object result = eval( pythonExpression.c_str(), e, e );
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
		
		virtual void load()
		{
			const std::string s = readFile( fileNamePlug()->getValue() );
			
			deleteNodes();			
			execute( s );
			
			UndoContext undoDisabled( this, UndoContext::Disabled );
			unsavedChangesPlug()->setValue( false );
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
		object executionDict( Node *parent )
		{
			dict result;
				
			object builtIn = import( "__builtin__" );
			result["__builtins__"] = builtIn;
			
			object gafferModule = import( "Gaffer" );
			result["Gaffer"] = gafferModule;
			
			result["script"] = object( ScriptNodePtr( this ) );
			result["parent"] = object( NodePtr( parent ? parent : this ) );

			return result;
		}
				
};

IE_CORE_DECLAREPTR( ScriptNodeWrapper )

struct ScriptEvaluatedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, ScriptNodePtr node, const std::string script, PyObject *result )
	{
		try
		{
			boost::python::object o( handle<>( borrowed( result ) ) );
			slot( node, script, o );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears error status
		}
		return boost::signals::detail::unusable();
	}
};

static ContextPtr context( ScriptNode &s )
{
	return s.context();
}

static ApplicationRootPtr applicationRoot( ScriptNode &s )
{
	return s.applicationRoot();
}

static StandardSetPtr selection( ScriptNode &s )
{
	return s.selection();
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
			slot( script, IECore::constPointerCast<Action>( action ), stage );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
	
};

void bindScriptNode()
{
	scope s = NodeClass<ScriptNode, ScriptNodeWrapperPtr>()
		.def( "applicationRoot", &applicationRoot )
		.def( "selection", &selection )
		.def( "undoAvailable", &ScriptNode::undoAvailable )
		.def( "undo", &ScriptNode::undo )
		.def( "redoAvailable", &ScriptNode::redoAvailable )
		.def( "redo", &ScriptNode::redo )
		.def( "actionSignal", &ScriptNode::actionSignal, return_internal_reference<1>() )
		.def( "copy", &ScriptNode::copy, ( arg_( "parent" ) = object(), arg_( "filter" ) = object() ) )
		.def( "cut", &ScriptNode::cut, ( arg_( "parent" ) = object(), arg_( "filter" ) = object() ) )
		.def( "paste", &ScriptNode::paste, ( arg_( "parent" ) = object() ) )
		.def( "deleteNodes", &ScriptNode::deleteNodes, ( arg_( "parent" ) = object(), arg_( "filter" ) = object(), arg_( "reconnect" ) = true ) )
		.def( "execute", &ScriptNode::execute, ( arg_( "parent" ) = object() ) )
		.def( "executeFile", &ScriptNode::executeFile, ( arg_( "fileName" ), arg_( "parent" ) = object() ) )
		.def( "evaluate", &ScriptNode::evaluate, ( arg_( "parent" ) = object() ) )
		.def( "scriptExecutedSignal", &ScriptNode::scriptExecutedSignal, return_internal_reference<1>() )
		.def( "scriptEvaluatedSignal", &ScriptNode::scriptEvaluatedSignal, return_internal_reference<1>() )
		.def( "serialise", &ScriptNode::serialise, ( arg_( "parent" ) = object(), arg_( "filter" ) = object() ) )
		.def( "serialiseToFile", &ScriptNode::serialiseToFile, ( arg_( "fileName" ), arg_( "parent" ) = object(), arg_( "filter" ) = object() ) )
		.def( "save", &ScriptNode::save )
		.def( "load", &ScriptNode::load )
		.def( "context", &context )
	;
	
	SignalBinder<ScriptNode::ActionSignal, DefaultSignalCaller<ScriptNode::ActionSignal>, ActionSlotCaller>::bind( "ActionSignal" );	

	SignalBinder<ScriptNode::ScriptExecutedSignal>::bind( "ScriptExecutedSignal" );
	SignalBinder<ScriptNode::ScriptEvaluatedSignal, DefaultSignalCaller<ScriptNode::ScriptEvaluatedSignal>, ScriptEvaluatedSlotCaller>::bind( "ScriptEvaluatedSignal" );	

	Serialisation::registerSerialiser( ScriptNode::staticTypeId(), new ScriptNodeSerialiser );
	
}

} // namespace GafferBindings
