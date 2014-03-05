//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
#include "boost/python/extract.hpp"

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/Plug.h"
#include "Gaffer/Context.h"
#include "Gaffer/ExecutableNode.h"
#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/ExecutableBinding.h"
#include "GafferBindings/ExecutableNodeBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace GafferBindings;
using namespace Gaffer;

// derived class created only so that we have access to protected static members from ExecutableNode
class PythonExecutableNode : public ExecutableNode
{
	public :

		static list defaultRequirements( ExecutableNode *node, const Context *context )
		{
			Executable::Tasks tasks;
			Executable::defaultRequirements( node, context, tasks );
			list result;
			for ( Executable::Tasks::const_iterator tIt = tasks.begin(); tIt != tasks.end(); tIt++ )
			{
				result.append( *tIt );
			}
			return result;
		}

		static bool acceptsRequirementsInput( const Plug *plug, const Plug *inputPlug )
		{
			return Executable::acceptsRequirementsInput( plug, inputPlug );
		}

		static bool isExecutable( object obj )
		{
			extract< Node * > node( obj );

			if ( node.check() )
			{
				Executable *pNode = dynamic_cast< Executable * >( node() );
				return ( pNode != NULL );
			}
			else
			{
				return PyObject_HasAttrString(obj.ptr(), "execute" );
			}
		}
};

/// Python wrapper for ExecutableNode class, forwarding C++ calls to the virtual methods from Executable on to the python object.
class ExecutableNodeWrapper : public NodeWrapper< ExecutableNode >
{
	public :

		ExecutableNodeWrapper( PyObject *self, const std::string &name ) : NodeWrapper< ExecutableNode >( self, name )
		{
		}

		virtual void execute( const Executable::Contexts &contexts ) const
		{
			ScopedGILLock gilLock;
			list contextList;
			for ( Executable::Contexts::const_iterator cIt = contexts.begin(); cIt != contexts.end(); cIt++ )
			{
				contextList.append( *cIt );
			}
			object exec = this->methodOverride( "execute" );
			if( exec )
			{
				exec( contextList );
			}
			else
			{
				throw Exception( "execute() python method not defined" );
			}
		}

		virtual void executionRequirements( const Context *context, Executable::Tasks &requirements ) const
		{
			ScopedGILLock gilLock;
			object req = this->methodOverride( "executionRequirements" );
			if( !req )
			{
				throw Exception( "executionRequirements() python method not defined" );
			}

			list requirementList = extract<boost::python::list>(
				req( ContextPtr(const_cast<Context*>(context)) )
			);
			
			Executable::Tasks tasks;
			
			size_t len = boost::python::len( requirementList );
			requirements.reserve( len );
			for ( size_t i = 0; i < len; i++ )
			{
				requirements.push_back( extract< Executable::Task >( requirementList[i] ) );
			}
		}

		virtual IECore::MurmurHash executionHash( const Context *context ) const
		{
			ScopedGILLock gilLock;
			object h = this->methodOverride( "executionHash" );
			if( h )
			{
				return extract<IECore::MurmurHash>(
					h( ContextPtr(const_cast<Context*>(context)) )
				);
			}
			else
			{
				throw Exception( "executionHash() python method not defined" );
			}
		}
		
};

IE_CORE_DECLAREPTR( ExecutableNodeWrapper );

static unsigned long taskHash( const Executable::Task &t )
{
	// we convert the hash to a long by doing XOR operator between each long that fits the hash.
	IECore::MurmurHash h;
	h = t.hash();
	unsigned long *u = (unsigned long*)&h;
	unsigned long v = u[0];
	for ( unsigned int i = 1; i < sizeof(h)/sizeof(long); i++ )
	{
		v ^= u[i];
	}
	return v;
}

static ContextPtr taskContext( const Executable::Task &t )
{
	return t.context;
}

static void setTaskContext( Executable::Task &t, ContextPtr c )
{
	t.context = c;
}

static NodePtr taskNode( const Executable::Task &t )
{
	return t.node;
}

static void setTaskNode( Executable::Task &t, NodePtr n )
{
	t.node = n;
}

void GafferBindings::bindExecutableNode()
{
	typedef NodeClass<ExecutableNode, ExecutableNodeWrapperPtr> PythonType;
	PythonType executable;
	executable
		.def( "_defaultRequirements", &PythonExecutableNode::defaultRequirements )
		.def( "_acceptsRequirementsInput", &PythonExecutableNode::acceptsRequirementsInput ).staticmethod( "_acceptsRequirementsInput" )

		// static function introduced in python because we don't have a way to detect multiple inheritance in python.
		.def( "isExecutable", &PythonExecutableNode::isExecutable ).staticmethod("isExecutable" )
	;

	ExecutableBinding<PythonType, ExecutableNodeWrapper>::bind( executable );

	scope executableScope(executable);

	class_<Executable::Task>( "Task", "Defined by a Node and a execution Context" )
		.def( init<>() )
		.def( init<Executable::Task>() )
		.def( init<Gaffer::NodePtr,Gaffer::ContextPtr>() )
		.add_property("node", &taskNode, &setTaskNode )
		.add_property("context", &taskContext, &setTaskContext )
		.def("__eq__", &Executable::Task::operator== )
		.def("__hash__", &taskHash )
	;

}
