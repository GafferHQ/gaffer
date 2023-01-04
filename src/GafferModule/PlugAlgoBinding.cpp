//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "PlugAlgoBinding.h"

#include "Gaffer/Plug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ValuePlug.h"

#include "IECorePython/RefCountedBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;

namespace
{

void replacePlug( GraphComponent &parent, Plug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	PlugAlgo::replacePlug( &parent, &plug );
}

ValuePlugPtr createPlugFromData( const std::string &name, Plug::Direction direction, unsigned flags, const IECore::Data *value )
{
	IECorePython::ScopedGILRelease gilRelease;
	return PlugAlgo::createPlugFromData( name, direction, flags, value );
}

IECore::DataPtr getValueAsData( const ValuePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return PlugAlgo::getValueAsData( &plug );
}

IECore::DataPtr extractDataFromPlug( const ValuePlug &plug )
{
	return getValueAsData( plug );
}

bool setLeafValueFromData( const ValuePlug *plug, ValuePlug *leafPlug, const IECore::Data *value )
{
	IECorePython::ScopedGILRelease gilRelease;
	return PlugAlgo::setValueFromData( plug, leafPlug, value );
}

bool setValueFromData( ValuePlug *plug, const IECore::Data *value )
{
	IECorePython::ScopedGILRelease gilRelease;
	return PlugAlgo::setValueFromData( plug, value );
}

bool canSetValueFromData( const ValuePlug *plug, const IECore::Data *value )
{
	IECorePython::ScopedGILRelease gilRelease;
	return PlugAlgo::canSetValueFromData( plug, value );
}

PlugPtr promote( Plug &plug, Plug *parent, const IECore::StringAlgo::MatchPattern &excludeMetadata )
{
	IECorePython::ScopedGILRelease gilRelease;
	return PlugAlgo::promote( &plug, parent, excludeMetadata );
}

PlugPtr promoteWithName( Plug &plug, const IECore::InternedString &name, Plug *parent, const IECore::StringAlgo::MatchPattern &excludeMetadata )
{
	IECorePython::ScopedGILRelease gilRelease;
	return PlugAlgo::promoteWithName( &plug, name, parent, excludeMetadata );
}

void unpromote( Plug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	PlugAlgo::unpromote( &plug );
}

} // namespace

void GafferModule::bindPlugAlgo()
{
	object module( borrowed( PyImport_AddModule( "Gaffer.PlugAlgo" ) ) );
	scope().attr( "PlugAlgo" ) = module;
	scope moduleScope( module );

	def( "replacePlug", &replacePlug, ( arg( "parent" ), arg( "plug" ) ) );
	def( "dependsOnCompute", &PlugAlgo::dependsOnCompute );

	def( "createPlugFromData", &createPlugFromData );
	def( "extractDataFromPlug", &extractDataFromPlug );
	def( "getValueAsData", &getValueAsData );
	def( "setValueFromData", &setLeafValueFromData );
	def( "setValueFromData", &setValueFromData );
	def( "canSetValueFromData", &canSetValueFromData, ( arg( "plug" ), arg( "value" ) = object() ) );

	def( "canPromote", &PlugAlgo::canPromote, ( arg( "plug" ), arg( "parent" ) = object() ) );
	def( "promote", &promote, ( arg( "plug" ), arg( "parent" ) = object(), arg( "excludeMetadata" ) = "layout:*" ) );
	def( "promoteWithName", &promoteWithName, ( arg( "plug" ), arg( "name" ), arg( "parent" ) = object(), arg( "excludeMetadata" ) = "layout:*" ) );
	def( "isPromoted", &PlugAlgo::isPromoted, ( arg( "plug" ) ) );
	def( "unpromote", &unpromote, ( arg( "plug" ) ) );

}
