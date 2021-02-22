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

#include "ExpressionBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Expression.h"
#include "Gaffer/StringPlug.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILLock.h"

#include "IECore/MessageHandler.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

void setExpression( Expression &e, const std::string &expression, const std::string &language )
{
	IECorePython::ScopedGILRelease gilRelease;
	e.setExpression( expression, language );
}

tuple getExpression( Expression &e )
{
	std::string language;
	std::string expression = e.getExpression( language );
	return boost::python::make_tuple( expression, language );
}

struct ExpressionEngineCreator
{
	ExpressionEngineCreator( object fn )
		:	m_fn( fn )
	{
	}

	Expression::EnginePtr operator()()
	{
		IECorePython::ScopedGILLock gilLock;
		Expression::EnginePtr result = extract<Expression::EnginePtr>( m_fn() );
		return result;
	}

	private :

		object m_fn;

};

struct ExpressionChangedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, ExpressionPtr e )
	{
		try
		{
			slot( e );
		}
		catch( const error_already_set &e )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

ValuePlug::CachePolicy defaultExecuteCachePolicy()
{
	// Expressions implemented through Python will be forced to run serially due to the GIL,
	// which makes it very bad to allow parallel evaluations of the same plug, since they will
	// all compete over the same GIL.

	// In the long term, we can probably lock this to Standard, but in the short term, overriding
	// to Legacy or TaskIsolation using an env var could provide a workaround if facilities have
	// Gaffer nodes that do their own tbb calls without properly isolating them, which could
	// cause hangs when using the Standard policy
	if( const char *cp = getenv( "GAFFER_PYTHONEXPRESSION_CACHEPOLICY" ) )
	{
		if( !strcmp( cp, "Standard" ) )
		{
			return ValuePlug::CachePolicy::Standard;
		}
		else if( !strcmp( cp, "TaskCollaboration" ) )
		{
			return ValuePlug::CachePolicy::TaskCollaboration;
		}
		else if( !strcmp( cp, "TaskIsolation" ) )
		{
			return ValuePlug::CachePolicy::TaskIsolation;
		}
		else if( !strcmp( cp, "Legacy" ) )
		{
			return ValuePlug::CachePolicy::Legacy;
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "Expression", "Invalid value for GAFFER_GAFFER_PYTHONEXPRESSION_CACHEPOLICY. Must be Standard, TaskCollaboration, TaskIsolation or Legacy." );
		}
	}

	return  ValuePlug::CachePolicy::Standard;
}


class EngineWrapper : public IECorePython::RefCountedWrapper<Expression::Engine>
{
	public :

		EngineWrapper( PyObject *self )
				:	IECorePython::RefCountedWrapper<Expression::Engine>( self )
		{
		}

		void parse( Expression *node, const std::string &expression, std::vector<ValuePlug *> &inputs, std::vector<ValuePlug *> &outputs, std::vector<IECore::InternedString> &contextVariables ) override
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "parse" );
					if( f )
					{
						list pythonInputs, pythonOutputs, pythonContextVariables;
						f( ExpressionPtr( node ), expression, pythonInputs, pythonOutputs, pythonContextVariables );

						container_utils::extend_container( inputs, pythonInputs );
						container_utils::extend_container( outputs, pythonOutputs );
						container_utils::extend_container( contextVariables, pythonContextVariables );
						return;
					}
				}
				catch( const error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::parse() python method not defined" );
		}

		IECore::ConstObjectVectorPtr execute( const Context *context, const std::vector<const ValuePlug *> &proxyInputs ) const override
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
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::execute() python method not defined" );
		}

		ValuePlug::CachePolicy executeCachePolicy() const override
		{
			return g_cachePolicy;
		}

		void apply( ValuePlug *proxyOutput, const ValuePlug *topLevelProxyOutput, const IECore::Object *value ) const override
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "apply" );
					if( f )
					{
						f( ValuePlugPtr( proxyOutput ), ValuePlugPtr( const_cast<ValuePlug *>( topLevelProxyOutput ) ), IECore::ObjectPtr( const_cast<IECore::Object *>( value ) ) );
						return;
					}
				}
				catch( const error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::apply() python method not defined" );
		}

		std::string identifier( const Expression *node, const ValuePlug *plug ) const override
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "identifier" );
					if( f )
					{
						object result = f( ExpressionPtr( const_cast<Expression *>( node ) ), ValuePlugPtr( const_cast<ValuePlug *>( plug ) ) );
						return extract<std::string>( result );
					}
				}
				catch( const error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::identifier() python method not defined" );
		}

		std::string replace( const Expression *node, const std::string &expression, const std::vector<const ValuePlug *> &oldPlugs, const std::vector<const ValuePlug *> &newPlugs ) const override
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "replace" );
					if( f )
					{
						list pythonOldPlugs, pythonNewPlugs;
						for( std::vector<const ValuePlug *>::const_iterator it = oldPlugs.begin(); it!=oldPlugs.end(); it++ )
						{
							pythonOldPlugs.append( PlugPtr( const_cast<ValuePlug *>( *it ) ) );
						}
						for( std::vector<const ValuePlug *>::const_iterator it = newPlugs.begin(); it!=newPlugs.end(); it++ )
						{
							pythonNewPlugs.append( PlugPtr( const_cast<ValuePlug *>( *it ) ) );
						}

						object result = f( ExpressionPtr( const_cast<Expression *>( node ) ), expression, pythonOldPlugs, pythonNewPlugs );
						return extract<std::string>( result );
					}
				}
				catch( const error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::replace() python method not defined" );
		}

		std::string defaultExpression( const ValuePlug *output ) const override
		{
			if( isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					object f = this->methodOverride( "defaultExpression" );
					if( f )
					{
						object result = f( ValuePlugPtr( const_cast<ValuePlug *>( output ) ) );
						return extract<std::string>( result );
					}
				}
				catch( const error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}

			throw IECore::Exception( "Engine::defaultExpression() python method not defined" );
		}


		static void registerEngine( const std::string &engineType, object creator )
		{
			Expression::Engine::registerEngine( engineType, ExpressionEngineCreator( creator ) );
		}

		static tuple registeredEngines()
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

		static ValuePlug::CachePolicy g_cachePolicy;
};


ValuePlug::CachePolicy EngineWrapper::g_cachePolicy( defaultExecuteCachePolicy() );

static tuple languages()
{
	std::vector<std::string> languages;
	Expression::languages( languages );
	boost::python::list l;
	for( std::vector<std::string>::const_iterator it = languages.begin(); it!=languages.end(); it++ )
	{
		l.append( *it );
	}
	return boost::python::tuple( l );
}

class ExpressionSerialiser : public NodeSerialiser
{

	void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const override
	{
		const Expression *e = static_cast<const Expression *>( graphComponent );
		std::string language;
		e->getExpression( language );
		if( !language.empty() && language != "python" )
		{
			/// \todo Consider a virtual method on the Engine
			/// to provide this information.
			modules.insert( "Gaffer" + language );
		}
	}

	std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		// We delay the serialisation of the values for the engine and expression plugs
		// until now so that `Expression::plugSet()` can successfully restore the engine
		// after all connections to the node have been made.

		std::string result = NodeSerialiser::postScript( graphComponent, identifier, serialisation );

		const Expression *expression = static_cast<const Expression *>( graphComponent );
		const StringPlug *enginePlug = expression->getChild<StringPlug>( "__engine" );
		const StringPlug *expressionPlug = expression->getChild<StringPlug>( "__expression" );

		const std::string engineValue = enginePlug->getValue();
		const std::string expressionValue = expressionPlug->getValue();
		if( engineValue.empty() || expressionValue.empty() )
		{
			return result;
		}

		std::string engineRepr = extract<std::string>( object( engineValue ).attr( "__repr__" )() );
		std::string expressionRepr = extract<std::string>( object( expressionValue ).attr( "__repr__" )() );

		result += serialisation.identifier( enginePlug ) + ".setValue( " + engineRepr + " )\n";
		result += serialisation.identifier( expressionPlug ) + ".setValue( " + expressionRepr + " )\n";

		return result;
	}

};

} // namespace

void GafferModule::bindExpression()
{

	scope s = DependencyNodeClass<Expression>()
		.def( "languages", &languages ).staticmethod( "languages" )
		.def( "defaultExpression", &Expression::defaultExpression ).staticmethod( "defaultExpression" )
		.def( "setExpression", &setExpression, ( arg( "expression" ), arg( "language" ) = "python" ) )
		.def( "getExpression", &getExpression )
		.def( "expressionChangedSignal", &Expression::expressionChangedSignal, return_internal_reference<1>() )
		.def( "identifier", &Expression::identifier )
	;

	IECorePython::RefCountedClass<Expression::Engine, IECore::RefCounted, EngineWrapper>( "Engine" )
		.def( init<>() )
		.def( "registerEngine", &EngineWrapper::registerEngine ).staticmethod( "registerEngine" )
		.def( "registeredEngines", &EngineWrapper::registeredEngines ).staticmethod( "registeredEngines" )
	;

	SignalClass<Expression::ExpressionChangedSignal, DefaultSignalCaller<Expression::ExpressionChangedSignal>, ExpressionChangedSlotCaller >( "ExpressionChangedSignal" );

	Serialisation::registerSerialiser( Expression::staticTypeId(), new ExpressionSerialiser );

}
