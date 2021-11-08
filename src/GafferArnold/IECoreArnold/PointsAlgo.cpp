//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2016, Image Engine Design Inc. All rights reserved.
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

#include "IECoreScene/PointsPrimitive.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreArnold;

namespace
{

const AtString g_modeArnoldString( "mode" );
const AtString g_motionStartArnoldString( "motion_start" );
const AtString g_motionEndArnoldString( "motion_end" );
const AtString g_pointsArnoldString( "points" );
const AtString g_quadArnoldString( "quad" );
const AtString g_sphereArnoldString( "sphere" );

AtNode *convertCommon( const IECoreScene::PointsPrimitive *points, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode = nullptr )
{

	AtNode *result = AiNode( universe, g_pointsArnoldString, AtString( nodeName.c_str() ), parentNode );

	// mode

	const StringData *t = points->variableData<StringData>( "type", PrimitiveVariable::Constant );
	if( t )
	{
		if( t->readable() == "particle" || t->readable()=="disk" )
		{
			// default type is disk - no need to do anything
		}
		else if( t->readable() == "sphere" )
		{
			AiNodeSetStr( result, g_modeArnoldString, g_sphereArnoldString );
		}
		else if( t->readable() == "patch" )
		{
			AiNodeSetStr( result, g_modeArnoldString, g_quadArnoldString );
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "ToArnoldPointsConverter::doConversion", boost::format( "Unknown type \"%s\" - reverting to disk mode." ) % t->readable() );
		}
	}

	// arbitrary user parameters

	const char *ignore[] = { "P", "width", "radius", nullptr };
	ShapeAlgo::convertPrimitiveVariables( points, result, ignore );

	return result;

}

AtNode *convert( const IECoreScene::PointsPrimitive *points, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *result = convertCommon( points, universe, nodeName, parentNode );

	ShapeAlgo::convertP( points, result, g_pointsArnoldString );
	ShapeAlgo::convertRadius( points, result );

	/// \todo Aspect, rotation

	return result;
}

AtNode *convert( const std::vector<const IECoreScene::PointsPrimitive *> &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *result = convertCommon( samples.front(), universe, nodeName, parentNode );

	std::vector<const IECoreScene::Primitive *> primitiveSamples( samples.begin(), samples.end() );
	ShapeAlgo::convertP( primitiveSamples, result, g_pointsArnoldString );
	ShapeAlgo::convertRadius( primitiveSamples, result );


	AiNodeSetFlt( result, g_motionStartArnoldString, motionStart );
	AiNodeSetFlt( result, g_motionEndArnoldString, motionEnd );

	/// \todo Aspect, rotation

	return result;
}

NodeAlgo::ConverterDescription<PointsPrimitive> g_description( ::convert, ::convert );

} // namespace
