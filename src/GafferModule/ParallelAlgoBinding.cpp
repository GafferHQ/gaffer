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

#include "boost/python.hpp"

#include "ParallelAlgoBinding.h"

#include "GafferBindings/SignalBinding.h"

#include "Gaffer/ParallelAlgo.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace Gaffer;
using namespace GafferBindings;
using namespace boost::python;

namespace
{

struct GILReleaseUIThreadFunction
{

	GILReleaseUIThreadFunction( ParallelAlgo::UIThreadFunction function )
		:	m_function( function )
	{
	}

	void operator()()
	{
		IECorePython::ScopedGILRelease gilRelease;
		m_function();
	}

	private :

		ParallelAlgo::UIThreadFunction m_function;

};

struct CallOnUIThreadSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, ParallelAlgo::UIThreadFunction function )
	{
		boost::python::object pythonFunction = make_function(
			GILReleaseUIThreadFunction( function ),
			boost::python::default_call_policies(),
			boost::mpl::vector<void>()
		);
		try
		{
			slot( pythonFunction );
		}
		catch( const boost::python::error_already_set &e )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

void callOnUIThread( boost::python::object f )
{
	auto fPtr = std::make_shared<boost::python::object>( f );
	Gaffer::ParallelAlgo::callOnUIThread(
		[fPtr]() mutable {
			IECorePython::ScopedGILLock gilLock;
			try
			{
				(*fPtr)();
				// We are likely to be the last owner of the python
				// function object. Make sure we release it while we
				// still hold the GIL.
				fPtr.reset();
			}
			catch( boost::python::error_already_set &e )
			{
				fPtr.reset();
				IECorePython::ExceptionAlgo::translatePythonException();
			}
		}
	);
}

} // namespace

void GafferModule::bindParallelAlgo()
{

	object module( borrowed( PyImport_AddModule( "Gaffer.ParallelAlgo" ) ) );
	scope().attr( "ParallelAlgo" ) = module;
	scope moduleScope( module );

	def( "callOnUIThread", &callOnUIThread );
	def( "callOnUIThreadSignal", &Gaffer::ParallelAlgo::callOnUIThreadSignal, boost::python::return_value_policy<boost::python::reference_existing_object>() );

	SignalClass<Gaffer::ParallelAlgo::CallOnUIThreadSignal, DefaultSignalCaller<Gaffer::ParallelAlgo::CallOnUIThreadSignal>, CallOnUIThreadSlotCaller>( "CallOnUIThreadSignal" );

}
