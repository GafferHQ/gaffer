//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "CatalogueBinding.h"

#include "GafferImage/Catalogue.h"
#include "GafferImage/Display.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferImage;

namespace
{

struct DriverCreatedSlotCaller
{
	void operator()( boost::python::object slot, IECoreImage::DisplayDriver *driver, const IECore::CompoundData *parameters )
	{
		try
		{
			slot( IECoreImage::DisplayDriverPtr( driver ), IECore::CompoundDataPtr( const_cast<IECore::CompoundData *>( parameters ) ) );
		}
		catch( const error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

class CatalogueSerialiser : public NodeSerialiser
{

	bool childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
	{
		if( child == child->parent<Catalogue>()->outPlug() )
		{
			/// \todo We don't want to serialise the output plug
			/// because that means an unnecessary `setInput()`
			/// call is emitted, revealing some of our internal
			/// implementation. It feels like we should be able to get this
			/// right by default on the NodeSerialiser, but this might
			/// have a few knock on effects that would require a major
			/// version. Note that we can't do the simple thing and turn off
			/// the Plug::Serialisable flag in the Catalogue constructor
			/// because that means that a promoted plug won't be serialised
			/// either.
			return false;
		}
		return NodeSerialiser::childNeedsSerialisation( child, serialisation );
	}

};

void copyFrom( Catalogue::Image &image, const Catalogue::Image *other )
{
	IECorePython::ScopedGILRelease gilRelease;
	image.copyFrom( other );
}

void save( Catalogue::Image &image, const std::filesystem::path &fileName )
{
	IECorePython::ScopedGILRelease gilRelease;
	image.save( fileName );
}

std::filesystem::path generateFileName1( Catalogue &catalogue, const Catalogue::Image *image )
{
	IECorePython::ScopedGILRelease gilRelease;
	return catalogue.generateFileName( image );
}

std::filesystem::path generateFileName2( Catalogue &catalogue, const ImagePlug *image )
{
	IECorePython::ScopedGILRelease gilRelease;
	return catalogue.generateFileName( image );
}

} // namespace

void GafferImageModule::bindCatalogue()
{

	{
		scope s = GafferBindings::DependencyNodeClass<Display>()
			.def( "setDriver", &Display::setDriver, ( arg( "driver" ), arg( "copy" ) = false ) )
			.def( "getDriver", (IECoreImage::DisplayDriver *(Display::*)())&Display::getDriver, return_value_policy<CastToIntrusivePtr>() )
			.def( "driverCreatedSignal", &Display::driverCreatedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "driverCreatedSignal" )
			.def( "imageReceivedSignal", &Display::imageReceivedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "imageReceivedSignal" )
		;

		SignalClass<Display::DriverCreatedSignal, DefaultSignalCaller<Display::DriverCreatedSignal>, DriverCreatedSlotCaller>( "DriverCreated" );
	}

	{
		scope s = GafferBindings::DependencyNodeClass<Catalogue>()
			.def( "generateFileName", &generateFileName1 )
			.def( "generateFileName", &generateFileName2 )
			.def( "displayDriverServer", &Catalogue::displayDriverServer, return_value_policy<IECorePython::CastToIntrusivePtr>() )
			.staticmethod( "displayDriverServer" )
		;

		GafferBindings::PlugClass<Catalogue::Image>()
			.def(
				init<const std::string &, Plug::Direction, unsigned>(
					(
						boost::python::arg_( "name" ) = GraphComponent::defaultName<Catalogue::Image>(),
						boost::python::arg_( "direction" ) = Plug::In,
						boost::python::arg_( "flags" ) = Plug::Default
					)
				)
			)
			.def( "copyFrom", &copyFrom )
			.def( "load", Catalogue::Image::load )
			.def( "save", &save )
			.staticmethod( "load" )
			.attr( "__qualname__" ) = "Catalogue.Image"
		;

		Serialisation::registerSerialiser( Catalogue::staticTypeId(), new CatalogueSerialiser );
	}

	// Expose Catalogue::InternalImages as if they were plain ImageNodes. We don't
	// want to bind them fully because then we'd be exposing a private class, but
	// we need to register them so that they can be returned to Python
	// successfully when inspecting Catalogue internals in the UI.
	//
	// See "Boost.Python and slightly more tricky inheritance" at
	// http://lists.boost.org/Archives/boost/2005/09/93017.php for more details.

	boost::python::objects::copy_class_object(
		type_id<ImageNode>(), Catalogue::internalImageTypeInfo()
	);

}
