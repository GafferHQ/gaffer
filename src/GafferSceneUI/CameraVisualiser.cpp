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


		IECoreGL::CurvesPrimitivePtr frustumVisualisation( const std::string& projection, const Box2f &screenWindow, const V2f &clippingPlanes, bool drawPlanes, bool drawEdges ) const
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

			if( drawPlanes )
			{
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
			}

			if( drawEdges )
			{
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
			}

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

			// box for the camera body

			const Box3f b( V3f( -0.5, -0.5, 0 ), V3f( 0.5, 0.5, 2.0 ) );

			vertsPerCurve.push_back( 5 );
			p.push_back( b.min );
			p.push_back( V3f( b.max.x, b.min.y, b.min.z ) );
			p.push_back( V3f( b.max.x, b.min.y, b.max.z ) );
			p.push_back( V3f( b.min.x, b.min.y, b.max.z ) );
			p.push_back( b.min );

			vertsPerCurve.push_back( 5 );
			p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );
			p.push_back( V3f( b.max.x, b.max.y, b.min.z ) );
			p.push_back( V3f( b.max.x, b.max.y, b.max.z ) );
			p.push_back( V3f( b.min.x, b.max.y, b.max.z ) );
			p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );

			vertsPerCurve.push_back( 2 );
			p.push_back( b.min );
			p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );

			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( b.max.x, b.min.y, b.min.z ) );
			p.push_back( V3f( b.max.x, b.max.y, b.min.z ) );

			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( b.max.x, b.min.y, b.max.z ) );
			p.push_back( V3f( b.max.x, b.max.y, b.max.z ) );

			vertsPerCurve.push_back( 2 );
			p.push_back( V3f( b.min.x, b.min.y, b.max.z ) );
			p.push_back( V3f( b.min.x, b.max.y, b.max.z ) );

			IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurveData );
			curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );

			return curves;
		}

		Visualisations visualise( const IECore::Object *object ) const override
		{
			Visualisations v;

			const IECoreScene::Camera *camera = IECore::runTimeCast<const IECoreScene::Camera>( object );
			if( !camera )
			{
				return v;
			}

			// Use distort mode to get a screen window that matches the whole aperture
			const Box2f &screenWindow = camera->frustum( IECoreScene::Camera::Distort );
			const std::string &projection = camera->getProjection();
			const float ornamentFrustumLength = 5.0f;

			IECoreGL::GroupPtr ornamentGroup = new IECoreGL::Group();
			ornamentGroup->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
			ornamentGroup->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
			ornamentGroup->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
			ornamentGroup->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0, 0.25, 0, 1 ) ) );

			// The ornament uses fixed near/far planes so it's manageable
			ornamentGroup->addChild( frustumVisualisation( projection, screenWindow, V2f( 0, ornamentFrustumLength ), true, true ) );
			ornamentGroup->addChild( bodyVisualisation() );

			IECoreGL::GroupPtr frustumGroup = new IECoreGL::Group();
			frustumGroup->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
			frustumGroup->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
			frustumGroup->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
			frustumGroup->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.4, 0.4, 0.4, 1 ) ) );

			const V2f cameraPlanes = camera->getClippingPlanes();

			// Planes
			frustumGroup->addChild( frustumVisualisation( projection, screenWindow, cameraPlanes, true, false ) );
			// Lines, starting at, at minimum, the edge of the ornament so we don't over-draw the ornament itself, which looks bad.
			const V2f drawingPlanes( std::max( ornamentFrustumLength, cameraPlanes.x ), cameraPlanes.y );
			frustumGroup->addChild( frustumVisualisation( projection, screenWindow, drawingPlanes, false, true ) );

			v[ VisualisationType::Frustum ] = frustumGroup;
			v[ VisualisationType::Ornament ] = ornamentGroup;

			return v;
		}

	protected :

		static ObjectVisualiserDescription<CameraVisualiser> g_visualiserDescription;

};

ObjectVisualiser::ObjectVisualiserDescription<CameraVisualiser> CameraVisualiser::g_visualiserDescription;

} // namespace
