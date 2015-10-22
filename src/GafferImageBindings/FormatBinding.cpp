//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
#include "boost/format.hpp"
#include "boost/lexical_cast.hpp"

#include "GafferImageBindings/FormatBinding.h"

using namespace boost::python;
using namespace GafferImage;

namespace
{

boost::python::list registeredFormats()
{
	std::vector<std::string> names;
	Format::registeredFormats( names );
	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

std::string formatRepr( const GafferImage::Format &format )
{
	if ( format.getDisplayWindow().isEmpty() )
	{
		return std::string( "GafferImage.Format()" );
	}
	else if ( format.getDisplayWindow().min == Imath::V2i( 0 ) )
	{
		Imath::Box2i box( format.getDisplayWindow() );
		return std::string(
			boost::str( boost::format(
				"GafferImage.Format( %d, %d, %.3f )" )
				% box.max.x % box.max.y % format.getPixelAspect()
			)
		);
	}
	else
	{
		Imath::Box2i box( format.getDisplayWindow() );
		return std::string(
			boost::str( boost::format(
				"GafferImage.Format( IECore.Box2i( IECore.V2i( %d, %d ), IECore.V2i( %d, %d ) ), %.3f )" )
				% box.min.x % box.min.y % box.max.x % box.max.y % format.getPixelAspect()
			)
		);
	}
}

} // namespace

void GafferImageBindings::bindFormat()
{
	class_<Format>( "Format" )

		.def(
			init<int, int, double>(
				(
					boost::python::arg( "width" ),
					boost::python::arg( "height" ),
					boost::python::arg( "pixelAspect" ) = 1.0f
				)
			)
		)
		.def(
			init<const Imath::Box2i &, double, bool>(
				(
					boost::python::arg( "displayWindow" ),
					boost::python::arg( "pixelAspect" ) = 1.0f,
					boost::python::arg( "fromEXRSpace" ) = false
				)
			)
		)

		.def( "width", &Format::width )
		.def( "height", &Format::height )
		.def( "getPixelAspect", &Format::getPixelAspect )
		.def( "setPixelAspect", &Format::setPixelAspect )
		.def( "getDisplayWindow", &Format::getDisplayWindow, return_value_policy<copy_const_reference>() )
		.def( "setDisplayWindow", &Format::setDisplayWindow )

		.def( "fromEXRSpace", ( int (Format::*)( int ) const )&Format::fromEXRSpace )
		.def( "fromEXRSpace", ( Imath::V2i (Format::*)( const Imath::V2i & ) const )&Format::fromEXRSpace )
		.def( "fromEXRSpace", ( Imath::Box2i (Format::*)( const Imath::Box2i & ) const )&Format::fromEXRSpace )

		.def( "toEXRSpace", ( int (Format::*)( int ) const )&Format::toEXRSpace )
		.def( "toEXRSpace", ( Imath::V2i (Format::*)( const Imath::V2i & ) const )&Format::toEXRSpace )
		.def( "toEXRSpace", ( Imath::Box2i (Format::*)( const Imath::Box2i & ) const )&Format::toEXRSpace )

		.def( "__eq__", &Format::operator== )
		.def( "__repr__", &formatRepr )
		.def( "__str__", &boost::lexical_cast<std::string, Format> )

		.def( "registerFormat", &Format::registerFormat ).staticmethod( "registerFormat" )
		.def( "deregisterFormat", &Format::deregisterFormat ).staticmethod( "deregisterFormat" )
		.def( "registeredFormats", &registeredFormats ).staticmethod( "registeredFormats" )
		.def( "format", &Format::format ).staticmethod( "format" )
		.def( "name", &Format::name ).staticmethod( "name" )
	;

}
