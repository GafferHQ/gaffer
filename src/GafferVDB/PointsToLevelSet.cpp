//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, John Haddon. All rights reserved.
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

#include "GafferVDB/PointsToLevelSet.h"

#include "GafferVDB/Interrupter.h"

#include "IECoreVDB/VDBObject.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "IECoreScene/PointsPrimitive.h"

#include "openvdb/openvdb.h"
#include "openvdb/tools/ParticlesToLevelSet.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreVDB;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferVDB;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

struct ParticleList
{

	using PosType = openvdb::Vec3R;

	ParticleList( const Primitive *points, const std::string &width, float widthScale, const std::string &velocity, float velocityScale )
		:	m_positionView( points->variableIndexedView<V3fVectorData>( "P", PrimitiveVariable::Vertex, /* throwIfInvalid = */ true ).get() ),
			m_widthView( points->variableIndexedView<FloatVectorData>( width, PrimitiveVariable::Vertex ) ),
			m_widthScale( 0.5f * widthScale ), // VDB wants radius, so divide by two
			m_velocityView( points->variableIndexedView<V3fVectorData>( velocity, PrimitiveVariable::Vertex ) ),
			m_velocityScale( velocityScale )
	{
		if( auto d = points->variableData<FloatData>( width, PrimitiveVariable::Constant ) )
		{
			m_widthScale *= d->readable();
		}
	}

	size_t size() const
	{
		return m_positionView.size();
	}

	void getPos( size_t i, PosType &pos ) const
	{
		const V3f &p = m_positionView[i];
		pos[0] = p[0];
		pos[1] = p[1];
		pos[2] = p[2];
	}

	void getPosRad( size_t i, PosType &pos, openvdb::Real &rad ) const
	{
		getPos( i, pos );
		rad = m_widthScale * ( m_widthView ? (*m_widthView)[i] : 1.0f );
	}

	void getPosRadVel( size_t i, PosType &pos, openvdb::Real &rad, PosType &vel ) const
	{
		getPosRad( i, pos, rad );
		const V3f v = m_velocityScale * ( m_velocityView ? (*m_velocityView)[i] : V3f( 0 ) );
		vel[0] = v[0];
		vel[1] = v[1];
		vel[2] = v[2];
	}

	bool hasVelocity() const
	{
		return static_cast<bool>( m_velocityView );
	}

	private :

		PrimitiveVariable::IndexedView<V3f> m_positionView;
		boost::optional<PrimitiveVariable::IndexedView<float>> m_widthView;
		float m_widthScale;
		boost::optional<PrimitiveVariable::IndexedView<V3f>> m_velocityView;
		float m_velocityScale;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// PointsToLevelSet implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( PointsToLevelSet );

size_t PointsToLevelSet::g_firstPlugIndex = 0;

PointsToLevelSet::PointsToLevelSet( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "width", Plug::In, "width" ) );
	addChild( new FloatPlug( "widthScale", Plug::In, 1.0f, 0.0f ) );
	addChild( new BoolPlug( "useVelocity", Plug::In, false ) );
	addChild( new StringPlug( "velocity", Plug::In, "velocity" ) );
	addChild( new FloatPlug( "velocityScale", Plug::In, 1.0f ) );
	addChild( new StringPlug( "grid", Plug::In, "surface") );
	addChild( new FloatPlug( "voxelSize", Plug::In, 0.1f, 0.0001f ) );
	addChild( new FloatPlug( "halfBandwidth", Plug::In, 3.0f, 0.0001f ) );
}

PointsToLevelSet::~PointsToLevelSet()
{
}

Gaffer::StringPlug *PointsToLevelSet::widthPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *PointsToLevelSet::widthPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *PointsToLevelSet::widthScalePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *PointsToLevelSet::widthScalePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *PointsToLevelSet::useVelocityPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *PointsToLevelSet::useVelocityPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *PointsToLevelSet::velocityPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *PointsToLevelSet::velocityPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *PointsToLevelSet::velocityScalePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *PointsToLevelSet::velocityScalePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *PointsToLevelSet::gridPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *PointsToLevelSet::gridPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

FloatPlug *PointsToLevelSet::voxelSizePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 6 );
}

const FloatPlug *PointsToLevelSet::voxelSizePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 6 );
}

Gaffer::FloatPlug *PointsToLevelSet::halfBandwidthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::FloatPlug *PointsToLevelSet::halfBandwidthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

bool PointsToLevelSet::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == widthPlug() ||
		input == widthScalePlug() ||
		input == useVelocityPlug() ||
		input == velocityPlug() ||
		input == velocityScalePlug() ||
		input == gridPlug() ||
		input == voxelSizePlug() ||
		input == halfBandwidthPlug()
	;
}

void PointsToLevelSet::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );

	widthPlug()->hash( h );
	widthScalePlug()->hash( h );
	useVelocityPlug()->hash( h );
	velocityPlug()->hash( h );
	velocityScalePlug()->hash( h );
	h.append( context->getFramesPerSecond() );
	gridPlug()->hash( h );
	voxelSizePlug()->hash( h );
	halfBandwidthPlug()->hash ( h );
}

IECore::ConstObjectPtr PointsToLevelSet::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const Primitive *points = runTimeCast<const Primitive>( inputObject );
	if( !points || points->variables.find( "P" ) == points->variables.end() )
	{
		return inputObject;
	}

	const float voxelSize = voxelSizePlug()->getValue();
	const float halfBandwidth = halfBandwidthPlug()->getValue();

	openvdb::FloatGrid::Ptr grid = openvdb::FloatGrid::create( /* background = */ halfBandwidth * voxelSize );
	grid->setGridClass( openvdb::GRID_LEVEL_SET );
	grid->setTransform( openvdb::math::Transform::createLinearTransform( voxelSize ) );
	grid->setName( gridPlug()->getValue() );

	Interrupter interrupter( context->canceller() );
	openvdb::tools::ParticlesToLevelSet<openvdb::FloatGrid, void, Interrupter> particlesToLevelSet( *grid, &interrupter );

	ParticleList particleList(
		points, widthPlug()->getValue(), widthScalePlug()->getValue(),
		velocityPlug()->getValue(), velocityScalePlug()->getValue() / context->getFramesPerSecond()
	);
	if( particleList.hasVelocity() && useVelocityPlug()->getValue() )
	{
		particlesToLevelSet.rasterizeTrails( particleList );
	}
	else
	{
		particlesToLevelSet.rasterizeSpheres( particleList );
	}
	particlesToLevelSet.finalize();

	// Make sure we don't return a partial result if the interrupter
	// stopped the VDB operation.
	Canceller::check( context->canceller() );

	if( particlesToLevelSet.getMinCount() )
	{
		IECore::msg(
			IECore::Msg::Warning, relativeName( scriptNode() ),
			boost::format( "%1% points from \"%2%\" were ignored because they were too small" )
				% particlesToLevelSet.getMinCount() % ScenePlug::pathToString( path )
		);
	}

	VDBObjectPtr result = new VDBObject();
	result->insertGrid( grid );

	return result;
}

Gaffer::ValuePlug::CachePolicy PointsToLevelSet::processedObjectComputeCachePolicy() const
{
	return ValuePlug::CachePolicy::TaskCollaboration;
}
