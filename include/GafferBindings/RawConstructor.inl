//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "boost/functional.hpp"

namespace GafferBindings
{

namespace Detail
{

template <class F>
struct RawConstructorDispatcher
{

	using ResultType = typename boost::binary_traits<F>::result_type;

	RawConstructorDispatcher( F f )
		: m_f( f )
	{
	}

	PyObject *operator()( PyObject *args, PyObject *keywords )
	{
		ResultType t = m_f(

			boost::python::tuple( boost::python::detail::borrowed_reference( args ) ),
			keywords ? boost::python::dict( boost::python::detail::borrowed_reference( keywords ) ) : boost::python::dict()

		);

		boost::python::detail::install_holder<ResultType> i( args );
		i( t );

		return boost::python::detail::none();
	}

	private:

		F m_f;

};

} // namespace Detail

template<typename F>
boost::python::object rawConstructor( F f )
{

	static boost::python::detail::keyword k;

	return boost::python::objects::function_object(

		boost::python::objects::py_function(

			Detail::RawConstructorDispatcher<F>( f ),
			boost::mpl::vector1<PyObject*>(),
			1,
			(std::numeric_limits<unsigned>::max)()

		),

		boost::python::detail::keyword_range( &k, &k )

	);
}

} // namespace GafferBindings
