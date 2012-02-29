//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "boost/tokenizer.hpp"

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"

#include "GafferBindings/ScriptNodeBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/Serialiser.h"
#include "GafferBindings/NodeBinding.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Context.h"

using namespace boost::python;
using namespace Gaffer;

namespace GafferBindings
{

/// The ScriptNodeWrapper class implements the scripting
/// components of the ScriptNode base class. In this way
/// scripting is available provided that the ScriptNode was
/// created from python.
class ScriptNodeWrapper : public ScriptNode, public IECorePython::Wrapper<ScriptNode>
{

	public :

		ScriptNodeWrapper( PyObject *self, const std::string &name, const dict &inputs, const tuple &dynamicPlugs )
			:	ScriptNode( name ), IECorePython::Wrapper<ScriptNode>( self, this )
		{
			initNode( this, inputs, dynamicPlugs );

			// this dict will form both the locals and the globals for the execute()
			// and evaluate() methods. it's not possible to have a separate locals
			// and globals dictionary and have things work as intended. see
			// ScriptNodeTest.testClassScope() for an example, and 
			// http://bugs.python.org/issue991196 for an explanation.
			dict executionDict;
			
			object builtIn = import( "__builtin__" );
			executionDict["__builtins__"] = builtIn;
			
			object gafferModule = import( "Gaffer" );
			executionDict["Gaffer"] = gafferModule;
			
			object weakMethod = gafferModule.attr( "WeakMethod" );
			
			object selfO( handle<>( borrowed( self ) ) );
			
			executionDict["addChild"] = weakMethod( object( selfO.attr( "addChild" ) ) );
			executionDict["getChild"] = weakMethod( object( selfO.attr( "getChild" ) ) );
			executionDict["childAddedSignal"] = weakMethod( object( selfO.attr( "childAddedSignal" ) ) );
			executionDict["childRemovedSignal"] = weakMethod( object( selfO.attr( "childRemovedSignal" ) ) );
			executionDict["selection"] = weakMethod( object( selfO.attr( "selection" ) ) );
			executionDict["undo"] = weakMethod( object( selfO.attr( "undo" ) ) );
			executionDict["redo"] = weakMethod( object( selfO.attr( "redo" ) ) );
			executionDict["deleteNodes"] = weakMethod( object( selfO.attr( "deleteNodes" ) ) );
			executionDict["serialise"] = weakMethod( object( selfO.attr( "serialise" ) ) );
			executionDict["save"] = weakMethod( object( selfO.attr( "save" ) ) );
			executionDict["load"] = weakMethod( object( selfO.attr( "load" ) ) );
			
			// ideally we'd just store the execution scope as a normal
			// c++ member variable but we can't as it may hold
			// references back to us. by storing it in self.__dict__
			// we allow it to participate in garbage collection, thus breaking
			// the cycle and allowing the ScriptNode to die.
			object selfDict = selfO.attr( "__dict__" );
			selfDict["__executionDict"] = executionDict;
			
		}

		virtual ~ScriptNodeWrapper()
		{
		}

		virtual void execute( const std::string &pythonScript )
		{
			object e = executionDict();
			exec( pythonScript.c_str(), e, e );
			scriptExecutedSignal()( this, pythonScript );
		}

		virtual PyObject *evaluate( const std::string &pythonExpression )
		{
			object e = executionDict();
			object result = eval( pythonExpression.c_str(), e, e );
			scriptEvaluatedSignal()( this, pythonExpression, result.ptr() );
			
			// make a reference to keep the result alive - the caller then
			// assumes responsibility for dealing with this
			Py_XINCREF( result.ptr() );
			return result.ptr();
		}

		virtual std::string serialise( ConstSetPtr filter=0 ) const
		{
			return Serialiser::serialise( this, filter );
		}
		
		/// \todo Clear the script before executing!!
		/// We need to consider implementing a delete() method first though.
		virtual void load()
		{
			std::string fileName = IECore::constPointerCast<StringPlug>( fileNamePlug() )->getValue();
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
						
			execute( s );
		}
		
		virtual void save() const
		{
			std::string s = serialise();
			
			std::string fileName = IECore::constPointerCast<StringPlug>( fileNamePlug() )->getValue();
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
		
		GAFFERBINDINGS_NODEWRAPPERFNS( ScriptNode )
		
	private :
	
		object executionDict()
		{
			object selfO( handle<>( borrowed( m_pyObject ) ) );
			object selfDict = selfO.attr( "__dict__" );
			return selfDict["__executionDict"];
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

BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS( serialiseOverloads, serialise, 0, 1 );
BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS( copyOverloads, copy, 0, 1 );
BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS( cutOverloads, cut, 0, 1 );
BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS( deleteNodesOverloads, deleteNodes, 0, 1 );

void bindScriptNode()
{
	scope s = NodeClass<ScriptNode, ScriptNodeWrapperPtr>()
		.def( "selection", (StandardSetPtr (ScriptNode::*)())&ScriptNode::selection )
		.def( "undo", &ScriptNode::undo )
		.def( "redo", &ScriptNode::redo )
		.def( "copy", &ScriptNode::copy, copyOverloads() )
		.def( "cut", &ScriptNode::cut, cutOverloads() )
		.def( "paste", &ScriptNode::paste )
		.def( "deleteNodes", &ScriptNode::deleteNodes, deleteNodesOverloads() )
		.def( "execute", &ScriptNode::execute )
		.def( "evaluate", &ScriptNode::evaluate )
		.def( "scriptExecutedSignal", &ScriptNode::scriptExecutedSignal, return_internal_reference<1>() )
		.def( "scriptEvaluatedSignal", &ScriptNode::scriptEvaluatedSignal, return_internal_reference<1>() )
		.def( "serialise", &ScriptNode::serialise, serialiseOverloads() )
		.def( "save", &ScriptNode::save )
		.def( "load", &ScriptNode::load )
		.def( "context", &context )
	;
	
	SignalBinder<ScriptNode::ScriptExecutedSignal>::bind( "ScriptExecutedSignal" );
	SignalBinder<ScriptNode::ScriptEvaluatedSignal, DefaultSignalCaller<ScriptNode::ScriptEvaluatedSignal>, ScriptEvaluatedSlotCaller>::bind( "ScriptEvaluatedSignal" );	
}

} // namespace GafferBindings
