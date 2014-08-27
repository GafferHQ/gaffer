//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "GafferBindings/ConnectionBinding.h"

using namespace boost::python;
using namespace GafferBindings;

Connection::Connection()
{
}

Connection::~Connection()
{
	disconnect();
}

void Connection::disconnect() const
{
	m_connection.disconnect();
}

bool Connection::connected() const
{
	return m_connection.connected();
}

void Connection::block()
{
	m_connection.block();
}

void Connection::unblock()
{
	m_connection.unblock();
}

bool Connection::blocked() const
{
	return m_connection.blocked();
}

boost::python::object Connection::slot()
{
	return m_slot;
}

void GafferBindings::bindConnection()
{
	class_<Connection, boost::noncopyable>( "Connection", no_init )
		.def( "disconnect", &Connection::disconnect )
		.def( "connected", &Connection::connected )
		.def( "block", &Connection::block )
		.def( "unblock", &Connection::unblock )
		.def( "blocked", &Connection::blocked )
		.def( "slot", &Connection::slot )
	;
}
