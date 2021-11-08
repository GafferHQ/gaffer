//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferArnold/Private/IECoreArnold/NodeAlgo.h"
#include "GafferArnold/Private/IECoreArnold/ShapeAlgo.h"

#include "IECoreScene/SpherePrimitive.h"

#include "IECore/MessageHandler.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreArnold;

namespace
{

const AtString g_sphereArnoldString("sphere");
const AtString g_radiusArnoldString("radius");
const AtString g_motionStartArnoldString("motion_start");
const AtString g_motionEndArnoldString("motion_end");

void warnIfUnsupported( const IECoreScene::SpherePrimitive *sphere )
{
	if( sphere->zMin() != -1.0f )
	{
		msg( Msg::Warning, "IECoreArnold::SphereAlgo::convert", "zMin not supported" );
	}
	if( sphere->zMax() != 1.0f )
	{
		msg( Msg::Warning, "IECoreArnold::SphereAlgo::convert", "zMax not supported" );
	}
	if( sphere->thetaMax() != 360.0f )
	{
		msg( Msg::Warning, "IECoreArnold::SphereAlgo::convert", "thetaMax not supported" );
	}
}

AtNode *convert( const IECoreScene::SpherePrimitive *sphere, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode )
{
	warnIfUnsupported( sphere );

	AtNode *result = AiNode( universe, g_sphereArnoldString, AtString( nodeName.c_str() ), parentNode );
	ShapeAlgo::convertPrimitiveVariables( sphere, result );

	AiNodeSetFlt( result, g_radiusArnoldString, sphere->radius() );

	return result;
}

AtNode *convert( const std::vector<const IECoreScene::SpherePrimitive *> &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *result = AiNode( universe, g_sphereArnoldString, AtString( nodeName.c_str() ), parentNode );
	ShapeAlgo::convertPrimitiveVariables( samples.front(), result );

	AtArray *radiusSamples = AiArrayAllocate( 1, samples.size(), AI_TYPE_FLOAT );

	for( vector<const IECoreScene::SpherePrimitive *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
	{
		warnIfUnsupported( *it );
		float radius = (*it)->radius();
		AiArraySetKey( radiusSamples, /* key = */ it - samples.begin(), &radius );
	}

	AiNodeSetArray( result, g_radiusArnoldString, radiusSamples );
	AiNodeSetFlt( result, g_motionStartArnoldString, motionStart );
	AiNodeSetFlt( result, g_motionEndArnoldString, motionEnd );

	return result;
}

NodeAlgo::ConverterDescription<SpherePrimitive> g_description( convert, convert );

} // namespace
