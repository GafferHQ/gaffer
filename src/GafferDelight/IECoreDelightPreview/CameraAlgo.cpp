//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "nsi.h"

#include "IECore/Camera.h"
#include "IECore/SimpleTypedData.h"

#include "GafferDelight/IECoreDelightPreview/NodeAlgo.h"
#include "GafferDelight/IECoreDelightPreview/ParameterList.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreDelight;

namespace
{

bool convert( const IECore::Camera *camera, NSIContext_t context, const char *handle )
{
	CameraPtr cameraCopy = camera->copy();
	cameraCopy->addStandardParameters();

	const string &projection = cameraCopy->parametersData()->member<StringData>( "projection", true )->readable();
	const string nodeType = projection + "camera";

	NSICreate( context, handle, nodeType.c_str(), 0, nullptr );

	ParameterList parameters;

	if( projection == "perspective" )
	{
		parameters.add( "fov", cameraCopy->parametersData()->member<FloatData>( "projection:fov", true ) );
	}

	const V2i &resolution = cameraCopy->parametersData()->member<V2iData>( "resolution", true )->readable();
	parameters.add( { "resolution", resolution.getValue(), NSITypeInteger, 2, 1, NSIParamIsArray } );

	const Box2f &screenWindow = cameraCopy->parametersData()->member<Box2fData>( "screenWindow", true )->readable();
	const Box2d screenWindowD( screenWindow.min, screenWindow.max );
	parameters.add( { "screenWindow", screenWindowD.min.getValue(), NSITypeDouble, 2, 2, NSIParamIsArray } );

	const float pixelAspectRatio = cameraCopy->parametersData()->member<FloatData>( "pixelAspectRatio", true )->readable();
	parameters.add( { "pixelaspectratio", &pixelAspectRatio, NSITypeFloat, 0, 1, 0 } );

	const V2d clippingPlanes = cameraCopy->parametersData()->member<V2fData>( "clippingPlanes", true )->readable();
	parameters.add( { "clippingrange", clippingPlanes.getValue(), NSITypeDouble, 0, 2, 0 } );

	const V2d shutter = cameraCopy->parametersData()->member<V2fData>( "shutter", true )->readable();
	parameters.add( { "shutterrange", shutter.getValue(), NSITypeDouble, 0, 2, 0 } );

	/// \todo Support renderRegion

	NSISetAttribute( context, handle, parameters.size(), parameters.data() );

	return true;
}

NodeAlgo::ConverterDescription<Camera> g_description( convert );

} // namespace
