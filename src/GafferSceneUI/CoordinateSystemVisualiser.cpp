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

#include "IECoreScene/CoordinateSystem.h"

using namespace std;
using namespace Imath;
using namespace IECoreGLPreview;

namespace
{

class CoordinateSystemVisualiser : public ObjectVisualiser
{

	public :

		typedef IECoreScene::CoordinateSystem ObjectType;

		CoordinateSystemVisualiser()
		{
			IECoreGL::GroupPtr group = new IECoreGL::Group();
			m_visualisations.push_back( Visualisation::createGeometry( group ) );

			group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
			group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
			group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
			group->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.06, 0.2, 0.56, 1 ) ) );
			group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 2.0f ) );

			IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
			vector<V3f> &p = pData->writable();
			p.reserve( 6 );
			p.push_back( V3f( 0 ) );
			p.push_back( V3f( 1, 0, 0 ) );
			p.push_back( V3f( 0 ) );
			p.push_back( V3f( 0, 1, 0 ) );
			p.push_back( V3f( 0 ) );
			p.push_back( V3f( 0, 0, 1 ) );

			IECore::IntVectorDataPtr vertsPerCurve = new IECore::IntVectorData;
			vertsPerCurve->writable().resize( 3, 2 );

			IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
			curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
			group->addChild( curves );
		}

		~CoordinateSystemVisualiser() override
		{
		}

		Visualisations visualise( const IECore::Object *object ) const override
		{
			return m_visualisations;
		}

	protected :

		static ObjectVisualiserDescription<CoordinateSystemVisualiser> g_visualiserDescription;

		Visualisations m_visualisations;

};

ObjectVisualiser::ObjectVisualiserDescription<CoordinateSystemVisualiser> CoordinateSystemVisualiser::g_visualiserDescription;

} // namespace
