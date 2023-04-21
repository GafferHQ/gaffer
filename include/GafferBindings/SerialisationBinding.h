//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "GafferBindings/Serialisation.h"

#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ExceptionAlgo.h"

#include "boost/python/suite/indexing/container_utils.hpp"

namespace GafferBindings
{

template<typename T, typename Base, typename TWrapper=T>
class SerialiserClass : public IECorePython::RefCountedClass<T, Base, TWrapper>
{
	public :

		SerialiserClass( const char *name );

};

template<typename WrappedType>
class SerialiserWrapper : public IECorePython::RefCountedWrapper<WrappedType>
{

	public :

		SerialiserWrapper( PyObject *self )
			:	IECorePython::RefCountedWrapper<WrappedType>( self )
		{
		}

		void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "moduleDependencies" );
					if( f )
					{
						boost::python::object mo = f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( graphComponent ) ), boost::ref( serialisation ) );
						std::vector<std::string> mv;
						boost::python::container_utils::extend_container( mv, mo );
						modules.insert( mv.begin(), mv.end() );
						return;
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::moduleDependencies( graphComponent, modules, serialisation );
		}

		std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "constructor" );
					if( f )
					{
						return boost::python::extract<std::string>(
							f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( graphComponent ) ), boost::ref( serialisation ) )
						);
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::constructor( graphComponent, serialisation );
		}

		std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "postConstructor" );
					if( f )
					{
						return boost::python::extract<std::string>(
							f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( graphComponent ) ), identifier, boost::ref( serialisation ) )
						);
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::postConstructor( graphComponent, identifier, serialisation );
		}

		std::string postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "postHierarchy" );
					if( f )
					{
						return boost::python::extract<std::string>(
							f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( graphComponent ) ), identifier, boost::ref( serialisation ) )
						);
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::postHierarchy( graphComponent, identifier, serialisation );
		}

		std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "postScript" );
					if( f )
					{
						return boost::python::extract<std::string>(
							f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( graphComponent ) ), identifier, boost::ref( serialisation ) )
						);
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::postScript( graphComponent, identifier, serialisation );
		}

		bool childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "childNeedsSerialisation" );
					if( f )
					{
						return f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( child ) ), boost::ref( serialisation ) );
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::childNeedsSerialisation( child, serialisation );
		}

		bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "childNeedsConstruction" );
					if( f )
					{
						return f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( child ) ), boost::ref( serialisation ) );
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::childNeedsConstruction( child, serialisation );
		}

};

} // namespace GafferBindings

#include "GafferBindings/SerialisationBinding.inl"
