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

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

std::string repr( const ValuePlug *plug )
{
	return ValuePlugSerialiser::repr( plug );
}

void setFrom( ValuePlug &plug, const ValuePlug &other )
{
	IECorePython::ScopedGILRelease r;
	plug.setFrom( &other );
}

void setToDefault( ValuePlug &plug )
{
	IECorePython::ScopedGILRelease r;
	plug.setToDefault();
}

bool isSetToDefault( ValuePlug *plug )
{
	// we use a GIL release here to prevent a lock in the case where this triggers a graph
	// evaluation which decides to go back into python on another thread:
	IECorePython::ScopedGILRelease r;
	return plug->isSetToDefault();
}

void resetDefault( ValuePlug *plug )
{
	IECorePython::ScopedGILRelease r;
	plug->resetDefault();
}

IECore::MurmurHash hash( ValuePlug *plug )
{
	// we use a GIL release here to prevent a lock in the case where this triggers a graph
	// evaluation which decides to go back into python on another thread:
	IECorePython::ScopedGILRelease r;
	return plug->hash();
}

void hash2( ValuePlug *plug, IECore::MurmurHash &h )
{
	// we use a GIL release here to prevent a lock in the case where this triggers a graph
	// evaluation which decides to go back into python on another thread:
	IECorePython::ScopedGILRelease r;
	plug->hash( h);
}


} // namespace

void GafferModule::bindValuePlug()
{
	scope s = PlugClass<ValuePlug, PlugWrapper<ValuePlug> >()
		.def( boost::python::init<const std::string &, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "name" ) = GraphComponent::defaultName<ValuePlug>(),
					boost::python::arg_( "direction" ) = Plug::In,
					boost::python::arg_( "flags" ) = Plug::Default
				)
			)
		)
		.def( "settable", &ValuePlug::settable )
		.def( "setFrom", setFrom )
		.def( "setToDefault", setToDefault )
		.def( "isSetToDefault", isSetToDefault )
		.def( "resetDefault", resetDefault )
		.def( "defaultHash", &ValuePlug::defaultHash )
		.def( "hash", hash )
		.def( "hash", hash2 )
		.def( "getCacheMemoryLimit", &ValuePlug::getCacheMemoryLimit )
		.staticmethod( "getCacheMemoryLimit" )
		.def( "setCacheMemoryLimit", &ValuePlug::setCacheMemoryLimit )
		.staticmethod( "setCacheMemoryLimit" )
		.def( "cacheMemoryUsage", &ValuePlug::cacheMemoryUsage )
		.staticmethod( "cacheMemoryUsage" )
		.def( "clearCache", &ValuePlug::clearCache )
		.staticmethod( "clearCache" )
		.def( "getHashCacheSizeLimit", &ValuePlug::getHashCacheSizeLimit )
		.staticmethod( "getHashCacheSizeLimit" )
		.def( "setHashCacheSizeLimit", &ValuePlug::setHashCacheSizeLimit )
		.staticmethod( "setHashCacheSizeLimit" )
		.def( "hashCacheTotalUsage", &ValuePlug::hashCacheTotalUsage )
		.staticmethod( "hashCacheTotalUsage" )
		.def( "clearHashCache", &ValuePlug::clearHashCache, arg( "now" ) = false )
		.staticmethod( "clearHashCache" )
		.def( "getHashCacheMode", &ValuePlug::getHashCacheMode )
		.staticmethod( "getHashCacheMode" )
		.def( "setHashCacheMode", &ValuePlug::setHashCacheMode )
		.staticmethod( "setHashCacheMode" )
		.def( "dirtyCount", &ValuePlug::dirtyCount )
		.def( "__repr__", &repr )
	;

	enum_<ValuePlug::HashCacheMode>( "HashCacheMode" )
		.value( "Standard", ValuePlug::HashCacheMode::Standard )
		.value( "Checked", ValuePlug::HashCacheMode::Checked )
		.value( "Legacy", ValuePlug::HashCacheMode::Legacy )
	;

	enum_<ValuePlug::CachePolicy>( "CachePolicy" )
		.value( "Uncached", ValuePlug::CachePolicy::Uncached )
		.value( "Standard", ValuePlug::CachePolicy::Standard )
		.value( "TaskCollaboration", ValuePlug::CachePolicy::TaskCollaboration )
		.value( "TaskIsolation", ValuePlug::CachePolicy::TaskIsolation )
		.value( "Default", ValuePlug::CachePolicy::Default )
		.value( "Legacy", ValuePlug::CachePolicy::Legacy )
	;

	Serialisation::registerSerialiser( Gaffer::ValuePlug::staticTypeId(), new ValuePlugSerialiser );
}
