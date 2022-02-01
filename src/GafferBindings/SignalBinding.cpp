//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "GafferBindings/SignalBinding.h"

using namespace boost::python;

namespace GafferBindings
{

namespace Detail
{

boost::python::object pythonConnection( const Gaffer::Signals::Connection &connection, const boost::python::object &scoped )
{
	bool useScopedConnection;
	if( scoped == boost::python::object() )
	{
		const char *warning =
			"The default value for `scoped` is deprecated. "
			"Please pass `scoped = True` to keep the previous behaviour, "
			"or consider using an unscoped connection."
		;
		if( PyErr_WarnEx( PyExc_DeprecationWarning, warning, 1 ) == -1 )
		{
			// Warning being treated as an error.
			throw_error_already_set();
		}
		useScopedConnection = true;
	}
	else
	{
		useScopedConnection = extract<bool>( scoped );
	}

	if( useScopedConnection )
	{
		// Simply returning `object( scoped_connection( connection ) )`
		// doesn't work - somehow the scoped_connection dies and the
		// connection is disconnected before we get into python. So
		// we construct via the python-bound copy constructor which
		// avoids the problem.
		PyTypeObject *type = boost::python::converter::registry::query(
			boost::python::type_info( typeid( Gaffer::Signals::ScopedConnection ) )
		)->get_class_object();

		boost::python::object oType( boost::python::handle<>( boost::python::borrowed( type ) ) );
		return oType( boost::python::object( connection ) );
	}
	else
	{
		return boost::python::object( connection );
	}
}

} // namespace Detail

} // namespace GafferBindings
