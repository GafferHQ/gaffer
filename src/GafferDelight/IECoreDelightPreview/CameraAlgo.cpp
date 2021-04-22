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

#include "GafferDelight/IECoreDelightPreview/NodeAlgo.h"
#include "GafferDelight/IECoreDelightPreview/ParameterList.h"

#include "IECoreScene/Camera.h"

#include "IECore/SimpleTypedData.h"

#include <nsi.h>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreDelight;

namespace
{

bool convert( const IECoreScene::Camera *camera, NSIContext_t context, const char *handle )
{
	const string &projection = camera->getProjection();
	const string nodeType = projection + "camera";

	NSICreate( context, handle, nodeType.c_str(), 0, nullptr );

	ParameterList parameters;

	const float fov = 90.0f;
	const int dofEnable = 1;
	const double fStop = camera->getFStop();
	const double focalLength = camera->getFocalLength() * camera->getFocalLengthWorldScale();
	const double focusDistance = camera->getFocusDistance();

	if( projection == "perspective" )
	{
		parameters.add( { "fov", &fov, NSITypeFloat, 0, 1, 0 } );
		if( camera->getFStop() > 0.0f )
		{
			parameters.add( { "depthoffield.enable", &dofEnable, NSITypeInteger, 0, 1, 0 } );
			parameters.add( { "depthoffield.fstop", &fStop, NSITypeDouble, 0, 1, 0 } );
			parameters.add( { "depthoffield.focallength", &focalLength, NSITypeDouble, 0, 1, 0 } );
			parameters.add( { "depthoffield.focaldistance", &focusDistance, NSITypeDouble, 0, 1, 0 } );
		}
	}

	const V2d clippingPlanes = camera->getClippingPlanes();
	parameters.add( { "clippingrange", clippingPlanes.getValue(), NSITypeDouble, 0, 2, 0 } );

	const V2d shutter = camera->getShutter();
	parameters.add( { "shutterrange", shutter.getValue(), NSITypeDouble, 0, 2, 0 } );

	NSISetAttribute( context, handle, parameters.size(), parameters.data() );

	return true;
}

NodeAlgo::ConverterDescription<Camera> g_description( convert );

} // namespace
