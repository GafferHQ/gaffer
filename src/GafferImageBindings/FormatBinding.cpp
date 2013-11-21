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

#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include "boost/python.hpp"
#include "boost/format.hpp"

#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/Serialisation.h"
#include "GafferImageBindings/FormatBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferImage;

namespace GafferImageBindings
{

namespace FormatBindings
{

std::string formatRepr( const GafferImage::Format *format )
{
	if ( format->getDisplayWindow().isEmpty() )
	{
		return std::string( "GafferImage.Format()" );
	}
	else
	{
		Imath::Box2i box( format->getDisplayWindow() );
		return std::string(
			boost::str( boost::format(
				"GafferImage.Format( IECore.Box2i( IECore.V2i( %d, %d ), IECore.V2i( %d, %d ) ), %.3f )" )
				% box.min.x % box.min.y % box.max.x % box.max.y %format->getPixelAspect()
			)
		);
	}
}

} // namespace FormatBindings

struct UnaryFormatSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, const std::string &s )
	{
		try
		{
			slot( s );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

static boost::python::str defaultFormatContextName()
{
	return boost::python::str( Format::defaultFormatContextName.string() );
}

static boost::python::list formatNamesList()
{
	std::vector<std::string> names;
	Format::formatNames( names );
	boost::python::list result;
	for( std::vector<std::string>::const_iterator it = names.begin(); it != names.end(); it++ )
	{
		result.append( *it );
	}
	return result;
}

void bindFormat()
{
	// Useful function pointers to the overloaded members
	static const Format &(*registerFormatPtr1)( const Format &, const std::string & ) (&Format::registerFormat);
	static const Format &(*registerFormatPtr2)( const Format & ) (&Format::registerFormat);
	static void (*removeFormatPtr1)( const Format & ) (&Format::removeFormat);
	static void (*removeFormatPtr2)( const std::string & ) (&Format::removeFormat);
	static void (*setDefaultFormatPtr1)( ScriptNode *scriptNode, const Format & ) (&Format::setDefaultFormat);
	static void (*setDefaultFormatPtr2)( ScriptNode *scriptNode, const std::string & ) (&Format::setDefaultFormat);
	
	class_<Format>( "Format", init<int, int, double>() )
		.def( init< const Imath::Box2i &, double >() )
		.def( init<>() )
		.def( "width", &Format::width )
		.def( "height", &Format::height )
		.def( "getPixelAspect", &Format::getPixelAspect )
		.def( "setPixelAspect", &Format::setPixelAspect )
		.def( "getDisplayWindow", &Format::getDisplayWindow )
		.def( "setDisplayWindow", &Format::setDisplayWindow )
		
		// Static bindings
		.def( "formatAddedSignal", &Format::formatAddedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "formatAddedSignal" )
		.def( "formatRemovedSignal", &Format::formatRemovedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "formatRemovedSignal" )
		.def( "setDefaultFormat", setDefaultFormatPtr1, return_value_policy<reference_existing_object>() )
		.def( "setDefaultFormat", setDefaultFormatPtr2, return_value_policy<reference_existing_object>() ).staticmethod( "setDefaultFormat" )
		.def( "getDefaultFormat", &Format::getDefaultFormat, return_value_policy<return_by_value>() ).staticmethod( "getDefaultFormat" )
		.def( "removeAllFormats", &Format::removeAllFormats ).staticmethod( "removeAllFormats" )
		.def( "registerFormat", registerFormatPtr1, return_value_policy<reference_existing_object>() )
		.def( "registerFormat", registerFormatPtr2, return_value_policy<reference_existing_object>() ).staticmethod( "registerFormat" )
		.def( "removeFormat", removeFormatPtr1, return_value_policy<reference_existing_object>() )
		.def( "removeFormat", removeFormatPtr2, return_value_policy<reference_existing_object>() ).staticmethod( "removeFormat" )
		.def( "formatCount", &Format::formatCount, return_value_policy<return_by_value>() ).staticmethod( "formatCount" )
		.def( "getFormat", &Format::getFormat, return_value_policy<reference_existing_object>() ).staticmethod( "getFormat" )
		.def( "formatName", &Format::formatName ).staticmethod( "formatName" )
		.def( "formatNames", &formatNamesList ).staticmethod( "formatNames" )
		.def( "__eq__", &Format::operator== )
		.def( "__repr__", &GafferImageBindings::FormatBindings::formatRepr )
		.def( "defaultFormatContextName", &defaultFormatContextName ).staticmethod( "defaultFormatContextName" )
	;
	
	SignalBinder<Format::UnaryFormatSignal, DefaultSignalCaller<Format::UnaryFormatSignal>, UnaryFormatSlotCaller >
	::bind( "UnaryFormatSignal" );
	
}


} // namespace IECorePython
