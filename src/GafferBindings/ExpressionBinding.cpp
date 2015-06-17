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

#include "Gaffer/Expression.h"
#include "Gaffer/StringPlug.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ExpressionBinding.h"
#include "GafferBindings/ExceptionAlgo.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

class EngineWrapper : public IECorePython::RefCountedWrapper<Expression::Engine>
{
	public :

		EngineWrapper( PyObject *self )
				:	IECorePython::RefCountedWrapper<Expression::Engine>( self )
		{
		}

		virtual void outPlugs( std::vector<std::string> &plugs )
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "outPlugs" );
					if( f )
					{
						list pythonPlugs = extract<list>( f() );
						container_utils::extend_container( plugs, pythonPlugs );
						return;
					}
				}
				catch( const error_already_set &e )
				{
					translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::outPlugs() python method not defined" );
		}

		virtual void inPlugs( std::vector<std::string> &plugs )
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "inPlugs" );
					if( f )
					{
						list pythonPlugs = extract<list>( f() );
						container_utils::extend_container( plugs, pythonPlugs );
						return;
					}
				}
				catch( const error_already_set &e )
				{
					translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::inPlugs() python method not defined" );
		}

		virtual void contextNames( std::vector<IECore::InternedString> &names )
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "contextNames" );
					if( f )
					{
						list pythonNames = extract<list>( f() );
						container_utils::extend_container( names, pythonNames );
						return;
					}
				}
				catch( const error_already_set &e )
				{
					translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::contextNames() python method not defined" );
		}

		virtual IECore::ConstObjectVectorPtr execute( const Context *context, const std::vector<const ValuePlug *> &proxyInputs )
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "execute" );
					if( f )
					{
						list pythonProxyInputs;
						for( std::vector<const ValuePlug *>::const_iterator it = proxyInputs.begin(); it!=proxyInputs.end(); it++ )
						{
							pythonProxyInputs.append( PlugPtr( const_cast<ValuePlug *>( *it ) ) );
						}

						object result = f( ContextPtr( const_cast<Context *>( context ) ), pythonProxyInputs );
						return extract<IECore::ConstObjectVectorPtr>( result );
					}
				}
				catch( const error_already_set &e )
				{
					translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::execute() python method not defined" );
		}

		virtual void setPlugValue( ValuePlug *plug, const IECore::Object *value )
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "setPlugValue" );
					if( f )
					{
						f( ValuePlugPtr( plug ), IECore::ObjectPtr( const_cast<IECore::Object *>( value ) ) );
						return;
					}
				}
				catch( const error_already_set &e )
				{
					translatePythonException();
				}
			}
			
			throw IECore::Exception( "Engine::setPlugValue() python method not defined" );
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

void registerEngine( const std::string &engineType, object creator )
{
	Expression::Engine::registerEngine( engineType, ExpressionEngineCreator( creator ) );
}

tuple registeredEnginesWrapper()
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

class ExpressionSerialiser : public NodeSerialiser
{

	virtual bool childNeedsSerialisation( const Gaffer::GraphComponent *child ) const
	{
		const Expression *expression = child->parent<Expression>();
		if( child == expression->expressionPlug() )
		{
			// We'll serialise this manually ourselves in
			// postScript() - see comments there.
			return false;
		}
		return NodeSerialiser::childNeedsSerialisation( child );
	}

	virtual std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
	{
		std::string result = NodeSerialiser::postScript( graphComponent, identifier, serialisation );

		// When the expression plug is set, the Expression node creates an engine,
		// parses the expression, and connects itself up in the graph. We must therefore
		// delay the setting of the expression until the whole graph has been created,
		// otherwise we'll be hunting for plugs referenced in the expression which have
		// not yet been created. The sad thing about all this is that the serialisation
		// has already reproduced the network we need anyway - the Expression node doesn't
		// even need to do anything.
		//
		/// \todo We could consider not using plugSetSignal() to trigger expression
		/// parsing, instead using an explicit method on the Expression class. In that
		/// case we wouldn't need any custom serialisation at all, but the UI code and
		/// scripts creating expressions would need to be updated to use the method
		/// rather than to just set the plug.
		const Expression *expression = static_cast<const Expression *>( graphComponent );
		const Serialiser *s = Serialisation::acquireSerialiser( expression->expressionPlug() );
		result += s->postConstructor( expression->expressionPlug(), serialisation.identifier( expression->expressionPlug() ), serialisation );

		return result;
	}

};

} // namespace

void GafferBindings::bindExpression()
{

	scope s = DependencyNodeClass<Expression>();

	IECorePython::RefCountedClass<Expression::Engine, IECore::RefCounted, EngineWrapper>( "Engine" )
		.def( init<>() )
		.def( "registerEngine", &registerEngine ).staticmethod( "registerEngine" )
		.def( "registeredEngines", &registeredEnginesWrapper ).staticmethod( "registeredEngines" )
	;

	Serialisation::registerSerialiser( Expression::staticTypeId(), new ExpressionSerialiser );

}
