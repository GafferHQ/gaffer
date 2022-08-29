//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Alex Fuller. All rights reserved.
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
//     * Neither the name of Alex Fuller nor the names of any
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

#include "GafferCycles/IECoreCyclesPreview/AttributeAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/GeometryAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECoreScene/SpherePrimitive.h"

#include "IECore/Interpolator.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/geometry.h"
#include "scene/pointcloud.h"
IECORE_POP_DEFAULT_VISIBILITY

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

void warnIfUnsupported( const IECoreScene::SpherePrimitive *sphere )
{
	if( sphere->zMin() != -1.0f )
	{
		msg( Msg::Warning, "IECoreCycles::SphereAlgo::convert", "zMin not supported" );
	}
	if( sphere->zMax() != 1.0f )
	{
		msg( Msg::Warning, "IECoreCycles::SphereAlgo::convert", "zMax not supported" );
	}
	if( sphere->thetaMax() != 360.0f )
	{
		msg( Msg::Warning, "IECoreCycles::SphereAlgo::convert", "thetaMax not supported" );
	}
}

ccl::PointCloud *convertCommon( const IECoreScene::SpherePrimitive *sphere )
{
	assert( sphere->typeId() == IECoreScene::SpherePrimitive::staticTypeId() );
	warnIfUnsupported( sphere );
	ccl::PointCloud *pointcloud = new ccl::PointCloud();

	//pointcloud->set_point_style( ccl::POINT_CLOUD_POINT_SPHERE );
	pointcloud->reserve( 1 );
	pointcloud->add_point( ccl::make_float3( 0.0f, 0.0f, 0.0f ), sphere->radius(), 0);

	PrimitiveVariableMap variablesToConvert = sphere->variables;
	for( PrimitiveVariableMap::iterator it = variablesToConvert.begin(), eIt = variablesToConvert.end(); it != eIt; ++it )
	{
		AttributeAlgo::convertPrimitiveVariable( it->first, it->second, pointcloud->attributes );
	}
	return pointcloud;
}

ccl::Geometry *convert( const IECoreScene::SpherePrimitive *sphere, const std::string &nodeName, ccl::Scene *scene )
{
	ccl::PointCloud *csphere = convertCommon( sphere );
	csphere->name = ccl::ustring( nodeName.c_str() );
	return static_cast<ccl::Geometry *>( csphere );
}

ccl::Geometry *convert( const vector<const IECoreScene::SpherePrimitive *> &samples, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene )
{
	ccl::PointCloud *csphere = convertCommon( samples.front() );
	csphere->name = ccl::ustring( nodeName.c_str() );
	return static_cast<ccl::Geometry *>( csphere );
}

GeometryAlgo::ConverterDescription<SpherePrimitive> g_description( ::convert, ::convert );

} // namespace
