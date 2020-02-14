//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#include "GafferScene/Private/IECoreGLPreview/ObjectVisualiser.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"

#include "IECoreScene/Camera.h"

#include "IECore/AngleConversion.h"
#include "IECore/SimpleTypedData.h"

using namespace std;
using namespace Imath;
using namespace IECoreGLPreview;

namespace
{

class CameraVisualiser : public ObjectVisualiser
{

	public :

		typedef IECoreScene::Camera ObjectType;

		CameraVisualiser()
		{
		}

		~CameraVisualiser() override
		{
		}

		IECoreGL::CurvesPrimitivePtr createFrustum( const std::string& projection, const Box2f &screenWindow, const V2f &clippingPlanes, float offset = 0.0f ) const
		{

			IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
			IECore::IntVectorDataPtr vertsPerCurveData = new IECore::IntVectorData;
			vector<V3f> &p = pData->writable();
			vector<int> &vertsPerCurve = vertsPerCurveData->writable();

			Box2f near( screenWindow );
			Box2f far( screenWindow );

			if( projection == "perspective" )
			{
				near.min *= clippingPlanes[0];
				near.max *= clippingPlanes[0];
				far.min *= clippingPlanes[1];
				far.max *= clippingPlanes[1];
			}

			const V2f o( offset );
			near.min -= o;
			near.max += o;
			far.min -= o;
			far.max += o;

			vertsPerCurve.push_back( 5 );
			p.push_back( V3f( near.min.x, near.min.y, -clippingPlanes[0] ) );
			p.push_back( V3f( near.max.x, near.min.y, -clippingPlanes[0] ) );
			p.push_back( V3f( near.max.x, near.max.y, -clippingPlanes[0] ) );
			p.push_back( V3f( near.min.x, near.max.y, -clippingPlanes[0] ) );
			p.push_back( V3f( near.min.x, near.min.y, -clippingPlanes[0] ) );

			vertsPerCurve.push_back( 5 );
			p.push_back( V3f( far.min.x, far.min.y, -clippingPlanes[1] ) );
			p.push_back( V3f( far.max.x, far.min.y, -clippingPlanes[1] ) );
			p.push_back( V3f( far.max.x, far.max.y, -clippingPlanes[1] ) );
			p.push_back( V3f( far.min.x, far.max.y, -clippingPlanes[1] ) );
			p.push_back( V3f( far.min.x, far.min.y, -clippingPlanes[1] ) );

			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( near.min.x, near.min.y, -clippingPlanes[0] ) );
			p.push_back( V3f( far.min.x, far.min.y, -clippingPlanes[1] ) );

			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( near.max.x, near.min.y, -clippingPlanes[0] ) );
			p.push_back( V3f( far.max.x, far.min.y, -clippingPlanes[1] ) );

			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( near.max.x, near.max.y, -clippingPlanes[0] ) );
			p.push_back( V3f( far.max.x, far.max.y, -clippingPlanes[1] ) );

			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( near.min.x, near.max.y, -clippingPlanes[0] ) );
			p.push_back( V3f( far.min.x, far.max.y, -clippingPlanes[1] ) );

			IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurveData );
			curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );

			return curves;
		}

		IECoreGL::CurvesPrimitivePtr bodyVisualisation() const
		{
			IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
			IECore::IntVectorDataPtr vertsPerCurveData = new IECore::IntVectorData;
			vector<V3f> &p = pData->writable();
			vector<int> &vertsPerCurve = vertsPerCurveData->writable();

			// A box for the camera body, with a handle to show which way is up.
			// Based on the more recent Arri cameras.
			//       ______
			//      |      |      Handle
			//     ------------
			// <=  |     ___  |
			//     |____/   \-|   Rest
			//

			static const Box3f b( V3f( -0.4f, -0.4f, 0 ), V3f( 0.4f, 0.4f, 1.8f ) );
			static const V3f size = b.size();
			static const float restHeight = size.y * 0.2f;
			static const float backMinY = b.min.y + ( restHeight * 0.5f );

			//
			// Front
			//

			vertsPerCurve.push_back( 5 );
			p.push_back( b.min );
			p.push_back( V3f( b.max.x, b.min.y, b.min.z ) );
			p.push_back( V3f( b.max.x, b.max.y, b.min.z ) );
			p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );
			p.push_back( b.min );

			//
			// Back
			//

			vertsPerCurve.push_back( 5 );
			p.push_back( b.max );
			p.push_back( V3f( b.max.x, backMinY, b.max.z ) );
			p.push_back( V3f( b.min.x, backMinY, b.max.z ) );
			p.push_back( V3f( b.min.x, b.max.y, b.max.z ) );
			p.push_back( b.max );

			//
			// Bottom edges (with shoulder rest curve)
			//

			static const float restXs[2] = { b.min.x, b.max.x };
			static const float restZs[6] = { b.min.z, size.z * 0.3f, size.z * 0.4f, size.z * 0.8f, size.z * 0.9f, b.max.z };
			static const float restYs[6] = { b.min.y, b.min.y, b.min.y + restHeight, b.min.y + restHeight, backMinY, backMinY };

			// front to back
			for( const float x : restXs )
			{
				vertsPerCurve.push_back( 6 );
				p.push_back( V3f( x, restYs[0], restZs[0] ) );
				p.push_back( V3f( x, restYs[1], restZs[1] ) );
				p.push_back( V3f( x, restYs[2], restZs[2] ) );
				p.push_back( V3f( x, restYs[3], restZs[3] ) );
				p.push_back( V3f( x, restYs[4], restZs[4] ) );
				p.push_back( V3f( x, restYs[5], restZs[5] ) );
			}
			// left to right edges
			for( size_t i = 0; i < 6; ++i )
			{
				vertsPerCurve.push_back( 2 );
				p.push_back( V3f( restXs[0], restYs[i], restZs[i] ) );
				p.push_back( V3f( restXs[1], restYs[i], restZs[i] ) );
			}

			//
			// Top edges
			//

			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );
			p.push_back( V3f( b.min.x, b.max.y, b.max.z ) );

			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( b.max.x, b.max.y, b.min.z ) );
			p.push_back( V3f( b.max.x, b.max.y, b.max.z ) );

			//
			// Handle
			//

			static const float handleThickness = size.y * 0.3f;
			static const float handleXs[2] = { b.min.x * 0.1f, b.max.x * 0.1f };
			static const float handleYs[3] = { b.max.y, b.max.y + handleThickness, b.max.y + handleThickness + ( handleXs[1] - handleXs[0] ) };
			static const float handleZs[4] = { b.min.z + 0.1f, b.min.z + 0.15f, b.max.z - 0.45f, b.max.z - 0.4f };

			// Outer handle
			for( const float x : handleXs )
			{
				vertsPerCurve.push_back( 4 );
				p.push_back( V3f( x, handleYs[0], handleZs[0] ) );
				p.push_back( V3f( x, handleYs[2], handleZs[0] ) );
				p.push_back( V3f( x, handleYs[2], handleZs[3] ) );
				p.push_back( V3f( x, handleYs[0], handleZs[3] ) );
			}
			// Inner handle
			for( const float x : handleXs )
			{
				vertsPerCurve.push_back( 4 );
				p.push_back( V3f( x, handleYs[0], handleZs[1] ) );
				p.push_back( V3f( x, handleYs[1], handleZs[1] ) );
				p.push_back( V3f( x, handleYs[1], handleZs[2] ) );
				p.push_back( V3f( x, handleYs[0], handleZs[2] ) );
			}
			// left - to - right lines
			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( handleXs[0], handleYs[2], handleZs[0] ) );
			p.push_back( V3f( handleXs[1], handleYs[2], handleZs[0] ) );
			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( handleXs[0], handleYs[1], handleZs[1] ) );
			p.push_back( V3f( handleXs[1], handleYs[1], handleZs[1] ) );
			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( handleXs[0], handleYs[1], handleZs[2] ) );
			p.push_back( V3f( handleXs[1], handleYs[1], handleZs[2] ) );
			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( handleXs[0], handleYs[2], handleZs[3] ) );
			p.push_back( V3f( handleXs[1], handleYs[2], handleZs[3] ) );

			IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurveData );
			curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );

			return curves;
		}

		Visualisations visualise( const IECore::Object *object ) const override
		{
			const IECoreScene::Camera *camera = IECore::runTimeCast<const IECoreScene::Camera>( object );
			if( !camera )
			{
				return {};
			}

			// Use distort mode to get a screen window that matches the whole aperture
			const Box2f &screenWindow = camera->frustum( IECoreScene::Camera::Distort );
			const std::string &projection = camera->getProjection();

			// Scalable 'camera body' visualisation

			IECoreGL::GroupPtr ornamentGroup = new IECoreGL::Group();
			ornamentGroup->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
			ornamentGroup->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
			ornamentGroup->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
			ornamentGroup->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0, 0.25, 0, 1 ) ) );

			// The ornament uses fixed near/far planes so it's manageable
			ornamentGroup->addChild( createFrustum( projection, screenWindow, V2f( 0.0f, 0.75f ), 0.1f ) );
			ornamentGroup->addChild( bodyVisualisation() );

			// Real-world frustum

			IECoreGL::GroupPtr frustumGroup = new IECoreGL::Group();
			frustumGroup->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
			frustumGroup->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
			frustumGroup->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
			frustumGroup->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.4, 0.4, 0.4, 1 ) ) );

			frustumGroup->addChild( createFrustum( projection, screenWindow, camera->getClippingPlanes() ) );

			// We need to make sure the frustum preview of the ornament scales
			// with any non-uniform scaling of the location.
			Visualisation boxVis = Visualisation::createOrnament( ornamentGroup, true );
			boxVis.scale = Visualisation::Scale::LocalAndVisualiser;

			Visualisation frustumVis = Visualisation::createFrustum( frustumGroup, Visualisation::Scale::Local );

			return { boxVis, frustumVis };
		}

	protected :

		static ObjectVisualiserDescription<CameraVisualiser> g_visualiserDescription;

};

ObjectVisualiser::ObjectVisualiserDescription<CameraVisualiser> CameraVisualiser::g_visualiserDescription;

} // namespace
