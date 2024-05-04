//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "TransformBinding.h"

#include "GafferImage/ContactSheetCore.h"
#include "GafferImage/Crop.h"
#include "GafferImage/ImageTransform.h"
#include "GafferImage/Mirror.h"
#include "GafferImage/Offset.h"
#include "GafferImage/Resample.h"
#include "GafferImage/Resize.h"

#include "GafferBindings/DependencyNodeBinding.h"

using namespace boost::python;
using namespace GafferImage;
using namespace GafferBindings;

void GafferImageModule::bindTransforms()
{

	GafferBindings::DependencyNodeClass<ContactSheetCore>();
	GafferBindings::DependencyNodeClass<ImageTransform>();
	GafferBindings::DependencyNodeClass<Mirror>();
	GafferBindings::DependencyNodeClass<Offset>();

	{
		scope s = GafferBindings::DependencyNodeClass<Resize>();

		enum_<Resize::FitMode>( "FitMode" )
			.value( "Horizontal", Resize::Horizontal )
			.value( "Vertical", Resize::Vertical )
			.value( "Fit", Resize::Fit )
			.value( "Fill", Resize::Fill )
			.value( "Distort", Resize::Distort )
		;
	}

	{
		scope s = GafferBindings::DependencyNodeClass<Resample>();

		enum_<Resample::Debug>( "Debug")
			.value( "Off", Resample::Off )
			.value( "HorizontalPass", Resample::HorizontalPass )
			.value( "SinglePass", Resample::SinglePass )
		;
	}

	{
		scope s = GafferBindings::DependencyNodeClass<Crop>();

		enum_<Crop::AreaSource>( "AreaSource" )
			.value( "Area", Crop::Area )
			.value( "Format", Crop::Format )
			.value( "DataWindow", Crop::DataWindow )
			.value( "DisplayWindow", Crop::DisplayWindow )
		;
	}

}
