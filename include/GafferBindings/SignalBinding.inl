//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2013, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERBINDINGS_SIGNALBINDING_INL
#define GAFFERBINDINGS_SIGNALBINDING_INL

#include "Gaffer/Signals.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

#include "boost/version.hpp"

namespace GafferBindings
{

namespace Detail
{

template<typename Signal, typename Caller>
struct Slot;

template<typename Result, typename... Args, typename Combiner, typename Caller>
struct Slot<Gaffer::Signals::Signal<Result( Args... ), Combiner>, Caller>
{

	Slot( boost::python::object slot )
		:	m_slot( boost::python::borrowed( slot.ptr() ) )
	{

	}

	~Slot()
	{
		IECorePython::ScopedGILLock gilLock;
		m_slot.reset();
	}

	Result operator()( Args&&... args )
	{
		IECorePython::ScopedGILLock gilLock;
		try
		{
			if constexpr( std::is_void_v<Result> )
			{
				Caller()( boost::python::object( m_slot ), std::forward<Args>( args )... );
			}
			else
			{
				return Caller()( boost::python::object( m_slot ), std::forward<Args>( args )... );
			}
		}
		catch( const boost::python::error_already_set &e )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}

	boost::python::handle<PyObject> m_slot;

};

// Overload boost's `visit_each()` function for all our Slot types.
// Signal will call this to discover slots which refer to `Trackable`
// objects, and will use it to automatically remove the connection
// when the `Trackable` object dies.
template<typename Visitor, typename Signal, typename Caller>
void visit_each( Visitor &visitor, const Slot<Signal, Caller> &slot, int )
{
	// Check to see if slot contains a WeakMethod referring to a trackable
	// object. There is no point checking for regular methods, because they
	// prevent the trackable object from dying until it has been disconnected
	// manually. We deliberately "leak" the static variables because doing
	// otherwise would cause the destruction of PyObjects _after_ Python has
	// been shut down (during application exit).
	static boost::python::object *g_gaffer = new boost::python::object( boost::python::import( "Gaffer" ) );
	static boost::python::object *g_weakMethod = new boost::python::object( g_gaffer->attr( "WeakMethod" ) );
	if( PyObject_IsInstance( slot.m_slot.get(), g_weakMethod->ptr() ) )
	{
		boost::python::object self = boost::python::object( slot.m_slot ).attr( "instance" )();
		boost::python::extract<Gaffer::Signals::Trackable &> e( self );
		if( e.check() )
		{
			boost::visit_each( visitor, e(), 0 );
		}
	}
}

GAFFERBINDINGS_API boost::python::object pythonConnection( const Gaffer::Signals::Connection &connection, bool scoped );

template<typename Signal, typename SlotCaller>
boost::python::object connect( Signal &s, boost::python::object &slot, bool scoped )
{
	return pythonConnection( s.connect( Slot<Signal, SlotCaller>( slot ) ), scoped );
}

template<typename Signal, typename SlotCaller>
boost::python::object connectFront( Signal &s, boost::python::object &slot, bool scoped )
{
	return pythonConnection( s.connectFront( Slot<Signal, SlotCaller>( slot ) ), scoped );
}

} // namespace Detail

template<typename Signal>
struct DefaultSignalCaller;

template<typename Result, typename... Args, typename Combiner>
struct DefaultSignalCaller<Gaffer::Signals::Signal<Result( Args... ), Combiner>>
{

	using Signal = Gaffer::Signals::Signal<Result( Args... ), Combiner>;

	static Result call( Signal &s, Args... args )
	{
		IECorePython::ScopedGILRelease gilRelease;
		return s( args... );
	}

};

template<typename Signal>
struct DefaultSlotCaller;

template<typename Result, typename... Args, typename Combiner>
struct DefaultSlotCaller<Gaffer::Signals::Signal<Result( Args... ), Combiner>>
{

	Result operator()( boost::python::object slot, Args&&... args )
	{
		if constexpr( std::is_void_v<Result> )
		{
			slot( std::forward<Args>( args )... );
		}
		else
		{
			return boost::python::extract<Result>( slot( std::forward<Args>( args )... ) )();
		}
	}

};

template<typename Signal, typename SignalCaller, typename SlotCaller>
SignalClass<Signal, SignalCaller, SlotCaller>::SignalClass( const char *className, const char *docString )
	:	boost::python::class_<Signal, boost::noncopyable>( className, docString )
{
	this->def( "connect", &Detail::connect<Signal, SlotCaller>, ( boost::python::arg( "slot" ), boost::python::arg( "scoped" ) = true ) );
	this->def( "connectFront", &Detail::connectFront<Signal, SlotCaller>, (boost::python::arg( "slot" ), boost::python::arg( "scoped" ) = true ) );
	this->def( "disconnectAllSlots", &Signal::disconnectAllSlots );
	this->def( "numSlots", &Signal::numSlots );
	this->def( "empty", &Signal::empty );
	this->def( "__call__", &SignalCaller::call );
}

} // namespace GafferBindings

#endif // GAFFERBINDINGS_SIGNALBINDING_INL
