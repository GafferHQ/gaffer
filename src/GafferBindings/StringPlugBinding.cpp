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

#include "IECorePython/ScopedGILRelease.h"

#include "Gaffer/StringPlug.h"

#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/StringPlugBinding.h"

using namespace boost::python;
using namespace Gaffer;

namespace
{

void setValue( StringPlug *plug, const char *value )
{
	// we use a GIL release here to prevent a lock in the case where this triggers a graph
	// evaluation which decides to go back into python on another thread:
	IECorePython::ScopedGILRelease r;
	plug->setValue( value );
}

std::string getValue( const StringPlug *plug, const IECore::MurmurHash *precomputedHash )
{
	// Must release GIL in case computation spawns threads which need
	// to reenter Python.
	IECorePython::ScopedGILRelease r;
	return plug->getValue( precomputedHash );
}

} // namespace

void GafferBindings::bindStringPlug()
{

	PlugClass<StringPlug>()
		.def(
			boost::python::init<const std::string &, Gaffer::Plug::Direction, const std::string &, unsigned>(
				(
					boost::python::arg_( "name" )=Gaffer::GraphComponent::defaultName<StringPlug>(),
					boost::python::arg_( "direction" )=Gaffer::Plug::In,
					boost::python::arg_( "defaultValue" )="",
					boost::python::arg_( "flags" )=Gaffer::Plug::Default
				)
			)
		)
		.def( "defaultValue", &StringPlug::defaultValue, return_value_policy<boost::python::copy_const_reference>() )
		.def( "setValue", &setValue )
		.def( "getValue", &getValue, ( boost::python::arg( "_precomputedHash" ) = object() ) )
	;

}
