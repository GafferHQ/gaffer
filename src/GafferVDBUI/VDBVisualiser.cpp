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

#include <boost/mpl/for_each.hpp>
#include <boost/mpl/list.hpp>

#include "openvdb/openvdb.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"

#include "GafferSceneUI/ObjectVisualiser.h"

#include "GafferVDB/VDBObject.h"

using namespace std;
using namespace Imath;
using namespace GafferSceneUI;
using namespace GafferVDB;

namespace
{

struct GeometryCollector
{
	template<typename GridType>
	void collect( typename GridType::ConstPtr grid )
	{
		using openvdb::Index64;

		for( typename GridType::TreeType::NodeCIter iter = grid->tree().cbeginNode(); iter; ++iter )
		{
			openvdb::CoordBBox bbox;
			iter.getBoundingBox( bbox );

			// Nodes are rendered as cell-centered
			const openvdb::Vec3d min( bbox.min().x() - 0.5, bbox.min().y() - 0.5, bbox.min().z() - 0.5 );
			const openvdb::Vec3d max( bbox.max().x() + 0.5, bbox.max().y() + 0.5, bbox.max().z() + 0.5 );

			addBox( grid.get(), iter.getDepth(), min, max );
		}
	}

	void collect( openvdb::GridBase::ConstPtr grid )
	{
		if( openvdb::BoolGrid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::BoolGrid>( grid ) )
		{
			collect<openvdb::BoolGrid>( t );
		}
		else if( openvdb::DoubleGrid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::DoubleGrid>( grid ) )
		{
			collect<openvdb::DoubleGrid>( t );
		}
		else if( openvdb::FloatGrid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::FloatGrid>( grid ) )
		{
			collect<openvdb::FloatGrid>( t );
		}
		else if( openvdb::Int32Grid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::Int32Grid>( grid ) )
		{
			collect<openvdb::Int32Grid>( t );
		}
		else if( openvdb::Int64Grid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::Int64Grid>( grid ) )
		{
			collect<openvdb::Int64Grid>( t );
		}
		else if( openvdb::MaskGrid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::MaskGrid>( grid ) )
		{
			collect<openvdb::MaskGrid>( t );
		}
		else if( openvdb::StringGrid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::StringGrid>( grid ) )
		{
			collect<openvdb::StringGrid>( t );
		}
		else if( openvdb::Vec3DGrid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::Vec3DGrid>( grid ) )
		{
			collect<openvdb::Vec3DGrid>( t );
		}
		else if( openvdb::Vec3IGrid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::Vec3IGrid>( grid ) )
		{
			collect<openvdb::Vec3IGrid>( t );
		}
		else if( openvdb::Vec3SGrid::ConstPtr t = openvdb::GridBase::constGrid<openvdb::Vec3SGrid>( grid ) )
		{
			collect<openvdb::Vec3SGrid>( t );
		}
	}

	template<typename GridType>
	void addBox(const GridType* grid,  openvdb::Index64 depth, openvdb::Vec3d min, openvdb::Vec3d max)
	{
		if (depth >= positions.size())
		{
			positions.resize(depth + 1);
			vertsPerCurve.resize(depth + 1);

			for (size_t i = 0; i <= depth; ++i)
			{
				if (!positions[i])
				{
					positions[i] = new IECore::V3fVectorData();
					vertsPerCurve[i] = new IECore::IntVectorData();
				}
			}
		}

		std::vector<V3f> &depthPositions = positions[depth]->writable();
		std::vector<int> &depthVertsPerCurve = vertsPerCurve[depth]->writable();

		openvdb::Vec3d ptn;
		std::array<V3f, 8> boundPositions;
		int boundIndex = 0;

		// corner 1
		ptn = grid->indexToWorld(min);
		boundPositions[boundIndex++] = V3f(ptn[0], ptn[1], ptn[2]);

		// corner 2
		ptn = openvdb::Vec3d(min.x(), min.y(), max.z());
		ptn = grid->indexToWorld(ptn);
		boundPositions[boundIndex++] = V3f(ptn[0], ptn[1], ptn[2]);

		// corner 3
		ptn = openvdb::Vec3d(max.x(), min.y(), max.z());
		ptn = grid->indexToWorld(ptn);
		boundPositions[boundIndex++] = V3f(ptn[0], ptn[1], ptn[2]);

		// corner 4
		ptn = openvdb::Vec3d(max.x(), min.y(), min.z());
		ptn = grid->indexToWorld(ptn);
		boundPositions[boundIndex++] = V3f(ptn[0], ptn[1], ptn[2]);

		// corner 5
		ptn = openvdb::Vec3d(min.x(), max.y(), min.z());
		ptn = grid->indexToWorld(ptn);
		boundPositions[boundIndex++] = V3f(ptn[0], ptn[1], ptn[2]);

		// corner 6
		ptn = openvdb::Vec3d(min.x(), max.y(), max.z());
		ptn = grid->indexToWorld(ptn);
		boundPositions[boundIndex++] = V3f(ptn[0], ptn[1], ptn[2]);

		// corner 7
		ptn = grid->indexToWorld(max);
		boundPositions[boundIndex++] = V3f(ptn[0], ptn[1], ptn[2]);

		// corner 8
		ptn = openvdb::Vec3d(max.x(), max.y(), min.z());
		ptn = grid->indexToWorld(ptn);
		boundPositions[boundIndex++] = V3f(ptn[0], ptn[1], ptn[2]);

		//todo remove the need for push_back
		for (size_t i = 0; i < 12; ++i)
		{
			depthVertsPerCurve.push_back(2);
		}

		//todo remove the need for push_back
		depthPositions.push_back(boundPositions[0]);
		depthPositions.push_back(boundPositions[1]);

		depthPositions.push_back(boundPositions[1]);
		depthPositions.push_back(boundPositions[2]);

		depthPositions.push_back(boundPositions[2]);
		depthPositions.push_back(boundPositions[3]);

		depthPositions.push_back(boundPositions[3]);
		depthPositions.push_back(boundPositions[0]);

		//

		depthPositions.push_back(boundPositions[4]);
		depthPositions.push_back(boundPositions[5]);

		depthPositions.push_back(boundPositions[5]);
		depthPositions.push_back(boundPositions[6]);

		depthPositions.push_back(boundPositions[6]);
		depthPositions.push_back(boundPositions[7]);

		depthPositions.push_back(boundPositions[7]);
		depthPositions.push_back(boundPositions[4]);

		//

		depthPositions.push_back(boundPositions[0]);
		depthPositions.push_back(boundPositions[4]);

		depthPositions.push_back(boundPositions[1]);
		depthPositions.push_back(boundPositions[5]);

		depthPositions.push_back(boundPositions[2]);
		depthPositions.push_back(boundPositions[6]);

		depthPositions.push_back(boundPositions[3]);
		depthPositions.push_back(boundPositions[7]);

	}

	std::vector<IECore::V3fVectorDataPtr>  positions;
	std::vector<IECore::IntVectorDataPtr>  vertsPerCurve;
};

class VDBVisualiser : public ObjectVisualiser
{

	public :

		typedef VDBObject ObjectType;

		VDBVisualiser()
			:	m_group( new IECoreGL::Group() )
		{

			m_group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
			m_group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
			m_group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
			m_group->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.06, 0.2, 0.56, 1 ) ) );
			m_group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 2.0f ) );

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
			curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, pData ) );
			m_group->addChild( curves );
		}

		virtual ~VDBVisualiser()
		{
		}

		virtual IECoreGL::ConstRenderablePtr visualise( const IECore::Object *object ) const
		{
			const VDBObject* vdbObject = IECore::runTimeCast<const VDBObject>(object);
			if ( !vdbObject )
			{
				return m_group;
			}

			// todo which grid should be visualised?
			std::vector<std::string> names = vdbObject->gridNames();
			if (names.empty())
			{
				return m_group;
			}

			openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( names[0] );

			IECoreGL::Group *rootGroup = new IECoreGL::Group();

			// todo can these colors go into a config?
			static std::array<Color4f, 4> colors = { { Color4f( 0.56, 0.06, 0.2, 0.2 ), Color4f( 0.06, 0.56, 0.2, 0.2 ), Color4f( 0.06, 0.2, 0.56, 0.2 ), Color4f( 0.6, 0.6, 0.6, 0.2 ) } };

			GeometryCollector collector;
			collector.collect( grid );

			// todo options to define what to visualise (tree, values)
			openvdb::Index64 depth = collector.positions.size() - 1;
			if ( !collector.positions.empty() && !collector.positions[depth]->readable().empty()  )
			{
				IECoreGL::Group *group = new IECoreGL::Group();

				group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
				group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
				group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
				group->getState()->add( new IECoreGL::WireframeColorStateComponent( colors[depth % colors.size()] ) );
				group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 0.5f ) );

				IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, collector.vertsPerCurve[depth] );
				curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, collector.positions[depth] ) );
				group->addChild( curves );

				rootGroup->addChild( group );
			}

			return rootGroup;
		}

	protected :

		static ObjectVisualiserDescription<VDBVisualiser> g_visualiserDescription;

		IECoreGL::GroupPtr m_group;

};

ObjectVisualiser::ObjectVisualiserDescription<VDBVisualiser> VDBVisualiser::g_visualiserDescription;

} // namespace
