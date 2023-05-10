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

#pragma once

#include "Gaffer/GraphComponent.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/RunTimeTypedBinding.h"

#include <utility>

namespace GafferBindings
{

template<typename T, typename TWrapper=T>
class GraphComponentClass : public IECorePython::RunTimeTypedClass<T, TWrapper>
{
	public :

		GraphComponentClass( const char *docString = nullptr );

};

template<typename WrappedType>
class GraphComponentWrapper : public IECorePython::RunTimeTypedWrapper<WrappedType>
{

	public :

		template<typename... Args>
		GraphComponentWrapper( PyObject *self, Args&&... args )
			:	IECorePython::RunTimeTypedWrapper<WrappedType>( self, std::forward<Args>( args )... )
		{
		}

		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "acceptsChild" );
					if( f )
					{
						return f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( potentialChild ) ) );
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::acceptsChild( potentialChild );
		}

		bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "acceptsParent" );
					if( f )
					{
						return f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( potentialParent ) ) );
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::acceptsParent( potentialParent );
		}

		void nameChanged( IECore::InternedString oldName ) override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "_nameChanged" );
					if( f )
					{
						f( oldName.string() );
						return;
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::nameChanged( oldName );
		}

		void parentChanging( Gaffer::GraphComponent *newParent ) override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "_parentChanging" );
					if( f )
					{
						f( Gaffer::GraphComponentPtr( newParent ) );
						return;
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::parentChanging( newParent );
		}

		void parentChanged( Gaffer::GraphComponent *oldParent ) override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "_parentChanged" );
					if( f )
					{
						f( Gaffer::GraphComponentPtr( oldParent ) );
						return;
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::parentChanged( oldParent );
		}

};

} // namespace GafferBindings

#include "GafferBindings/GraphComponentBinding.inl"
