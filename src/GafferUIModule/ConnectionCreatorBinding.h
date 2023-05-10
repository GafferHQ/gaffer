//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine. All rights reserved.
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

#include "GafferUIBindings/GadgetBinding.h"

#include "GafferUI/ConnectionCreator.h"

#include "Gaffer/Plug.h"

#include "IECorePython/ExceptionAlgo.h"

#include "IECore/Exception.h"

namespace GafferUIModule
{

template<typename T, typename TWrapper=T>
class ConnectionCreatorClass : public GafferUIBindings::GadgetClass<T, TWrapper>
{
	public :

		ConnectionCreatorClass( const char *docString = nullptr );

};

template<typename WrappedType>
class ConnectionCreatorWrapper : public GafferUIBindings::GadgetWrapper<WrappedType>
{

	public :

		template<typename... Args>
		ConnectionCreatorWrapper( PyObject *self, Args&&... args )
			:	GafferUIBindings::GadgetWrapper<WrappedType>( self, std::forward<Args>( args )... )
		{
		}

		bool canCreateConnection( const Gaffer::Plug *endpoint ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "canCreateConnection" );
				if( f )
				{
					try
					{
						return f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( endpoint ) ) );
					}
					catch( const boost::python::error_already_set & )
					{
						IECorePython::ExceptionAlgo::translatePythonException();
					}
				}
			}
			throw IECore::Exception( "No canCreateConnection method defined in Python." );
		}

		void updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent ) override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "updateDragEndPoint" );
				if( f )
				{
					try
					{
						f( position, tangent );
						return;
					}
					catch( const boost::python::error_already_set & )
					{
						IECorePython::ExceptionAlgo::translatePythonException();
					}
				}
			}

			if constexpr ( !std::is_same_v<decltype( &WrappedType::updateDragEndPoint ), decltype( &GafferUI::ConnectionCreator::updateDragEndPoint )> )
			{
				// No need to force PlugAdder derived classes to reimplement this.
				WrappedType::updateDragEndPoint( position, tangent );
			}
			else
			{
				throw IECore::Exception( "No updateDragEndPoint method defined in Python." );
			}
		}

		void createConnection( Gaffer::Plug *endpoint ) override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "createConnection" );
				if( f )
				{
					try
					{
						f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( endpoint ) ) );
						return;
					}
					catch( const boost::python::error_already_set & )
					{
						IECorePython::ExceptionAlgo::translatePythonException();
					}
				}
			}
			throw IECore::Exception( "No createConnection method defined in Python." );
		}

};

} // namespace GafferUIModule

#include "ConnectionCreatorBinding.inl"
