//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "ConnectionCreatorBinding.h"

#include "GafferUIBindings/GadgetBinding.h"

#include "GafferUI/ConnectionCreator.h"

#include "Gaffer/Plug.h"

#include "IECorePython/ExceptionAlgo.h"

using namespace boost::python;
using namespace GafferUI;
using namespace GafferBindings;
using namespace GafferUIBindings;

namespace
{

struct ConnectionCreatorWrapper : public GadgetWrapper<ConnectionCreator>
{

	ConnectionCreatorWrapper(PyObject *self)
		: GadgetWrapper<ConnectionCreator>( self )
	{
	}

	bool canCreateConnection( const Gaffer::Plug *endpoint ) override
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
				catch( const error_already_set &e )
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
				}
				catch( const error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
		}
		throw IECore::Exception( "No canCreateConnection method defined in Python." );
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
				catch( const error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
		}
		throw IECore::Exception( "No canCreateConnection method defined in Python." );
	}
};

} // namespace

void GafferUIModule::bindConnectionCreator()
{
	GadgetClass<ConnectionCreator, ConnectionCreatorWrapper>( "ConnectionCreator" )
		.def( init<>() )
		.def( "canCreateConnection", &ConnectionCreatorWrapper::canCreateConnection )
		.def( "updateDragEndPoint", &ConnectionCreatorWrapper::updateDragEndPoint )
		.def( "createConnection", &ConnectionCreatorWrapper::createConnection )
	;
}
