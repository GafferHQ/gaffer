//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#ifndef GAFFERBINDINGS_CATCHINGSLOTCALLER_INL
#define GAFFERBINDINGS_CATCHINGSLOTCALLER_INL

#include "boost/version.hpp"

namespace GafferBindings
{

template<int Arity, typename Signal>
struct CatchingSlotCallerBase;

template<typename Signal>
struct CatchingSlotCallerBase<0, Signal>
{
	typename Signal::slot_result_type operator()( boost::python::object slot )
	{
		try
		{
			return boost::python::extract<typename Signal::slot_result_type>( slot() )();
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // also clears the python error status
			return typename Signal::slot_result_type();
		}
	}
};

template<typename Signal>
struct CatchingSlotCallerBase<1, Signal>
{
#if BOOST_VERSION < 103900
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg2_type a1 )
#else
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg1_type a1 )
#endif
	{
		try
		{
			return boost::python::extract<typename Signal::slot_result_type>( slot( a1 ) )();
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // also clears the python error status
			return typename Signal::slot_result_type();
		}
	}
};

template<typename Signal>
struct CatchingSlotCallerBase<2, Signal>
{
#if BOOST_VERSION < 103900
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg2_type a1, typename Signal::arg3_type a2 )
#else
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg1_type a1, typename Signal::arg2_type a2 )
#endif
	{
		try
		{
			return boost::python::extract<typename Signal::slot_result_type>( slot( a1, a2 ) )();
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // also clears the python error status
			return typename Signal::slot_result_type();
		}
	}
};

template<typename Signal>
struct CatchingSlotCallerBase<3, Signal>
{
#if BOOST_VERSION < 103900
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg2_type a1, typename Signal::arg3_type a2, typename Signal::arg4_type a3 )
#else
	typename Signal::slot_result_type operator()( boost::python::object slot, typename Signal::arg1_type a1, typename Signal::arg2_type a2, typename Signal::arg3_type a3 )
#endif
	{
		try
		{
			return boost::python::extract<typename Signal::slot_result_type>( slot( a1, a2, a3 ) )();
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // also clears the python error status
			return typename Signal::slot_result_type();
		}
	}
};

template<typename Signal>
struct CatchingSlotCaller : public CatchingSlotCallerBase<Signal::slot_function_type::arity, Signal>
{
};


} // namespace GafferBindings

#include "GafferBindings/CatchingSlotCaller.inl"

#endif // GAFFERBINDINGS_CATCHINGSLOTCALLER_INL

