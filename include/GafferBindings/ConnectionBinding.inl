//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2013, John Haddon. All rights reserved.
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERBINDINGS_CONNECTIONBINDING_INL
#define GAFFERBINDINGS_CONNECTIONBINDING_INL

#include "boost/version.hpp"

#include "IECorePython/ScopedGILLock.h"

namespace boost { namespace python {

/// \todo this works for now, but should blatantly be implemented as some rvalue_from_python jobby.
template<>
struct extract<boost::signals::detail::unusable>
{
	extract( PyObject *o ) { m_obj = o; };
	extract( object const &o ) { m_obj = o.ptr();  };
	PyObject *m_obj;
	bool check() const { return m_obj==Py_None; };
	boost::signals::detail::unusable operator()() const { return boost::signals::detail::unusable(); };
};

}}

namespace GafferBindings
{

template<int Arity, typename Signal>
struct DefaultSlotCallerBase;

template<typename Signal>
struct DefaultSlotCallerBase<0, Signal>
{
	typename Signal::slot_result_type operator()( boost::python::object slot )
	{
		return boost::python::extract<typename Signal::slot_result_type>( slot() )();
	}
};

template<typename Signal>
struct DefaultSlotCallerBase<1, Signal>
{
#if BOOST_VERSION < 103900
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg2_type a1 )
#else
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg1_type a1 )
#endif
	{
		return boost::python::extract<typename Signal::slot_result_type>( slot( a1 ) )();
	}
};

template<typename Signal>
struct DefaultSlotCallerBase<2, Signal>
{
#if BOOST_VERSION < 103900
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg2_type a1, typename Signal::arg3_type a2 )
#else
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg1_type a1, typename Signal::arg2_type a2 )
#endif
	{
		return boost::python::extract<typename Signal::slot_result_type>( slot( a1, a2 ) )();
	}
};

template<typename Signal>
struct DefaultSlotCallerBase<3, Signal>
{
#if BOOST_VERSION < 103900
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg2_type a1, typename Signal::arg3_type a2, typename Signal::arg4_type a3 )
#else
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg1_type a1, typename Signal::arg2_type a2, typename Signal::arg3_type a3 )
#endif
	{
		return boost::python::extract<typename Signal::slot_result_type>( slot( a1, a2, a3 ) )();
	}
};

template<typename Signal>
struct DefaultSlotCaller : public DefaultSlotCallerBase<Signal::slot_function_type::arity, Signal>
{
};

template<int Arity, typename Signal, typename Caller>
struct SlotBase;

template<typename Signal, typename Caller>
struct SlotBase<0, Signal, Caller>
{
	SlotBase( Connection *connection )
		:	m_connection( connection )
	{
	}
	typename Signal::slot_result_type operator()()
	{
		IECorePython::ScopedGILLock gilLock;
		return Caller()( m_connection->slot() );
	}
	Connection *m_connection;
};

template<typename Signal, typename Caller>
struct SlotBase<1, Signal, Caller>
{
	SlotBase( Connection *connection )
		:	m_connection( connection )
	{
	}
#if BOOST_VERSION < 103900
	typename Signal::slot_result_type operator()( typename Signal::arg2_type a1 )
#else
	typename Signal::slot_result_type operator()( typename Signal::arg1_type a1 )
#endif
	{
		IECorePython::ScopedGILLock gilLock;
		return Caller()( m_connection->slot(), a1 );
	}
	Connection *m_connection;
};

template<typename Signal, typename Caller>
struct SlotBase<2, Signal, Caller>
{
	SlotBase( Connection *connection )
		:	m_connection( connection )
	{
	}
#if BOOST_VERSION < 103900
	typename Signal::slot_result_type operator()( typename Signal::arg2_type a1, typename Signal::arg3_type a2 )
#else
	typename Signal::slot_result_type operator()( typename Signal::arg1_type a1, typename Signal::arg2_type a2 )
#endif
	{
		IECorePython::ScopedGILLock gilLock;
		return Caller()( m_connection->slot(), a1, a2 );
	}
	Connection *m_connection;
};

template<typename Signal, typename Caller>
struct SlotBase<3, Signal, Caller>
{
	SlotBase( Connection *connection )
		:	m_connection( connection )
	{
	}
#if BOOST_VERSION < 103900
	typename Signal::slot_result_type operator()( typename Signal::arg2_type a1, typename Signal::arg3_type a2, typename Signal::arg4_type a3 )
#else
	typename Signal::slot_result_type operator()( typename Signal::arg1_type a1, typename Signal::arg2_type a2, typename Signal::arg3_type a3 )
#endif
	{
		IECorePython::ScopedGILLock gilLock;
		return Caller()( m_connection->slot(), a1, a2, a3 );
	}
	Connection *m_connection;
};

template<typename Signal, typename Caller>
struct Slot : public SlotBase<Signal::slot_function_type::arity, Signal, Caller>
{
	Slot( Connection *connection )
		:	SlotBase<Signal::slot_function_type::arity, Signal, Caller>( connection )
	{
	}
};

template<typename Signal, typename SlotCaller>
Connection *Connection::create( Signal &s, boost::python::object &slot )
{
	Connection *connection = new Connection;
	connection->m_slot = slot;	
	connection->m_connection = s.connect( Slot<Signal, SlotCaller>( connection ) );
	return connection;
}

template<typename Signal, typename SlotCaller>
Connection *Connection::createInGroup( Signal &s, int group, boost::python::object &slot )
{
	Connection *connection = new Connection;
	connection->m_slot = slot;	
	connection->m_connection = s.connect( group, Slot<Signal, SlotCaller>( connection ) );
	return connection;
}

}; // namespace GafferBindings

#endif // GAFFERBINDINGS_CONNECTIONBINDING_INL
