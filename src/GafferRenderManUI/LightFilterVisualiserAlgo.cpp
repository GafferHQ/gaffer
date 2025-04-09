//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
//     * Neither the name of Cinesite VFX Ltd. nor the names of any
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

#include "LightFilterVisualiserAlgo.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"

#include "IECoreScene/PrimitiveVariable.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"

#include <array>

using namespace Imath;
using namespace IECore;

namespace
{

void addRect(
	const V2f &innerSize,
	const V2f &innerScale,
	const V4f &innerOffset,  // Convenient way to pass top, left, bottom, right, in that order
	const float radius,
	const float falloffWidth,
	const V4f &falloffScale,  // Same order as above
	std::vector<int> &vertsPerCurve,
	std::vector<V3f> &p
)
{
	const V3f halfSize( innerSize.x * 0.5f, innerSize.y * 0.5f, 0.f );
	const V3f scale( innerScale.x, innerScale.y, 0.f );

	if( radius == 0 && falloffWidth == 0.f )
	{
		const V3f halfSizeScaled = halfSize * scale;
		vertsPerCurve.push_back( 4 );
		p.push_back( V3f( -halfSizeScaled.x - innerOffset[1] * innerScale.x, -halfSizeScaled.y - innerOffset[2] * innerScale.y, 0.f ) );
		p.push_back( V3f( halfSizeScaled.x + innerOffset[3] * innerScale.x, -halfSizeScaled.y - innerOffset[2] * innerScale.y, 0.f ) );
		p.push_back( V3f( halfSizeScaled.x + innerOffset[3] * innerScale.x, halfSizeScaled.y + innerOffset[0] * innerScale.y, 0.f ) );
		p.push_back( V3f( -halfSizeScaled.x - innerOffset[1] * innerScale.x, halfSizeScaled.y + innerOffset[0] * innerScale.y, 0.f ) );

		return;
	}

	const int numDivisions = 100;
	vertsPerCurve.push_back( numDivisions + 4 );

	for(
		const auto &[startIndex, quadrantMult, quadrantOffset, falloffMult] : std::array<std::tuple<int, V3f, V3f, V3f>, 4> {
			std::tuple<int, V3f, V3f, V3f>{
				0,
				V3f( 1.f, 1.f, 0.f ),
				V3f( innerOffset[3], innerOffset[0], 0.f ),
				V3f( falloffScale[3], falloffScale[0], 0.f )
			},  // Top-right
			std::tuple<int, V3f, V3f, V3f>{
				numDivisions / 4,
				V3f( -1.f, 1.f, 0.f ),
				V3f( -innerOffset[1], innerOffset[0], 0.f ),
				V3f( falloffScale[1], falloffScale[0], 0.f )
			},  // Top-left
			std::tuple<int, V3f, V3f, V3f>{
				numDivisions / 2,
				V3f( -1.f, -1.f, 0.f ),
				V3f( -innerOffset[1], -innerOffset[2], 0.f ),
				V3f( falloffScale[1], falloffScale[2], 0.f )
			},  // Bottom-left
			std::tuple<int, V3f, V3f, V3f>{
				( numDivisions * 3 ) / 4,
				V3f( 1.f, -1.f, 0.f ),
				V3f( innerOffset[3], -innerOffset[2], 0.f ),
				V3f( falloffScale[3], falloffScale[2], 0.f )
			}  // Bottom-right
		}
	)
	{
		for( int i = startIndex, eI = startIndex + ( numDivisions / 4 ); i <= eI; ++i )
		{
			const float angle = 2.f * M_PI * (float)i / (float)numDivisions;
			const V3f delta( cos( angle ), sin( angle ), 0.f );
			p.push_back( ( delta * radius + ( halfSize * quadrantMult ) + quadrantOffset ) * scale + ( delta * falloffWidth * falloffMult ) );
		}
	}
}

}  // namespace

IECoreGL::GroupPtr GafferRenderManUI::lightFilterRectangles( const V2f &innerSize, const float radius, const V2f &innerScale, const V4f &innerOffset, const V4f &falloffScale, const float edge )
{
	IntVectorDataPtr innerVertsPerCurveData = new IntVectorData();
	V3fVectorDataPtr innerPData = new V3fVectorData();

	std::vector<int> &innerVertsPerCurve = innerVertsPerCurveData->writable();
	std::vector<V3f> &innerP = innerPData->writable();

	addRect( innerSize, innerScale, innerOffset, radius, 0.f, V4f( 0.f ), innerVertsPerCurve, innerP );

	IECoreGL::CurvesPrimitivePtr rect = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic */ true, innerVertsPerCurveData );
	rect->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, innerPData ) );
	rect->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 255.f / 255.f, 171.f / 255.f, 15.f / 255.f ) ) ) );

	IECoreGL::GroupPtr group = new IECoreGL::Group();
	group->addChild( rect );

	if( edge > 0 )
	{
		IECoreGL::GroupPtr edgeGroup = new IECoreGL::Group();
		edgeGroup->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 1.0f ) );

		IntVectorDataPtr edgeVertsPerCurveData = new IntVectorData();
		V3fVectorDataPtr edgePData = new V3fVectorData();

		std::vector<int> &edgeVertsPerCurve = edgeVertsPerCurveData->writable();
		std::vector<V3f> &edgeP = edgePData->writable();

		addRect( innerSize, innerScale, innerOffset, radius, edge, falloffScale, edgeVertsPerCurve, edgeP );

		IECoreGL::CurvesPrimitivePtr edgeRect = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic */ true, edgeVertsPerCurveData );
		edgeRect->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, edgePData ) );
		edgeRect->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 0.f ) ) ) );

		edgeGroup->addChild( edgeRect );
		group->addChild( edgeGroup );
	}

	return group;
}
