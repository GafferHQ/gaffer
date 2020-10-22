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

#include "SerialisationBinding.h"

#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/MetadataBinding.h"
#include "GafferBindings/Serialisation.h"
#include "GafferBindings/SerialisationBinding.h"

#include "Gaffer/Context.h"
#include "Gaffer/Plug.h"

#include "IECorePython/ScopedGILLock.h"

#include "IECore/MessageHandler.h"

#include "boost/format.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"
#include "boost/tokenizer.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;
using namespace boost::python;

namespace
{

GraphComponentPtr parent( const Serialisation &serialisation )
{
	return const_cast<GraphComponent *>( serialisation.parent() );
}

std::string childIdentifier( const Serialisation &serialisation, const std::string &parentIdentifier, const GraphComponent *child )
{
	return serialisation.childIdentifier( parentIdentifier, child );
}

std::string objectToBase64Wrapper( const IECore::Object *object )
{
	IECorePython::ScopedGILRelease gilRelease;
	return Serialisation::objectToBase64( object );
}

IECore::ObjectPtr objectFromBase64Wrapper( const std::string &base64String )
{
	IECorePython::ScopedGILRelease gilRelease;
	return Serialisation::objectFromBase64( base64String );
}

} // namespace

void GafferModule::bindSerialisation()
{

	scope s = boost::python::class_<Serialisation>( "Serialisation", no_init )
		.def(
			init<const Gaffer::GraphComponent *, const std::string &, const Gaffer::Set *>
			(
				(
					arg( "parent" ),
					arg( "parentName" ) = "parent",
					arg( "filter" ) = object()
				)
			)
		)
		.def( "parent", &parent )
		.def( "identifier", &Serialisation::identifier )
		.def( "childIdentifier", &childIdentifier )
		.def( "result", &Serialisation::result )
		.def( "modulePath", (std::string (*)( object & ))&Serialisation::modulePath )
		.staticmethod( "modulePath" )
		.def( "classPath", (std::string (*)( object & ))&Serialisation::classPath )
		.staticmethod( "classPath" )
		.def( "objectToBase64", &objectToBase64Wrapper )
		.staticmethod( "objectToBase64" )
		.def( "objectFromBase64", &objectFromBase64Wrapper )
		.staticmethod( "objectFromBase64" )
		.def( "registerSerialiser", &Serialisation::registerSerialiser )
		.staticmethod( "registerSerialiser" )
		.def( "acquireSerialiser", &Serialisation::acquireSerialiser, return_value_policy<reference_existing_object>() )
		.staticmethod( "acquireSerialiser" )
	;

	SerialiserClass<Serialisation::Serialiser, IECore::RefCounted, SerialiserWrapper<Serialisation::Serialiser>>( "Serialiser" );

}
