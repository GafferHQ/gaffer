//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "ValuePlugBinding.h"

#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/Serialisation.h"

#include "Gaffer/ValuePlug.h"
#include "Gaffer/Node.h"
#include "Gaffer/Context.h"
#include "Gaffer/Reference.h"
#include "Gaffer/Metadata.h"

#include "boost/format.hpp"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

std::string repr( const ValuePlug *plug )
{
	return ValuePlugSerialiser::repr( plug );
}

} // namespace

void GafferModule::bindValuePlug()
{
	PlugClass<ValuePlug, PlugWrapper<ValuePlug> >()
		.def( boost::python::init<const std::string &, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "name" ) = GraphComponent::defaultName<ValuePlug>(),
					boost::python::arg_( "direction" ) = Plug::In,
					boost::python::arg_( "flags" ) = Plug::Default
				)
			)
		)
		.def( "settable", &ValuePlug::settable )
		.def( "setFrom", &ValuePlug::setFrom )
		.def( "setToDefault", &ValuePlug::setToDefault )
		.def( "isSetToDefault", &ValuePlug::isSetToDefault )
		.def( "hash", (IECore::MurmurHash (ValuePlug::*)() const)&ValuePlug::hash )
		.def( "hash", (void (ValuePlug::*)( IECore::MurmurHash & ) const)&ValuePlug::hash )
		.def( "getCacheMemoryLimit", &ValuePlug::getCacheMemoryLimit )
		.staticmethod( "getCacheMemoryLimit" )
		.def( "setCacheMemoryLimit", &ValuePlug::setCacheMemoryLimit )
		.staticmethod( "setCacheMemoryLimit" )
		.def( "cacheMemoryUsage", &ValuePlug::cacheMemoryUsage )
		.staticmethod( "cacheMemoryUsage" )
		.def( "clearCache", &ValuePlug::clearCache )
		.staticmethod( "clearCache" )
		.def( "__repr__", &repr )
	;

	Serialisation::registerSerialiser( Gaffer::ValuePlug::staticTypeId(), new ValuePlugSerialiser );
}
