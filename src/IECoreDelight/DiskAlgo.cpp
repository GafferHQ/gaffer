//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "IECoreDelight/NodeAlgo.h"
#include "IECoreDelight/ParameterList.h"

#include "IECoreScene/DiskPrimitive.h"

#include <nsi.h>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreDelight;

namespace
{

bool convert( const IECoreScene::DiskPrimitive *object, NSIContext_t context, const char *handle )
{
	NSICreate( context, handle, "particles", 0, nullptr );

	ParameterList parameters;

	const V3f p( 0, 0, object->getZ() );
	parameters.add( {
		"P",
		&p,
		NSITypePoint,
		0,
		1,
		NSIParamPerVertex
	} );

	// Technically speaking, I think the normal should probably
	// point in +ve Z (to be facing a default camera which is facing
	// in -ve Z). But practically speaking we expect disks to only
	// be used as the geometry for spotlights, in which case 3Delight
	// seems to want it to point in -ve Z.
	const V3f n( 0, 0, -1 );
	parameters.add( {
		"N",
		&n,
		NSITypeNormal,
		0,
		1,
		NSIParamPerVertex
	} );

	const float width = object->getRadius() * 2;
	parameters.add( {
		"width",
		&width,
		NSITypeFloat,
		0,
		1,
		NSIParamPerVertex
	} );

	NSISetAttribute( context, handle, parameters.size(), parameters.data() );
	return true;
}

NodeAlgo::ConverterDescription<DiskPrimitive> g_description( convert );

} // namespace
