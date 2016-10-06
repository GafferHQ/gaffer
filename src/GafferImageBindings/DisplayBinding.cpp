//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "GafferImage/Display.h"
#include "GafferImageBindings/DisplayBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace GafferImage;
using namespace GafferBindings;

namespace
{

struct DriverCreatedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, IECore::DisplayDriver *driver, const IECore::CompoundData *parameters )
	{
		try
		{
			slot( IECore::DisplayDriverPtr( driver ), IECore::CompoundDataPtr( const_cast<IECore::CompoundData *>( parameters ) ) );
		}
		catch( const error_already_set &e )
		{
			translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

} // namespace

void GafferImageBindings::bindDisplay()
{

	scope s = GafferBindings::DependencyNodeClass<Display>()
		.def( "setDriver", &Display::setDriver )
		.def( "getDriver", (IECore::DisplayDriver *(Display::*)())&Display::getDriver, return_value_policy<CastToIntrusivePtr>() )
		.def( "driverCreatedSignal", &Display::driverCreatedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "driverCreatedSignal" )
		.def( "dataReceivedSignal", &Display::dataReceivedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "dataReceivedSignal" )
		.def( "imageReceivedSignal", &Display::imageReceivedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "imageReceivedSignal" )
	;

	SignalClass<Display::DriverCreatedSignal, DefaultSignalCaller<Display::DriverCreatedSignal>, DriverCreatedSlotCaller>( "DriverCreated" );

}
