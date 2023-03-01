//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#pragma once

#include "GafferCortex/ParameterisedHolder.h"

#include "GafferBindings/NodeBinding.h"

#include "IECorePython/ExceptionAlgo.h"

#include "IECore/Parameter.h"

#include "boost/format.hpp"

#include <memory>

namespace GafferCortexModule
{

template<typename BaseType>
class ParameterisedHolderWrapper : public BaseType
{

	public :

		ParameterisedHolderWrapper( PyObject *self, const std::string &name )
			:	BaseType( self, name )
		{
		}

		IECore::RunTimeTypedPtr loadClass( const std::string &className, int classVersion, const std::string &searchPathEnvVar ) const override
		{
			IECorePython::ScopedGILLock gilLock;
			boost::python::dict scopeDict;
			scopeDict["IECore"] = boost::python::import( "IECore" );
			std::string toExecute = boost::str(
				boost::format(
					"IECore.ClassLoader.defaultLoader( \"%s\" ).load( \"%s\", %d )()\n"
				) % searchPathEnvVar % className % classVersion
			);
			boost::python::object result = boost::python::eval( toExecute.c_str(), scopeDict, scopeDict );
			return boost::python::extract<IECore::RunTimeTypedPtr>( result );
		}

		void parameterChanged( IECore::RunTimeTyped *parameterised, IECore::Parameter *parameter ) override
		{
			IECorePython::ScopedGILLock gilLock;
			IECore::RunTimeTypedPtr parameterisedPtr( parameterised );
			boost::python::object pythonParameterised( parameterisedPtr );
			if( PyObject_HasAttrString( pythonParameterised.ptr(), "parameterChanged" ) )
			{
				BaseType::WrappedType::parameterHandler()->setParameterValue();

				typename BaseType::WrappedType::ParameterModificationContext parameterModificationContext( this );

				try
				{
					pythonParameterised.attr( "parameterChanged" )( IECore::ParameterPtr( parameter ) );
				}
				catch( boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
		}

};

template<typename BaseType>
class ParameterisedHolderClass : public BaseType
{

	public :

		ParameterisedHolderClass( const char *docString = nullptr )
			:	BaseType( docString )
		{

			this->def(
				"setParameterised",
				(void (BaseType::wrapped_type::*)( IECore::RunTimeTypedPtr, bool ))&BaseType::wrapped_type::setParameterised,
				(
					boost::python::arg_( "parameterised" ),
					boost::python::arg_( "keepExistingValues" ) = false
				)
			);

			this->def(
				"setParameterised",
				(void (BaseType::wrapped_type::*)( const std::string &, int, const std::string &, bool ))&BaseType::wrapped_type::setParameterised,
				(
					boost::python::arg_( "className" ),
					boost::python::arg_( "classVersion" ),
					boost::python::arg_( "searchPathEnvVar" ),
					boost::python::arg_( "keepExistingValues" ) = false
				)
			);

			this->def( "getParameterised", &getParameterised );

			this->def(
				"parameterHandler",
				(GafferCortex::CompoundParameterHandler *(BaseType::wrapped_type::*)())&BaseType::wrapped_type::parameterHandler,
				boost::python::return_value_policy<IECorePython::CastToIntrusivePtr>()
			);

			this->def( "parameterModificationContext", &parameterModificationContext, boost::python::return_value_policy<boost::python::manage_new_object>() );

			this->def( "setParameterisedValues", &BaseType::wrapped_type::setParameterisedValues );

			boost::python::scope s = *this;
			boost::python::class_<ParameterModificationContextWrapper, boost::noncopyable>( "ParameterModificationContext", boost::python::init<typename BaseType::wrapped_type::Ptr>() )
				.def( "__enter__", &ParameterModificationContextWrapper::enter )
				.def( "__exit__", &ParameterModificationContextWrapper::exit )
			;

		}

	private :

		static boost::python::tuple getParameterised( typename BaseType::wrapped_type &parameterisedHolder )
		{
			std::string className;
			int classVersion;
			std::string searchPathEnvVar;
			IECore::RunTimeTypedPtr p = parameterisedHolder.getParameterised( &className, &classVersion, &searchPathEnvVar );
			return boost::python::make_tuple( p, className, classVersion, searchPathEnvVar );
		}

		class ParameterModificationContextWrapper : boost::noncopyable
		{

			public :

				ParameterModificationContextWrapper( typename BaseType::wrapped_type::Ptr parameterisedHolder )
					:	m_parameterisedHolder( parameterisedHolder ), m_context()
				{
				}

				IECore::RunTimeTypedPtr enter()
				{
					m_context.reset( new typename BaseType::wrapped_type::ParameterModificationContext( m_parameterisedHolder ) );
					return m_parameterisedHolder->getParameterised();
				}

				bool exit( boost::python::object excType, boost::python::object excValue, boost::python::object excTraceBack )
				{
					m_context.reset();
					return false; // don't suppress exceptions
				}

			private :

				typename BaseType::wrapped_type::Ptr m_parameterisedHolder;
				std::unique_ptr<typename BaseType::wrapped_type::ParameterModificationContext> m_context;

		};

		static ParameterModificationContextWrapper *parameterModificationContext( typename BaseType::wrapped_type *parameterisedHolder )
		{
			return new ParameterModificationContextWrapper( parameterisedHolder );
		}

};

void bindParameterisedHolder();

} // namespace GafferCortexModule
