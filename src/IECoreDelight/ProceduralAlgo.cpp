//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "IECoreDelight/NodeAlgo.h"
#include "IECoreDelight/ParameterList.h"

#include "IECoreScene/ExternalProcedural.h"

#include "IECore/SimpleTypedData.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "fmt/format.h"

#include <nsi.h>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreDelight;

namespace
{

bool convert( const IECoreScene::ExternalProcedural *object, NSIContext_t context, const char *handle )
{
	NSICreate( context, handle, "procedural", 0, nullptr );

	ParameterList procParameters;

	const std::string &filename = object->getFileName();
	std::string type;

	if( boost::ends_with( filename, "lua" ) )
	{
		type = "lua";
	}
	else if ( boost::ends_with( filename, "nsi" ) or boost::ends_with( filename, "nsia" ) )
	{
		type = "apistream";
	}
	else
	{
		type = "dynamiclibrary";
	}

	// 3Delight seems to behave weirdly when passed the boundingbox parameter:
	// doesn't render the procedural content when streaming the NSI scene initially,
	// yet always renders the procedural content when reading a NSI scene from disk.
	// Due to this commenting out the corresponding code for now.
	//
	// const Box3f &bbox = object->getBound();
	//
	// if ( bbox != Box3f( V3f( -0.5, -0.5, -0.5 ), V3f( 0.5, 0.5, 0.5 ) ) )
	// {
	//	procParameters.add( { "boundingbox", bbox.min.getValue(), NSITypePoint, 2, 1, NSIParamIsArray } );
	// }

	procParameters.add( "type", type );
	procParameters.add( "filename", filename );

	for( const auto &parameter : object->parameters()->readable() )
	{
		procParameters.add( parameter.first.c_str(), parameter.second.get(), true );
	}

	NSISetAttribute( context, handle, procParameters.size(), procParameters.data() );
	return true;
}

NodeAlgo::ConverterDescription<ExternalProcedural> g_description( convert );

} // namespace
