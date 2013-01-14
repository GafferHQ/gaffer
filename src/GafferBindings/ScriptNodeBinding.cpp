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

#include "boost/tokenizer.hpp"

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ScopedGILLock.h"

#include "GafferBindings/ScriptNodeBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/Serialiser.h"
#include "GafferBindings/NodeBinding.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Context.h"
#include "Gaffer/ApplicationRoot.h"

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

		ScriptNodeWrapper( PyObject *self, const std::string &name, const dict &inputs, const tuple &dynamicPlugs )
			:	NodeWrapper<ScriptNode>( self, name, dict(), tuple() )
		{
			initNode( this, inputs, dynamicPlugs );
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
			
			deleteNodes();			
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
				
	private :

		virtual void parentChanging( Gaffer::GraphComponent *newParent )
		{
			if( !newParent )
			{
				// we ditch m_executionDict when we lose our parent, so
				// that we're not kept alive unecessarily by potential
				// circular references created by variables in the dict.
				// see GafferTest.ScriptNodeTest.testLifeTimeAfterExecution()
				// for further discussion.
				IECorePython::ScopedGILLock gilLock;
				m_executionDict = object();
			}
		}
	
		// the dict returned will form both the locals and the globals for the execute()
		// and evaluate() methods. it's not possible to have a separate locals
		// and globals dictionary and have things work as intended. see
		// ScriptNodeTest.testClassScope() for an example, and 
		// http://bugs.python.org/issue991196 for an explanation.
		object executionDict()
		{
			if( !m_executionDict.is_none() )
			{
				return m_executionDict;
			}
			
			m_executionDict = dict();
				
			object builtIn = import( "__builtin__" );
			m_executionDict["__builtins__"] = builtIn;
			
			object gafferModule = import( "Gaffer" );
			m_executionDict["Gaffer"] = gafferModule;
			
			object selfO( ScriptNodePtr( this ) );
			
			object weakrefModule = import( "weakref" );
			m_executionDict["script"] = weakrefModule.attr( "ref" )( selfO );
			
			object weakMethod = gafferModule.attr( "WeakMethod" );
			m_executionDict["addChild"] = weakMethod( object( selfO.attr( "addChild" ) ) );
			m_executionDict["getChild"] = weakMethod( object( selfO.attr( "getChild" ) ) );
			m_executionDict["childAddedSignal"] = weakMethod( object( selfO.attr( "childAddedSignal" ) ) );
			m_executionDict["childRemovedSignal"] = weakMethod( object( selfO.attr( "childRemovedSignal" ) ) );
			m_executionDict["selection"] = weakMethod( object( selfO.attr( "selection" ) ) );
			m_executionDict["undo"] = weakMethod( object( selfO.attr( "undo" ) ) );
			m_executionDict["redo"] = weakMethod( object( selfO.attr( "redo" ) ) );
			m_executionDict["deleteNodes"] = weakMethod( object( selfO.attr( "deleteNodes" ) ) );
			m_executionDict["serialise"] = weakMethod( object( selfO.attr( "serialise" ) ) );
			m_executionDict["save"] = weakMethod( object( selfO.attr( "save" ) ) );
			m_executionDict["load"] = weakMethod( object( selfO.attr( "load" ) ) );

			return m_executionDict;
		}
		
		object m_executionDict;
		
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

static ApplicationRootPtr applicationRoot( ScriptNode &s )
{
	return s.applicationRoot();
}

void bindScriptNode()
{
	scope s = NodeClass<ScriptNode, ScriptNodeWrapperPtr>()
		.def( "applicationRoot", &applicationRoot )
		.def( "selection", (StandardSetPtr (ScriptNode::*)())&ScriptNode::selection )
		.def( "undoAvailable", &ScriptNode::undoAvailable )
		.def( "undo", &ScriptNode::undo )
		.def( "redoAvailable", &ScriptNode::redoAvailable )
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
