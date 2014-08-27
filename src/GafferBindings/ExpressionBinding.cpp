//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "IECore/MessageHandler.h"
#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/Wrapper.h"

#include "Gaffer/Expression.h"
#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ExpressionBinding.h"
#include "GafferBindings/ExceptionAlgo.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

class EngineWrapper : public Expression::Engine, public IECorePython::Wrapper<Expression::Engine>
{
	public :

		EngineWrapper( PyObject *self )
				:	Engine(), IECorePython::Wrapper<Expression::Engine>( self, this )
		{
		}

		virtual std::string outPlug()
		{
			IECorePython::ScopedGILLock gilLock;
			try
			{
				boost::python::override f = this->get_override( "outPlug" );
				if( f )
				{
					return f();
				}
				else
				{
					msg( IECore::Msg::Error, "EngineWrapper::outPlug", "outPlug method not defined in python." );
				}
			}
			catch( const error_already_set &e )
			{
				translatePythonException();
			}
			return "";
		}

		virtual void inPlugs( std::vector<std::string> &plugs )
		{
			IECorePython::ScopedGILLock gilLock;
			try
			{
				override f = this->get_override( "inPlugs" );
				if( f )
				{
					list pythonPlugs = f();
					container_utils::extend_container( plugs, pythonPlugs );
				}
				else
				{
					msg( IECore::Msg::Error, "EngineWrapper::inPlugs", "inPlugs method not defined in python." );
				}
			}
			catch( const error_already_set &e )
			{
				translatePythonException();
			}
		}

		virtual void contextNames( std::vector<std::string> &names )
		{
			IECorePython::ScopedGILLock gilLock;
			try
			{
				override f = this->get_override( "contextNames" );
				if( f )
				{
					list pythonNames = f();
					container_utils::extend_container( names, pythonNames );
				}
				else
				{
					msg( IECore::Msg::Error, "EngineWrapper::contextNames", "contextNames method not defined in python." );
				}
			}
			catch( const error_already_set &e )
			{
				translatePythonException();
			}
		}

		virtual void execute( const Context *context, const std::vector<const ValuePlug *> &proxyInputs, ValuePlug *proxyOutput )
		{
			IECorePython::ScopedGILLock gilLock;
			try
			{
				override f = this->get_override( "execute" );
				if( f )
				{
					list pythonProxyInputs;
					for( std::vector<const ValuePlug *>::const_iterator it = proxyInputs.begin(); it!=proxyInputs.end(); it++ )
					{
						pythonProxyInputs.append( PlugPtr( const_cast<ValuePlug *>( *it ) ) );
					}

					f( ContextPtr( const_cast<Context *>( context ) ), pythonProxyInputs, ValuePlugPtr( proxyOutput ) );
				}
				else
				{
					msg( IECore::Msg::Error, "EngineWrapper::execute", "execute method not defined in python." );
				}
			}
			catch( const error_already_set &e )
			{
				translatePythonException();
			}
		}

};

struct ExpressionEngineCreator
{
	ExpressionEngineCreator( object fn )
		:	m_fn( fn )
	{
	}

	Expression::EnginePtr operator()( const std::string &expression )
	{
		IECorePython::ScopedGILLock gilLock;
		Expression::EnginePtr result = extract<Expression::EnginePtr>( m_fn( expression ) );
		return result;
	}

	private :

		object m_fn;

};

static void registerEngine( const std::string &engineType, object creator )
{
	Expression::Engine::registerEngine( engineType, ExpressionEngineCreator( creator ) );
}

static tuple registeredEnginesWrapper()
{
	std::vector<std::string> engineTypes;
	Expression::Engine::registeredEngines( engineTypes );
	boost::python::list l;
	for( std::vector<std::string>::const_iterator it = engineTypes.begin(); it!=engineTypes.end(); it++ )
	{
		l.append( *it );
	}
	return boost::python::tuple( l );
}

void GafferBindings::bindExpression()
{

	scope s = DependencyNodeClass<Expression>();

	IECorePython::RefCountedClass<Expression::Engine, IECore::RefCounted, EngineWrapper>( "Engine" )
		.def( init<>() )
		.def( "registerEngine", &registerEngine ).staticmethod( "registerEngine" )
		.def( "registeredEngines", &registeredEnginesWrapper ).staticmethod( "registeredEngines" )
	;

}
