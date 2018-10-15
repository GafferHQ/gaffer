#include "GafferVDBUI/VDBRenderable.h"

#include "openvdb/openvdb.h"
#include "openvdb/points/PointConversion.h"
#include "openvdb/points/PointCount.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/PointsPrimitive.h"
#include "IECoreGL/SpherePrimitive.h"

#include "IECore/SplineData.h"


//#include "IECoreGL/State.h"

using namespace std;
using namespace Imath;
using namespace IECoreScene;
using namespace IECoreVDB;

namespace
{

class GeometryCollector
{

public:
    //! dispatch a base grid to a typed grid
    void collect( openvdb::GridBase::ConstPtr grid )
    {
        static const std::map<std::string, std::function<void(GeometryCollector&, openvdb::GridBase::ConstPtr)> > collectors =
                {
                        { openvdb::typeNameAsString<bool>(), []( GeometryCollector& collector, openvdb::GridBase::ConstPtr grid) { collector.collectTyped<openvdb::BoolGrid>( grid ); } },
                        { openvdb::typeNameAsString<double>(), []( GeometryCollector& collector, openvdb::GridBase::ConstPtr grid ) { collector.collectTyped<openvdb::DoubleGrid>( grid ); } },
                        { openvdb::typeNameAsString<float>(), []( GeometryCollector& collector, openvdb::GridBase::ConstPtr grid ) { collector.collectTyped<openvdb::FloatGrid>( grid ); } },
                        { openvdb::typeNameAsString<int32_t>(), []( GeometryCollector& collector, openvdb::GridBase::ConstPtr grid ) { collector.collectTyped<openvdb::Int32Grid>( grid ); } },
                        { openvdb::typeNameAsString<int64_t>(), []( GeometryCollector& collector , openvdb::GridBase::ConstPtr grid) { collector.collectTyped<openvdb::Int64Grid>( grid ); } },
                        { openvdb::typeNameAsString<openvdb::ValueMask>(), []( GeometryCollector& collector , openvdb::GridBase::ConstPtr grid) { collector.collectTyped<openvdb::MaskGrid>( grid ); } },
                        { openvdb::typeNameAsString<std::string>(), []( GeometryCollector& collector , openvdb::GridBase::ConstPtr grid) { collector.collectTyped<openvdb::StringGrid>( grid ); } },
                        { openvdb::typeNameAsString<openvdb::Vec3d>(), []( GeometryCollector& collector , openvdb::GridBase::ConstPtr grid) { collector.collectTyped<openvdb::Vec3DGrid>( grid ); } },
                        { openvdb::typeNameAsString<openvdb::Vec3i>(), []( GeometryCollector& collector , openvdb::GridBase::ConstPtr grid) { collector.collectTyped<openvdb::Vec3IGrid>( grid ); } },
                        { openvdb::typeNameAsString<openvdb::Vec3f>(), []( GeometryCollector& collector , openvdb::GridBase::ConstPtr grid) { collector.collectTyped<openvdb::Vec3SGrid>( grid ); } },
                        { openvdb::typeNameAsString<openvdb::PointDataIndex32>(), [] ( GeometryCollector& collector , openvdb::GridBase::ConstPtr grid) { collector.collectPoints( grid ); } }
                };

        const auto it = collectors.find( grid->valueType() );
        if( it != collectors.end() )
        {
            it->second( *this, grid );
        }
        else
        {
            throw IECore::InvalidArgumentException( boost::str( boost::format( "VDBVisualiser: Incompatible Grid found name: '%1%' type: '%2' " ) % grid->valueType() % grid->getName() ) );
        }
    }

    void collectVectors(  openvdb::GridBase::ConstPtr grid, const IECore::Splineff& spline )
    {
        static const std::map<std::string, std::function<void(GeometryCollector&, openvdb::GridBase::ConstPtr, const IECore::Splineff& spline)> > collectors =
                {
                        { openvdb::typeNameAsString<openvdb::Vec3d>(), []( GeometryCollector& collector, openvdb::GridBase::ConstPtr grid, const IECore::Splineff& spline ) { collector.collectTypedVector<openvdb::Vec3DGrid>( grid, spline ); } },
                        { openvdb::typeNameAsString<openvdb::Vec3f>(), []( GeometryCollector& collector, openvdb::GridBase::ConstPtr grid, const IECore::Splineff& spline ) { collector.collectTypedVector<openvdb::Vec3SGrid>( grid, spline  ); } },
                };

        const auto it = collectors.find( grid->valueType() );
        if( it != collectors.end() )
        {
            it->second( *this, grid, spline );
        }
        else
        {
            throw IECore::InvalidArgumentException( boost::str( boost::format( "VDBVisualiser: Incompatible Grid found name: '%1%' type: '%2' " ) % grid->valueType() % grid->getName() ) );
        }
    }

    std::vector<IECore::V3fVectorDataPtr>  positions;
    std::vector<IECore::IntVectorDataPtr>  vertsPerCurve;

    std::vector<IECore::V3fVectorDataPtr> points;


private:

    template<typename GridType>
    void collectTyped( openvdb::GridBase::ConstPtr baseGrid )
    {
        using openvdb::Index64;

        typename GridType::ConstPtr grid = openvdb::GridBase::constGrid<GridType>( baseGrid );

        if ( !grid )
        {
            return;
        }

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

    template<typename GridType>
    void collectTypedVector( openvdb::GridBase::ConstPtr baseGrid, const IECore::Splineff& spline )
    {
        typename GridType::ConstPtr grid = openvdb::GridBase::constGrid<GridType>( baseGrid );

        if ( !grid )
        {
            return;
        }

        for (typename GridType::ValueOnCIter iter = grid->cbeginValueOn(); iter.test(); ++iter)
        {
            const typename GridType::TreeType::ValueType& value = *iter;

            openvdb::CoordBBox bbox;
            iter.getBoundingBox(bbox);

            float length = value.length();
            float newLength = spline( value.length() );

            addLine(0, grid->indexToWorld( bbox.getCenter()),  grid->indexToWorld( bbox.getCenter() + value * (newLength / length) ) );

        }

    }

    void collectPoints( openvdb::GridBase::ConstPtr baseGrid )
    {

        openvdb::points::PointDataGrid::ConstPtr pointsGrid = openvdb::GridBase::constGrid<openvdb::points::PointDataGrid>( baseGrid );
        if ( !pointsGrid )
        {
            return;
        }

        openvdb::Index64 count = openvdb::points::pointCount( pointsGrid->tree() );

        IECore::V3fVectorDataPtr pointData = new IECore::V3fVectorData();
        auto &points = pointData->writable();
        points.reserve( count );

        for (auto leafIter = pointsGrid->tree().cbeginLeaf(); leafIter; ++leafIter) {
            const openvdb::points::AttributeArray& array =  leafIter->constAttributeArray("P");
            openvdb::points::AttributeHandle<openvdb::Vec3f> positionHandle( array );

            for (auto indexIter = leafIter->beginIndexOn(); indexIter; ++indexIter)
            {
                openvdb::Vec3f voxelPosition = positionHandle.get( *indexIter );
                const openvdb::Vec3d xyz = indexIter.getCoord().asVec3d();
                openvdb::Vec3f worldPosition =  pointsGrid->transform().indexToWorld( voxelPosition + xyz );
                points.push_back( Imath::Vec3<float>( worldPosition[0], worldPosition[1], worldPosition[2] ) );
            }
        }

        addPoints( pointData );
        collectTyped<openvdb::points::PointDataGrid> ( baseGrid );
    }

    void addPoints(IECore::V3fVectorDataPtr _points)
    {
        points.push_back(_points);
    }

    template<typename GridValueType>
    void addLine(openvdb::Index64 depth, const GridValueType& min, const GridValueType& max)
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

        depthVertsPerCurve.push_back(2);

        depthPositions.push_back( V3f(min[0], min[1], min[2]) );
        depthPositions.push_back( V3f(max[0], max[1], max[2]) );

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
};

}

namespace GafferVDBUI
{

void VDBRenderable::render( IECoreGL::State *currentState ) const
{
    const IECoreVDB::VDBObject* vdbObject = IECore::runTimeCast<const IECoreVDB::VDBObject>( m_vdbObject.get() );

    if ( !vdbObject )
    {
        return;
    }

    // todo which grid should be visualised?
    std::vector<std::string> names = vdbObject->gridNames();
    if ( names.empty() )
    {
        return;
    }

    std::string gridName = names[0];

    IECoreGL::VolumeGridStateComponent *volumeGridStateComponent = currentState->get<IECoreGL::VolumeGridStateComponent>();

    if ( volumeGridStateComponent )
    {
        gridName = volumeGridStateComponent->value();
    }

    openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( gridName );

    if ( !grid )
    {
        return;
    }

    IECoreGL::VolumeScalarRampStateComponent *volumeScalarRampStateComponent = currentState->get<IECoreGL::VolumeScalarRampStateComponent>();

    IECore::Splineff spline;

    IECore::MurmurHash hash;

    if ( volumeScalarRampStateComponent )
    {
        spline = volumeScalarRampStateComponent->value();
    }

    IECore::SplineffDataPtr splineData = new IECore::SplineffData(spline);
    splineData->hash( hash );

    IECoreGL::VolumeTypeStateComponent* volumeTypeStateComponent = currentState->get<IECoreGL::VolumeTypeStateComponent>();
    int renderType = 0;
    if ( volumeTypeStateComponent )
    {
        renderType = volumeTypeStateComponent->value();
    }

    if ( m_group && m_renderType == renderType && m_gridName == gridName && m_hash == hash)
    {
        m_group->render( currentState );
        return;
    }

    m_renderType = renderType;
    m_gridName = gridName;
    m_hash = hash;


    m_group = new IECoreGL::Group();

    if ( m_renderType == 0 )
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
        curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
        m_group->addChild( curves );

        // todo can these colors go into a config?
        static std::array<Color4f, 4> colors = { { Color4f( 0.56, 0.06, 0.2, 0.2 ), Color4f( 0.06, 0.56, 0.2, 0.2 ), Color4f( 0.06, 0.2, 0.56, 0.2 ), Color4f( 0.55, 0.55, 0.55, 0.5 ) } };

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
            curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, collector.positions[depth] ) );
            group->addChild( curves );

            m_group->addChild( group );
        }

        for(auto pointsData : collector.points )
        {
            IECoreGL::Group *pointsGroup = new IECoreGL::Group();

            pointsGroup->getState()->add( new IECoreGL::Primitive::DrawPoints( true ) );
            pointsGroup->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
            pointsGroup->getState()->add( new IECoreGL::PointColorStateComponent( Color4f( 0.8, 0.8, 0.8, 1 ) ) );
            pointsGroup->getState()->add( new IECoreGL::PointsPrimitive::GLPointWidth( 2.0 ) );

            IECoreGL::PointsPrimitivePtr points = new IECoreGL::PointsPrimitive( IECoreGL::PointsPrimitive::Point );
            points->addPrimitiveVariable("P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pointsData ) );
            pointsGroup->addChild( points );

            m_group->addChild( pointsGroup );
        }

    }
    else if ( m_renderType == 1 )
    {
        m_group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
        m_group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
        m_group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
        m_group->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.06, 0.2, 0.56, 1 ) ) );
        m_group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 2.0f ) );

        GeometryCollector collector;
        collector.collectVectors( grid, spline);

        openvdb::Index64 depth = 0;

        if ( !collector.positions.empty() && !collector.positions[depth]->readable().empty()  )
        {
            IECoreGL::Group *group = new IECoreGL::Group();

            group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
            group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
            group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
            group->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 1, 0, 0, 1 ) ) );
            group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 0.5f ) );

            IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, collector.vertsPerCurve[depth] );
            curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, collector.positions[depth] ) );
            group->addChild( curves );

            m_group->addChild( group );
        }
    }
    else
    {
        m_group->addChild( new IECoreGL::SpherePrimitive( 100.0f ) );
    }


    m_group->render( currentState );

}

Imath::Box3f VDBRenderable::bound() const
{
    //todo return the correct bounding box
    return Imath::Box3f();
}

}
