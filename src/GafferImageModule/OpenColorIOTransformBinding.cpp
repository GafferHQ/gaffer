//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "OpenColorIOTransformBinding.h"

#include "GafferImage/CDL.h"
#include "GafferImage/ColorSpace.h"
#include "GafferImage/DisplayTransform.h"
#include "GafferImage/LookTransform.h"
#include "GafferImage/LUT.h"
#include "GafferImage/OpenColorIOTransform.h"
#include "GafferImage/Saturation.h"

#include "GafferBindings/DependencyNodeBinding.h"

using namespace boost::python;
using namespace GafferImage;

namespace
{

boost::python::list availableColorSpaces()
{
	std::vector<std::string> e;
	OpenColorIOTransform::availableColorSpaces( e );

	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = e.begin(), eIt = e.end(); it != eIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

boost::python::list availableRoles()
{
	std::vector<std::string> e;
	OpenColorIOTransform::availableRoles( e );

	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = e.begin(), eIt = e.end(); it != eIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

boost::python::list supportedExtensions()
{
	std::vector<std::string> e;
	LUT::supportedExtensions( e );

	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = e.begin(), eIt = e.end(); it != eIt; ++it )
	{
		result.append( *it );
	}

	return result;
}

} // namespace

void GafferImageModule::bindOpenColorIOTransform()
{

	GafferBindings::DependencyNodeClass<ColorProcessor>();

	// This probably shouldn't live in this file, but neither should the ColorProcessor line above?
	GafferBindings::DependencyNodeClass<Saturation>();

	GafferBindings::DependencyNodeClass<OpenColorIOTransform>()
		.def( "availableColorSpaces", &availableColorSpaces ).staticmethod( "availableColorSpaces" )
		.def( "availableRoles", &availableRoles ).staticmethod( "availableRoles" )
	;

	GafferBindings::DependencyNodeClass<ColorSpace>();
	GafferBindings::DependencyNodeClass<DisplayTransform>();
	GafferBindings::DependencyNodeClass<LookTransform>();

	{
		scope s = GafferBindings::DependencyNodeClass<LUT>()
			.def( "supportedExtensions", &supportedExtensions ).staticmethod( "supportedExtensions" )
		;

		enum_<LUT::Interpolation>( "Interpolation" )
			.value( "Best", LUT::Best )
			.value( "Nearest", LUT::Nearest )
			.value( "Linear", LUT::Linear )
			.value( "Tetrahedral", LUT::Tetrahedral )
		;

		enum_<LUT::Direction>( "Direction" )
			.value( "Forward", LUT::Forward )
			.value( "Inverse", LUT::Inverse )
		;
	}

	{
		scope s = GafferBindings::DependencyNodeClass<CDL>()
		;

		enum_<CDL::Direction>( "Direction" )
			.value( "Forward", CDL::Forward )
			.value( "Inverse", CDL::Inverse )
		;
	}

}
