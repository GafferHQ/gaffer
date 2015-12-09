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

#include "IECore/ExternalProcedural.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"

#include "GafferSceneUI/Visualiser.h"

using namespace std;
using namespace Imath;
using namespace GafferSceneUI;

namespace
{

class ExternalProceduralVisualiser : public Visualiser
{

	public :

		typedef IECore::ExternalProcedural ObjectType;

		ExternalProceduralVisualiser()
		{
		}

		virtual ~ExternalProceduralVisualiser()
		{
		}

		virtual IECoreGL::ConstRenderablePtr visualise( const IECore::Object *object ) const
		{
			const IECore::ExternalProcedural *externalProcedural = IECore::runTimeCast<const IECore::ExternalProcedural>( object );

			IECoreGL::GroupPtr group = new IECoreGL::Group();
			group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
			group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
			group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );

			IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
			IECore::IntVectorDataPtr vertsPerCurveData = new IECore::IntVectorData;
			vector<V3f> &p = pData->writable();
			vector<int> &vertsPerCurve = vertsPerCurveData->writable();

			// box representing the location of the renderable

			const Box3f b = externalProcedural->bound();

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
			curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, pData ) );
			group->addChild( curves );

			return group;
		}

	protected :

		static VisualiserDescription<ExternalProceduralVisualiser> g_visualiserDescription;

};

Visualiser::VisualiserDescription<ExternalProceduralVisualiser> ExternalProceduralVisualiser::g_visualiserDescription;

} // namespace
